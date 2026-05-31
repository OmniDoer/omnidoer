import json
import os
import stat
import tempfile
import unittest
from http.server import ThreadingHTTPServer
from pathlib import Path
from threading import Thread
from urllib import request as urllib_request

from omnidoer.omni_control.chat import MAX_CHAT_RECORDS, ChatStore
from omnidoer.omni_control.server import ControlHandler


class ControlChatStoreTest(unittest.TestCase):
    def test_chat_lifecycle_and_streaming_delta(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            store = ChatStore(Path(tmp) / "chat.json")
            user = store.append(role="user", text="Hello from the client")
            self.assertEqual(stat.S_IMODE(store.path.stat().st_mode), 0o600)
            self.assertEqual(user.status, "queued")
            claimed = store.next_user_message()
            self.assertIsNotNone(claimed)
            assert claimed is not None
            self.assertEqual(claimed.message_id, user.message_id)
            self.assertEqual(claimed.status, "claimed")
            assistant = store.append(role="assistant", text="", status="streaming", reply_to_message_id=user.message_id)
            updated = store.append_delta(assistant.message_id, "Hi")
            self.assertEqual(updated.text, "Hi")
            completed = store.complete(assistant.message_id, text="Hi there")
            self.assertEqual(completed.status, "completed")
            self.assertEqual(completed.text, "Hi there")
            records = store.list_records()
            self.assertGreaterEqual(len(records), 5)
            self.assertEqual(records[-2].record_type, "delta")
            self.assertEqual(records[-2].text, "Hi")
            public = completed.to_public_dict()
            self.assertFalse(public["secret_fields_allowed"])
            self.assertFalse(public["control_client_calls_model"])

    def test_chat_records_are_pruned_to_about_five_screens(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            store = ChatStore(Path(tmp) / "chat.json")
            for index in range(MAX_CHAT_RECORDS + 40):
                store.append_record(record_type="note", text=f"record {index}", role="system")
            records = store.list_records(limit=1000)
            self.assertLessEqual(len(records), MAX_CHAT_RECORDS)
            self.assertEqual(records[0].text, "record 40")
            self.assertEqual(records[-1].text, f"record {MAX_CHAT_RECORDS + 39}")


class ControlChatApiTest(unittest.TestCase):
    def test_control_server_chat_api_and_sse_stream(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            old_home = os.environ.get("OMNIDOER_HOME")
            os.environ["OMNIDOER_HOME"] = tmp
            server = ThreadingHTTPServer(("127.0.0.1", 0), ControlHandler)
            thread = Thread(target=server.serve_forever, daemon=True)
            thread.start()
            base = f"http://127.0.0.1:{server.server_address[1]}"
            try:
                create = urllib_request.Request(
                    f"{base}/api/chat/messages",
                    data=json.dumps({"text": "Queue a chat message"}).encode(),
                    headers={"content-type": "application/json"},
                    method="POST",
                )
                with urllib_request.urlopen(create, timeout=5) as response:
                    self.assertEqual(response.status, 201)
                    message = json.loads(response.read().decode())
                self.assertEqual(message["role"], "user")
                self.assertEqual(message["status"], "queued")

                next_req = urllib_request.Request(
                    f"{base}/api/chat/messages/next",
                    data=json.dumps({"claim": True}).encode(),
                    headers={"content-type": "application/json"},
                    method="POST",
                )
                with urllib_request.urlopen(next_req, timeout=5) as response:
                    claimed = json.loads(response.read().decode())
                self.assertEqual(claimed["status"], "ok")
                self.assertEqual(claimed["message"]["status"], "claimed")

                assistant_req = urllib_request.Request(
                    f"{base}/api/chat/messages/assistant",
                    data=json.dumps({"text": "", "status": "streaming", "reply_to_message_id": message["message_id"]}).encode(),
                    headers={"content-type": "application/json"},
                    method="POST",
                )
                with urllib_request.urlopen(assistant_req, timeout=5) as response:
                    assistant = json.loads(response.read().decode())
                delta_req = urllib_request.Request(
                    f"{base}/api/chat/messages/{assistant['message_id']}/delta",
                    data=json.dumps({"delta": "streamed"}).encode(),
                    headers={"content-type": "application/json"},
                    method="POST",
                )
                with urllib_request.urlopen(delta_req, timeout=5) as response:
                    updated = json.loads(response.read().decode())
                self.assertEqual(updated["text"], "streamed")

                with urllib_request.urlopen(f"{base}/api/chat/messages", timeout=5) as response:
                    payload = json.loads(response.read().decode())
                self.assertEqual(len(payload["messages"]), 2)
                self.assertGreaterEqual(len(payload["records"]), 4)
                self.assertEqual(payload["records"][-1]["record_type"], "delta")
                self.assertFalse(payload["control_client_calls_model"])
                self.assertEqual(payload["retention"]["approx_screen_count"], 5)

                with urllib_request.urlopen(f"{base}/api/chat/events?stream=1&snapshots=1&interval=0", timeout=5) as response:
                    stream = response.read().decode()
                self.assertIn("event: chat", stream)
                self.assertIn("streamed", stream)
            finally:
                server.shutdown()
                server.server_close()
                if old_home is None:
                    os.environ.pop("OMNIDOER_HOME", None)
                else:
                    os.environ["OMNIDOER_HOME"] = old_home


if __name__ == "__main__":
    unittest.main()
