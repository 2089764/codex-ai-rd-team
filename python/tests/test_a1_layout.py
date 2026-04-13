import json
import os
import subprocess
import unittest
from pathlib import Path


class A1LayoutTests(unittest.TestCase):
    def test_required_files_exist(self):
        required = [
            "rd-team/SKILL.md",
            "rd-team/commands/rd-team.md",
            "rd-team/agents/analyst.md",
            "rd-team/agents/architect.md",
            "rd-team/agents/backend-dev.md",
            "rd-team/agents/frontend-dev.md",
            "rd-team/agents/code-reviewer.md",
            "rd-team/agents/tester.md",
            "rd-team/shared-rd-resources/tech-profiles/tech-profiles.json",
            "scripts/sync_tech_profiles.py",
        ]

        for rel_path in required:
            self.assertTrue(Path(rel_path).exists(), rel_path)

    def test_cli_entrypoint_ai_rd_exists_and_is_executable(self):
        ai_rd = Path("bin/ai-rd")
        self.assertTrue(ai_rd.exists(), ai_rd.as_posix())
        self.assertTrue(os.access(ai_rd, os.X_OK), ai_rd.as_posix())

    def test_command_document_mentions_orchestrator_transpile_command(self):
        command_doc = Path("rd-team/commands/rd-team.md").read_text(encoding="utf-8")

        self.assertIn("python -m orchestrator.cli orchestrate --objective", command_doc)

    def test_synced_tech_profiles_matches_config(self):
        config_path = Path("config/tech-profiles.json")
        synced_path = Path("rd-team/shared-rd-resources/tech-profiles/tech-profiles.json")

        self.assertTrue(config_path.exists(), config_path.as_posix())
        self.assertTrue(synced_path.exists(), synced_path.as_posix())

        config_data = json.loads(config_path.read_text(encoding="utf-8"))
        synced_data = json.loads(synced_path.read_text(encoding="utf-8"))

        self.assertEqual(synced_data, config_data)

    def test_sync_script_restores_target_file_from_config(self):
        config_path = Path("config/tech-profiles.json")
        synced_path = Path("rd-team/shared-rd-resources/tech-profiles/tech-profiles.json")
        script_path = Path("scripts/sync_tech_profiles.py")

        original_synced = synced_path.read_text(encoding="utf-8")
        wrong_content = '{"broken": true}\n'

        try:
            synced_path.write_text(wrong_content, encoding="utf-8")

            result = subprocess.run(
                ["python3", str(script_path)],
                check=True,
                capture_output=True,
                text=True,
            )

            self.assertEqual(result.stdout, "")
            self.assertEqual(result.stderr, "")
            self.assertEqual(synced_path.read_text(encoding="utf-8"), config_path.read_text(encoding="utf-8"))
        finally:
            synced_path.write_text(original_synced, encoding="utf-8")


if __name__ == "__main__":
    unittest.main()
