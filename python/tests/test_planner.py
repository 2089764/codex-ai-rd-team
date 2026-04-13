import unittest

from orchestrator.planner import build_work_queue
from orchestrator.profiles import TechProfile
from orchestrator.runtime_models import Role


class PlannerTests(unittest.TestCase):
    def test_build_work_queue_respects_role_order_and_focus(self):
        profile = TechProfile(
            name="generic",
            data={
                "has_frontend": False,
                "role_focus": {
                    "analyst": ["a1"],
                    "architect": ["arc1"],
                    "backend-dev": ["be1", "be2"],
                    "frontend-dev": ["fe1"],
                    "tester": ["t1"],
                    "code-reviewer": ["cr1"],
                },
            },
        )

        queue = build_work_queue(profile=profile, objective="build demo")

        self.assertEqual([item.role for item in queue], [
            Role.ANALYST,
            Role.ARCHITECT,
            Role.BACKEND_DEV,
            Role.BACKEND_DEV,
            Role.TESTER,
            Role.CODE_REVIEWER,
        ])
        self.assertIn("build demo", queue[0].instructions)
        self.assertIn("a1", queue[0].instructions)

    def test_build_work_queue_supports_structured_role_focus(self):
        profile = TechProfile(
            name="generic",
            data={
                "has_frontend": False,
                "role_focus": {
                    "analyst": {
                        "priorities": ["a-priority"],
                        "must_check": ["a-must"],
                        "avoid": ["a-avoid"],
                    },
                    "architect": {"priorities": ["arc-priority"]},
                    "backend-dev": {"must_check": ["be-must"]},
                    "frontend-dev": {"priorities": ["fe-priority"]},
                    "tester": {"priorities": ["t-priority"]},
                    "code-reviewer": {"priorities": ["cr-priority"]},
                },
            },
        )

        queue = build_work_queue(profile=profile, objective="build demo")

        self.assertEqual([item.role for item in queue], [
            Role.ANALYST,
            Role.ARCHITECT,
            Role.BACKEND_DEV,
            Role.TESTER,
            Role.CODE_REVIEWER,
        ])
        self.assertIn("a-priority", queue[0].instructions)
        self.assertIn("be-must", queue[2].instructions)


if __name__ == "__main__":
    unittest.main()
