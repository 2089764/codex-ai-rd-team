import unittest
from unittest.mock import patch

from orchestrator.agent_clients import CodexAgentClient, EchoAgentClient
from orchestrator.cli import _create_agent_client


class CliAgentClientSelectionTests(unittest.TestCase):
    def test_explicit_echo_client(self):
        client = _create_agent_client(
            agent_client="echo",
            codex_bin="codex",
            codex_model=None,
            workdir=".",
        )
        self.assertIsInstance(client, EchoAgentClient)

    def test_explicit_codex_client(self):
        with patch("orchestrator.cli._resolve_executable", return_value="/usr/local/bin/codex"):
            client = _create_agent_client(
                agent_client="codex",
                codex_bin="codex",
                codex_model="gpt-5.4",
                workdir=".",
            )
        self.assertIsInstance(client, CodexAgentClient)
        self.assertEqual(client.model, "gpt-5.4")
        self.assertEqual(client.binary, "/usr/local/bin/codex")

    def test_explicit_codex_client_raises_when_binary_missing(self):
        with patch("orchestrator.cli._resolve_executable", return_value=None):
            with self.assertRaises(RuntimeError):
                _create_agent_client(
                    agent_client="codex",
                    codex_bin="codex",
                    codex_model="gpt-5.4",
                    workdir=".",
                )

    def test_auto_falls_back_to_echo_without_codex(self):
        with patch("orchestrator.cli.shutil.which", return_value=None):
            client = _create_agent_client(
                agent_client="auto",
                codex_bin="codex",
                codex_model=None,
                workdir=".",
            )
        self.assertIsInstance(client, EchoAgentClient)

    def test_auto_prefers_codex_when_available(self):
        with patch("orchestrator.cli.shutil.which", return_value="/usr/local/bin/codex"):
            client = _create_agent_client(
                agent_client="auto",
                codex_bin="codex",
                codex_model=None,
                workdir=".",
            )
        self.assertIsInstance(client, CodexAgentClient)


if __name__ == "__main__":
    unittest.main()
