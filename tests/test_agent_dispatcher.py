import unittest

from orchestrator.agent_dispatcher import AgentDispatchError, AgentDispatcher
from orchestrator.runtime_models import Role, RuntimeState, WorkItem, WorkStatus


class FakeAgentClient:
    def __init__(self, response: str = "ok", raise_error: bool = False):
        self.response = response
        self.raise_error = raise_error
        self.calls = []

    def run(self, *, role: str, prompt: str, context: dict):
        self.calls.append({"role": role, "prompt": prompt, "context": context})
        if self.raise_error:
            raise RuntimeError("boom")
        return self.response


class AgentDispatcherTests(unittest.TestCase):
    def test_dispatch_calls_client_and_updates_attempts(self):
        client = FakeAgentClient(response="analysis done")
        dispatcher = AgentDispatcher(client)
        state = RuntimeState(run_id="run-1", profile_name="generic", objective="demo")
        item = WorkItem(item_id="w1", role=Role.ANALYST, title="分析", instructions="拆解需求")

        result = dispatcher.dispatch(item, state)

        self.assertEqual(result, "analysis done")
        self.assertEqual(item.attempts, 1)
        self.assertEqual(len(client.calls), 1)
        self.assertEqual(client.calls[0]["role"], Role.ANALYST.value)

    def test_dispatch_wraps_client_error(self):
        client = FakeAgentClient(raise_error=True)
        dispatcher = AgentDispatcher(client)
        state = RuntimeState(run_id="run-2", profile_name="generic", objective="demo")
        item = WorkItem(
            item_id="w1",
            role=Role.TESTER,
            title="测试",
            instructions="写测试",
            status=WorkStatus.IN_PROGRESS,
        )

        with self.assertRaises(AgentDispatchError):
            dispatcher.dispatch(item, state)


if __name__ == "__main__":
    unittest.main()
