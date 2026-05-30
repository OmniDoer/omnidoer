import os
import tempfile
import unittest

from omnidoer.omni_takeover.input_events import parse_actions
from omnidoer.omni_takeover.relay import request_registration_handoff, start_stream
from omnidoer.omni_takeover.stream import current_frame


class TakeoverStreamTest(unittest.TestCase):
    def test_frame_is_control_only(self) -> None:
        frame = current_frame()
        self.assertTrue(frame["for_control_client_only"])
        self.assertTrue(frame["not_for_llm"])

    def test_parse_actions(self) -> None:
        events = parse_actions("tap:1,2;click:3,4;double_click:5,6;long_press:7,8;drag:1,2->3,4;scroll:30;type:secret;key:Enter;release")
        self.assertEqual(
            [event.event_type for event in events],
            ["tap", "click", "double_click", "long_press", "drag", "scroll", "type", "key", "release"],
        )

    def test_registration_handoff_stream_is_control_only(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            old_home = os.environ.get("OMNIDOER_HOME")
            os.environ["OMNIDOER_HOME"] = tmp
            try:
                request = request_registration_handoff(
                    origin="https://example.com",
                    top_level_url="https://example.com/register",
                    reason="site requires user registration",
                )
                frame = start_stream(request.request_id)
                self.assertEqual(request.request_type, "account_registration")
                self.assertTrue(frame["for_control_client_only"])
                self.assertTrue(frame["not_for_llm"])
            finally:
                if old_home is None:
                    os.environ.pop("OMNIDOER_HOME", None)
                else:
                    os.environ["OMNIDOER_HOME"] = old_home


if __name__ == "__main__":
    unittest.main()
