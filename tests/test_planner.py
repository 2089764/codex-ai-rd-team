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


if __name__ == "__main__":
    unittest.main()
