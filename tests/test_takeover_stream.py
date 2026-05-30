import unittest

from omnidoer.omni_takeover.input_events import parse_actions
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


if __name__ == "__main__":
    unittest.main()
