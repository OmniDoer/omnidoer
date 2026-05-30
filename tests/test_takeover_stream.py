import unittest

from omnidoer.omni_takeover.input_events import parse_actions
from omnidoer.omni_takeover.stream import current_frame


class TakeoverStreamTest(unittest.TestCase):
    def test_frame_is_control_only(self) -> None:
        frame = current_frame()
        self.assertTrue(frame["for_control_client_only"])
        self.assertTrue(frame["not_for_llm"])

    def test_parse_actions(self) -> None:
        events = parse_actions("tap:1,2;scroll:30;type:secret;release")
        self.assertEqual([event.event_type for event in events], ["tap", "scroll", "type", "release"])


if __name__ == "__main__":
    unittest.main()
