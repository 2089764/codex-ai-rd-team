import tempfile
import unittest
from pathlib import Path

from orchestrator.prompts import (
    PromptConfigError,
    load_role_prompts,
    render_coordinator_prompt,
    render_role_prompt,
)
from orchestrator.runtime_models import Role


class PromptsTests(unittest.TestCase):
    def test_load_role_prompts_reads_json_mapping(self):
        tempdir = tempfile.TemporaryDirectory()
        self.addCleanup(tempdir.cleanup)
        path = Path(tempdir.name) / "role-prompts.json"
        path.write_text('{"analyst":"A", "coordinator":"C"}', encoding="utf-8")

        prompts = load_role_prompts(path)

        self.assertEqual(prompts["analyst"], "A")
        self.assertEqual(prompts["coordinator"], "C")

    def test_render_role_prompt_includes_context(self):
        prompts = {
            "analyst": "你是分析师，关注需求边界。",
            "coordinator": "你是协调者。",
        }

        text = render_role_prompt(
            role=Role.ANALYST,
            objective="构建订单系统",
            instructions="拆解里程碑",
            profile_name="go-kratos-api",
            prompts=prompts,
        )

        self.assertIn("你是分析师", text)
        self.assertIn("构建订单系统", text)
        self.assertIn("拆解里程碑", text)
        self.assertIn("go-kratos-api", text)

    def test_render_role_prompt_includes_structured_role_focus(self):
        prompts = {
            "code-reviewer": "你是审查者。",
            "coordinator": "你是协调者。",
        }
        text = render_role_prompt(
            role=Role.CODE_REVIEWER,
            objective="构建订单系统",
            instructions="审查 backend 变更",
            profile_name="go-kratos-api",
            prompts=prompts,
            role_focus={
                "priorities": ["correctness", "security"],
                "must_check": ["api-contract"],
                "avoid": ["直接改代码"],
            },
        )

        self.assertIn("RoleFocus.Priorities", text)
        self.assertIn("correctness", text)
        self.assertIn("RoleFocus.MustCheck", text)
        self.assertIn("api-contract", text)
        self.assertIn("RoleFocus.Avoid", text)
        self.assertIn("直接改代码", text)

    def test_render_role_prompt_raises_when_template_missing(self):
        with self.assertRaises(PromptConfigError):
            render_role_prompt(
                role=Role.TESTER,
                objective="obj",
                instructions="ins",
                profile_name="generic",
                prompts={"coordinator": "x"},
            )

    def test_render_coordinator_prompt_uses_template(self):
        prompts = {"coordinator": "你是协调者，负责推进。"}
        text = render_coordinator_prompt(objective="build", profile_name="generic", prompts=prompts)

        self.assertIn("你是协调者", text)
        self.assertIn("build", text)
        self.assertIn("generic", text)


if __name__ == "__main__":
    unittest.main()
