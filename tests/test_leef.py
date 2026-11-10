import json
import os
import shutil
import tempfile
import unittest

import leef


class DummyParent:
    def __init__(self):
        self.messages = []

    def send_message(self, message):
        self.messages.append(message)

    def is_moderator(self, user):
        return user == "mod"

    def has_permission(self, user, permission):
        return user == "mod" and permission == "Moderator"


class TestChatData:
    def __init__(self, user_name, params):
        self.UserName = user_name
        self._params = params

    def IsChatMessage(self):
        return True

    def GetParam(self, index):
        if index < len(self._params):
            return self._params[index]
        return None


class LeefCompatibilityTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp(prefix="leef-test-", dir=os.getcwd())
        leef.scriptPath = self.temp_dir
        leef.settings = leef.Settings()
        leef.plantData = {
            "total_water": 0,
            "level": 0,
            "last_task": "",
            "last_user": "",
            "last_action": "",
            "last_amount": 0,
        }

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_execute_accepts_parent_bridge(self):
        parent = DummyParent()
        data = TestChatData("alice", ["!leef"])

        leef.Execute(data, parent=parent)

        self.assertEqual(1, len(parent.messages))
        self.assertIn("alice", parent.messages[0])

    def test_completing_final_level_assigns_task_and_resets_to_level_zero(self):
        final_task = "Finale Aufgabe"
        leef.settings.TaskList = [final_task]
        final_level_threshold = sum(
            leef.GetWaterNeededForLevel(level)
            for level in range(len(leef.settings.LevelNames) - 1)
        )

        response = leef.WaterPlant("alice", final_level_threshold)

        self.assertIn(final_task, response)
        self.assertIn("Level 0 'Samen'", response)
        self.assertEqual(0, leef.plantData["total_water"])
        self.assertEqual(0, leef.plantData["level"])
        self.assertEqual(final_task, leef.plantData["last_task"])
        self.assertEqual("reset", leef.plantData["last_action"])

        with open(os.path.join(self.temp_dir, leef.OverlayStateFile), encoding="utf-8") as state_file:
            overlay_state = json.load(state_file)
        self.assertEqual(0, overlay_state["level"])
        self.assertEqual(final_task, overlay_state["lastTask"])


if __name__ == "__main__":
    unittest.main()
