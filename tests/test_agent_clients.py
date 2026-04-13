import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from orchestrator.agent_clients import CodexAgentClient, EchoAgentClient


class AgentClientsTests(unittest.TestCase):
    def test_echo_agent_client_returns_tail(self):
        client = EchoAgentClient()
        result = client.run(
            role="analyst",
            prompt="line1\nline2",
            context={"run_id": "run-1"},
        )
        self.assertEqual(result, "DONE: [analyst] line2")

    def test_codex_agent_client_reads_last_message_file(self):
        with tempfile.TemporaryDirectory() as tempdir:
            workdir = Path(tempdir)
            client = CodexAgentClient(binary="codex", model="gpt-5.4", workdir=workdir, timeout_sec=30.0)

            def fake_run(cmd, *, input, text, capture_output, check, timeout):
                self.assertIn("codex", cmd[0])
                self.assertIn("exec", cmd)
                self.assertIn("--output-last-message", cmd)
                self.assertIn("--model", cmd)
                self.assertEqual(text, True)
                self.assertEqual(capture_output, True)
                self.assertEqual(check, False)
                self.assertEqual(timeout, 30.0)
                self.assertIn("BUG:", input)
                out_idx = cmd.index("--output-last-message") + 1
                Path(cmd[out_idx]).write_text("PASS: all good", encoding="utf-8")
                return subprocess.CompletedProcess(args=cmd, returncode=0, stdout="", stderr="")

            with patch("orchestrator.agent_clients.subprocess.run", side_effect=fake_run):
                result = client.run(role="tester", prompt="请测试", context={"run_id": "run-1"})

            self.assertEqual(result, "PASS: all good")

    def test_codex_agent_client_raises_when_exec_fails(self):
        client = CodexAgentClient(binary="codex")
        with patch(
            "orchestrator.agent_clients.subprocess.run",
            return_value=subprocess.CompletedProcess(args=["codex"], returncode=2, stdout="", stderr="boom"),
        ):
            with self.assertRaises(RuntimeError):
                client.run(role="backend-dev", prompt="do work", context={})

    def test_codex_agent_client_raises_when_timeout(self):
        client = CodexAgentClient(binary="codex", timeout_sec=1.0)
        with patch(
            "orchestrator.agent_clients.subprocess.run",
            side_effect=subprocess.TimeoutExpired(cmd=["codex"], timeout=1.0),
        ):
            with self.assertRaises(RuntimeError):
                client.run(role="backend-dev", prompt="do work", context={})


if __name__ == "__main__":
    unittest.main()
