import unittest

from orchestrator.mode_classifier import classify_mode


class ModeClassifierTests(unittest.TestCase):
    def test_bugfix_wins_over_feature(self):
        text = "这是一个功能需求，但先修复这个 bug 后再说"

        self.assertEqual(classify_mode(text), "bugfix")

    def test_bugfix_wins_over_refactor(self):
        text = "这次需要重构代码结构，但这里有个 bug 先修复"

        self.assertEqual(classify_mode(text), "bugfix")

    def test_refactor_wins_over_feature(self):
        text = "这是一次功能扩展，不过需要先重构一下代码结构"

        self.assertEqual(classify_mode(text), "refactor")

    def test_feature_is_detected(self):
        text = "请增加一个新功能，用于导出报告"

        self.assertEqual(classify_mode(text), "feature")

    def test_default_is_new_project(self):
        text = "这是一段和现有任务无关的描述"

        self.assertEqual(classify_mode(text), "new_project")

    def test_english_uppercase_bug_is_detected(self):
        text = "Please fix the BUG in login flow"

        self.assertEqual(classify_mode(text), "bugfix")

    def test_english_bug_wins_over_feature(self):
        text = "please add a feature, then fix this bug"

        self.assertEqual(classify_mode(text), "bugfix")

    def test_english_bug_wins_over_refactor(self):
        text = "please refactor this module, but first fix this bug"

        self.assertEqual(classify_mode(text), "bugfix")

    def test_empty_string_defaults_to_new_project(self):
        self.assertEqual(classify_mode(""), "new_project")

    def test_noise_text_defaults_to_new_project(self):
        text = "12345 !!! --- ###"

        self.assertEqual(classify_mode(text), "new_project")

    def test_traditional_chinese_keywords_are_detected(self):
        self.assertEqual(classify_mode("需要重構這段流程"), "refactor")
        self.assertEqual(classify_mode("系統一直在報錯"), "bugfix")

    def test_debug_is_not_treated_as_bugfix(self):
        text = "need to debug the parser"

        self.assertEqual(classify_mode(text), "new_project")


if __name__ == "__main__":
    unittest.main()
