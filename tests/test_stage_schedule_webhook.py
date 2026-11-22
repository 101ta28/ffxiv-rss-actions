import json
import os
import unittest
from datetime import datetime, timedelta
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

import stage_schedule_webhook as stage


class StageScheduleTests(unittest.TestCase):
    def test_weekly_table_covers_every_slot_after_delayed_updates(self):
        zero = datetime.fromisoformat("2026-05-03T00:30:00+09:00")
        anchor = datetime.fromisoformat("2026-11-22T17:30:00+09:00")
        slots = {}
        for line in stage.build_weekly_table(zero).splitlines()[2:-1]:
            cells = [int(value) for value in line.split()]
            hours, weekdays = cells[:-7], cells[-7:]
            for hour in hours:
                for day, number in enumerate(weekdays):
                    slots[day, hour] = number

        self.assertEqual(len(slots), 168)
        for hours_later in range(2 * 168):
            start = anchor + timedelta(hours=hours_later)
            expected = (stage.STAGES.index("クラウドナイン") + hours_later) % 7 + 1
            self.assertEqual(slots[start.weekday(), start.hour], expected, start)

    def test_existing_message_gets_dated_schedule_before_next_rotation(self):
        now = datetime.fromisoformat("2026-11-22T17:53:19+09:00")
        boundary = datetime.fromisoformat("2026-11-22T18:00:00+09:00")
        env = {stage.WEBHOOK_URL_ENV: "https://example.invalid", stage.STAGE_ZERO_TIME_ENV: ""}
        with TemporaryDirectory() as tmp:
            state = Path(tmp) / "stage_schedule_state.json"
            state.write_text(json.dumps({
                "message_id": "123",
                "last_rotation_key": "2026-11-22T18:00:00+0900",
                "payload_version": 2,
            }))
            with (
                patch.object(stage, "STATE_FILE", state),
                patch.dict(os.environ, env),
                patch.object(stage, "datetime", wraps=datetime) as clock,
                patch.object(stage.requests, "patch") as edit,
                patch.object(stage.requests, "post") as create,
            ):
                clock.now.return_value = now
                stage.main()
                stage.main()
                create.assert_not_called()
                edit.assert_called_once()
                self.assertEqual(edit.call_args.args[0], "https://example.invalid/messages/123")
                fields = edit.call_args.kwargs["json"]["embeds"][0]["fields"]
                lines = fields[0]["value"].splitlines()
                expected_stages = stage.STAGES[3:] + stage.STAGES[:3]
                for offset, name in enumerate(expected_stages):
                    start = boundary + timedelta(hours=offset - 1)
                    number = stage.STAGES.index(name) + 1
                    expected_line = f"<t:{int(start.timestamp())}:f>　`{number}` {name}"
                    self.assertEqual(lines[offset], expected_line)
                self.assertEqual(len(lines), 7)
                self.assertIn("日本時間・毎時00分", fields[1]["name"])
                self.assertEqual(json.loads(state.read_text())["message_id"], "123")

                clock.now.return_value = now + timedelta(days=1)
                stage.main()
                self.assertEqual(edit.call_count, 2)
                create.assert_not_called()
                new_fields = edit.call_args.kwargs["json"]["embeds"][0]["fields"]
                self.assertNotEqual(fields[0], new_fields[0])
                self.assertEqual(fields[1], new_fields[1])


if __name__ == "__main__":
    unittest.main()
