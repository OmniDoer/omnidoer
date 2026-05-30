import os
import tempfile
import unittest

from omnidoer.omni_takeover.input_events import event_from_dict, parse_actions
from omnidoer.omni_takeover.relay import request_registration_handoff, start_stream
from omnidoer.omni_takeover.stream import frame_profile_settings, current_frame, normalize_frame_profile


class ProfileAwareBrowser:
    def __init__(self):
        self.frame_profile = None

    def takeover_frame(self, *, frame_profile: str | None = None) -> dict:
        self.frame_profile = frame_profile
        return {
            "content_type": "image/jpeg",
            "data_b64": "frame",
            "transport": {"profile": frame_profile, "content_type": "image/jpeg", "quality": 48},
            "for_control_client_only": True,
            "not_for_llm": True,
        }


class TakeoverStreamTest(unittest.TestCase):
    def test_frame_is_control_only(self) -> None:
        frame = current_frame()
        self.assertTrue(frame["for_control_client_only"])
        self.assertTrue(frame["not_for_llm"])
        self.assertIn("frame_id", frame)
        self.assertIn("captured_at", frame)
        self.assertEqual(frame["coordinate_space"], "viewport_pixels")
        self.assertTrue(frame["input_binding_required"])
        self.assertEqual(frame["transport"]["profile"], "lossless")
        self.assertEqual(frame["transport"]["content_type"], "image/png")

    def test_frame_profiles_are_normalized(self) -> None:
        self.assertEqual(normalize_frame_profile("data-saver"), "data_saver")
        self.assertEqual(frame_profile_settings("balanced")["content_type"], "image/jpeg")
        self.assertEqual(frame_profile_settings("data_saver")["quality"], 48)
        with self.assertRaises(ValueError) as raised:
            normalize_frame_profile("raw-secret-profile")
        self.assertEqual(str(raised.exception), "unsupported takeover frame profile")

    def test_start_stream_passes_requested_profile_to_browser(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            old_home = os.environ.get("OMNIDOER_HOME")
            os.environ["OMNIDOER_HOME"] = tmp
            try:
                request = request_registration_handoff(
                    origin="https://example.com",
                    top_level_url="https://example.com/register",
                    reason="site requires user registration",
                )
                browser = ProfileAwareBrowser()
                frame = start_stream(request.request_id, browser_controller=browser, frame_profile="data_saver")
                self.assertEqual(browser.frame_profile, "data_saver")
                self.assertEqual(frame["transport"]["profile"], "data_saver")
            finally:
                if old_home is None:
                    os.environ.pop("OMNIDOER_HOME", None)
                else:
                    os.environ["OMNIDOER_HOME"] = old_home

    def test_parse_actions(self) -> None:
        events = parse_actions("tap:1,2;click:3,4;double_click:5,6;long_press:7,8;drag:1,2->3,4;scroll:30;type:secret;key:Enter;release")
        self.assertEqual(
            [event.event_type for event in events],
            ["tap", "click", "double_click", "long_press", "drag", "scroll", "type", "key", "release"],
        )

    def test_event_from_dict_rejects_untrusted_event_type_without_echo(self) -> None:
        with self.assertRaises(ValueError) as raised:
            event_from_dict({"event_type": "password=should-not-log", "text": "also-secret"})
        self.assertEqual(str(raised.exception), "unsupported takeover event")

    def test_event_from_dict_rejects_oversized_text_without_echo(self) -> None:
        with self.assertRaises(ValueError) as raised:
            event_from_dict({"event_type": "type", "text": "x" * 4097})
        self.assertEqual(str(raised.exception), "takeover text too long")

    def test_event_from_dict_rejects_oversized_frame_id_without_echo(self) -> None:
        with self.assertRaises(ValueError) as raised:
            event_from_dict({"event_type": "tap", "frame_id": "x" * 129, "x": 1, "y": 2})
        self.assertEqual(str(raised.exception), "takeover frame id too long")

    def test_event_from_dict_rejects_non_integer_coordinates_without_echo(self) -> None:
        with self.assertRaises(ValueError) as raised:
            event_from_dict({"event_type": "tap", "frame_id": "frame", "x": "secret-x", "y": 2})
        self.assertEqual(str(raised.exception), "takeover coordinates must be integers")

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
