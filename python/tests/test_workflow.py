import unittest

from orchestrator.workflow import build_execution_stages, build_role_flow


class WorkflowTests(unittest.TestCase):
    def test_new_project_with_frontend(self):
        self.assertEqual(
            build_role_flow(mode="new_project", has_frontend=True),
            [
                "analyst",
                "architect",
                "backend-dev",
                "frontend-dev",
                "code-reviewer",
                "tester",
            ],
        )

    def test_new_project_without_frontend(self):
        self.assertEqual(
            build_role_flow(mode="new_project", has_frontend=False),
            [
                "analyst",
                "architect",
                "backend-dev",
                "code-reviewer",
                "tester",
            ],
        )

    def test_feature_with_frontend(self):
        self.assertEqual(
            build_role_flow(mode="feature", has_frontend=True),
            [
                "analyst",
                "architect",
                "backend-dev",
                "frontend-dev",
                "code-reviewer",
                "tester",
            ],
        )

    def test_feature_without_frontend(self):
        self.assertEqual(
            build_role_flow(mode="feature", has_frontend=False),
            [
                "analyst",
                "architect",
                "backend-dev",
                "code-reviewer",
                "tester",
            ],
        )

    def test_bugfix_uses_backend_only_flow(self):
        self.assertEqual(
            build_role_flow(mode="bugfix", has_frontend=True),
            ["backend-dev", "code-reviewer", "tester"],
        )
        self.assertEqual(
            build_role_flow(mode="bugfix", has_frontend=False),
            ["backend-dev", "code-reviewer", "tester"],
        )

    def test_refactor_with_frontend(self):
        self.assertEqual(
            build_role_flow(mode="refactor", has_frontend=True),
            [
                "architect",
                "backend-dev",
                "frontend-dev",
                "code-reviewer",
                "tester",
            ],
        )

    def test_refactor_without_frontend(self):
        self.assertEqual(
            build_role_flow(mode="refactor", has_frontend=False),
            [
                "architect",
                "backend-dev",
                "code-reviewer",
                "tester",
            ],
        )

    def test_unknown_mode_defaults_to_new_project(self):
        self.assertEqual(
            build_role_flow(mode="unknown-mode", has_frontend=False),
            [
                "analyst",
                "architect",
                "backend-dev",
                "code-reviewer",
                "tester",
            ],
        )

    def test_build_execution_stages_marks_parallel_backend_frontend(self):
        stages = build_execution_stages(mode="new_project", has_frontend=True)
        self.assertEqual(stages[0]["roles"], ["analyst"])
        self.assertEqual(stages[1]["roles"], ["architect"])
        self.assertEqual(stages[2]["roles"], ["backend-dev", "frontend-dev"])
        self.assertTrue(stages[2]["parallel"])

    def test_build_execution_stages_bugfix_has_no_parallel(self):
        stages = build_execution_stages(mode="bugfix", has_frontend=True)
        self.assertEqual(
            [stage["roles"] for stage in stages],
            [["backend-dev"], ["code-reviewer"], ["tester"]],
        )
        self.assertTrue(all(stage["parallel"] is False for stage in stages))


if __name__ == "__main__":
    unittest.main()
