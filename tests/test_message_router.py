import unittest

from orchestrator.message_router import route_next_role
from orchestrator.runtime_models import Role


class MessageRouterTests(unittest.TestCase):
    def test_routes_backend_to_tester_when_no_frontend(self):
        next_role = route_next_role(Role.BACKEND_DEV, has_frontend=False)
        self.assertEqual(next_role, Role.TESTER)

    def test_routes_backend_to_frontend_when_frontend_exists(self):
        next_role = route_next_role(Role.BACKEND_DEV, has_frontend=True)
        self.assertEqual(next_role, Role.FRONTEND_DEV)

    def test_routes_final_reviewer_to_none(self):
        next_role = route_next_role(Role.CODE_REVIEWER, has_frontend=True)
        self.assertIsNone(next_role)


if __name__ == "__main__":
    unittest.main()
