import json
import tempfile
import unittest
from pathlib import Path
from copy import deepcopy

from orchestrator.profiles import (
    ProfileConfigError,
    load_tech_profiles,
    resolve_tech_profile,
)


def write_profiles(payload):
    tempdir = tempfile.TemporaryDirectory()
    path = Path(tempdir.name) / "tech-profiles.json"
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    return tempdir, path


class TechProfileTests(unittest.TestCase):
    def setUp(self):
        payload = {
            "generic": {
                "description": "base profile",
                "has_frontend": False,
                "keywords": ["base"],
                "resolved_stack": {
                    "language": "go",
                    "framework": "kratos",
                    "delivery": "cli",
                    "ui": "none",
                },
                "role_focus": {
                    "analyst": ["requirement-tracing", "gap-analysis"],
                    "architect": ["boundary-design"],
                    "backend-dev": ["orchestration", "profiles"],
                    "frontend-dev": [],
                    "code-reviewer": ["correctness"],
                    "tester": ["coverage"],
                },
            },
            "go-kratos-web": {
                "extends": "generic",
                "description": "web profile",
                "has_frontend": True,
                "keywords": ["kratos web", "go-kratos-web"],
                "resolved_stack": {
                    "language": "go",
                    "framework": "kratos",
                    "delivery": "http",
                    "ui": "vue",
                    "runtime": {
                        "backend": "kratos",
                        "frontend": "vue",
                    },
                },
                "role_focus": {
                    "frontend-dev": ["routing", "presentation"],
                    "tester": ["ui-smoke"],
                },
            },
            "go-kratos-api": {
                "extends": "generic",
                "description": "api profile",
                "has_frontend": False,
                "keywords": ["kratos api", "go-kratos-api"],
                "resolved_stack": {
                    "language": "go",
                    "framework": "kratos",
                    "delivery": "grpc",
                    "ui": "none",
                    "runtime": {
                        "backend": "kratos",
                        "frontend": None,
                    },
                },
                "role_focus": {
                    "backend-dev": ["rpc", "contracts"],
                    "tester": ["api-smoke"],
                },
            },
        }
        self._tempdir, self.path = write_profiles(payload)
        self.catalog = load_tech_profiles(self.path)

    def tearDown(self):
        self._tempdir.cleanup()

    def test_explicit_selection_wins_over_keyword_match(self):
        resolved = resolve_tech_profile(
            self.catalog,
            explicit="go-kratos-api",
            text="this looks like a kratos web service",
        )

        self.assertEqual(resolved.name, "go-kratos-api")
        self.assertEqual(resolved.data["description"], "api profile")
        self.assertFalse(resolved.data["has_frontend"])
        self.assertEqual(resolved.data["resolved_stack"]["delivery"], "grpc")
        self.assertEqual(resolved.data["resolved_stack"]["framework"], "kratos")

    def test_keyword_matching_selects_matching_profile(self):
        resolved = resolve_tech_profile(
            self.catalog,
            text="we are building a go kratos web application",
        )

        self.assertEqual(resolved.name, "go-kratos-web")
        self.assertEqual(resolved.data["description"], "web profile")
        self.assertTrue(resolved.data["has_frontend"])
        self.assertEqual(resolved.data["resolved_stack"]["ui"], "vue")

    def test_extends_merges_parent_profile(self):
        resolved = resolve_tech_profile(self.catalog, explicit="go-kratos-web")

        self.assertEqual(resolved.data["description"], "web profile")
        self.assertTrue(resolved.data["has_frontend"])
        self.assertEqual(resolved.data["resolved_stack"]["language"], "go")
        self.assertEqual(resolved.data["resolved_stack"]["framework"], "kratos")
        self.assertEqual(resolved.data["resolved_stack"]["delivery"], "http")
        self.assertEqual(resolved.data["resolved_stack"]["ui"], "vue")
        self.assertEqual(resolved.data["resolved_stack"]["runtime"]["backend"], "kratos")
        self.assertEqual(resolved.data["resolved_stack"]["runtime"]["frontend"], "vue")
        self.assertEqual(
            resolved.data["role_focus"]["backend-dev"],
            ["orchestration", "profiles"],
        )
        self.assertEqual(
            resolved.data["role_focus"]["frontend-dev"],
            ["routing", "presentation"],
        )
        self.assertEqual(
            resolved.data["role_focus"]["tester"],
            ["coverage", "ui-smoke"],
        )

    def test_fallback_resolves_generic(self):
        resolved = resolve_tech_profile(self.catalog, text="some unrelated project")

        self.assertEqual(resolved.name, "generic")
        self.assertEqual(resolved.data["description"], "base profile")
        self.assertFalse(resolved.data["has_frontend"])
        self.assertEqual(resolved.data["resolved_stack"]["language"], "go")
        self.assertEqual(resolved.data["resolved_stack"]["framework"], "kratos")
        self.assertEqual(resolved.data["resolved_stack"]["delivery"], "cli")
        self.assertEqual(resolved.data["role_focus"]["backend-dev"], ["orchestration", "profiles"])

    def test_has_frontend_inherits_and_overrides(self):
        web_profile = resolve_tech_profile(self.catalog, explicit="go-kratos-web")
        generic_profile = resolve_tech_profile(self.catalog, explicit="generic")

        self.assertFalse(generic_profile.data["has_frontend"])
        self.assertTrue(web_profile.data["has_frontend"])

    def test_role_focus_is_read_and_validated(self):
        resolved = resolve_tech_profile(self.catalog, explicit="go-kratos-api")

        self.assertEqual(resolved.data["role_focus"]["backend-dev"], ["orchestration", "profiles", "rpc", "contracts"])
        self.assertEqual(resolved.data["role_focus"]["tester"], ["coverage", "api-smoke"])

    def test_invalid_profile_catalog_is_rejected(self):
        tempdir, path = write_profiles(
            {
                "generic": {
                    "has_frontend": "nope",
                    "keywords": ["base"],
                    "resolved_stack": [],
                    "role_focus": {
                        "primary": "not-a-list",
                    },
                }
            }
        )
        self.addCleanup(tempdir.cleanup)

        with self.assertRaises(ProfileConfigError):
            load_tech_profiles(path)

    def test_invalid_role_focus_key_is_rejected(self):
        tempdir, path = write_profiles(
            {
                "generic": {
                    "has_frontend": False,
                    "keywords": ["base"],
                    "resolved_stack": {},
                    "role_focus": {
                        "primary": ["not-allowed"],
                    },
                }
            }
        )
        self.addCleanup(tempdir.cleanup)

        with self.assertRaises(ProfileConfigError):
            load_tech_profiles(path)

    def test_unknown_extends_parent_is_rejected(self):
        tempdir, path = write_profiles(
            {
                "generic": {
                    "has_frontend": False,
                    "keywords": [],
                    "resolved_stack": {
                        "language": "go",
                        "framework": "kratos",
                        "delivery": "cli",
                        "ui": "none",
                    },
                    "role_focus": {
                        "analyst": [],
                        "architect": [],
                        "backend-dev": [],
                        "frontend-dev": [],
                        "code-reviewer": [],
                        "tester": [],
                    },
                },
                "broken": {
                    "extends": "missing-parent",
                    "keywords": ["broken"],
                },
            }
        )
        self.addCleanup(tempdir.cleanup)

        with self.assertRaises(ProfileConfigError):
            load_tech_profiles(path)

    def test_extends_cycle_is_rejected(self):
        tempdir, path = write_profiles(
            {
                "generic": {
                    "has_frontend": False,
                    "keywords": [],
                    "resolved_stack": {
                        "language": "go",
                        "framework": "kratos",
                        "delivery": "cli",
                        "ui": "none",
                    },
                    "role_focus": {
                        "analyst": [],
                        "architect": [],
                        "backend-dev": [],
                        "frontend-dev": [],
                        "code-reviewer": [],
                        "tester": [],
                    },
                },
                "a": {
                    "extends": "b",
                    "keywords": ["a"],
                },
                "b": {
                    "extends": "a",
                    "keywords": ["b"],
                },
            }
        )
        self.addCleanup(tempdir.cleanup)

        with self.assertRaises(ProfileConfigError):
            load_tech_profiles(path)

    def test_resolved_stack_field_types_are_validated(self):
        tempdir, path = write_profiles(
            {
                "generic": {
                    "has_frontend": False,
                    "keywords": [],
                    "resolved_stack": {
                        "language": "go",
                        "framework": 123,
                        "delivery": "cli",
                        "ui": "none",
                    },
                    "role_focus": {
                        "analyst": [],
                        "architect": [],
                        "backend-dev": [],
                        "frontend-dev": [],
                        "code-reviewer": [],
                        "tester": [],
                    },
                }
            }
        )
        self.addCleanup(tempdir.cleanup)

        with self.assertRaises(ProfileConfigError):
            load_tech_profiles(path)

    def test_resolved_stack_runtime_must_be_object(self):
        tempdir, path = write_profiles(
            {
                "generic": {
                    "has_frontend": False,
                    "keywords": [],
                    "resolved_stack": {
                        "language": "go",
                        "framework": "kratos",
                        "delivery": "cli",
                        "ui": "none",
                        "runtime": [],
                    },
                    "role_focus": {
                        "analyst": [],
                        "architect": [],
                        "backend-dev": [],
                        "frontend-dev": [],
                        "code-reviewer": [],
                        "tester": [],
                    },
                }
            }
        )
        self.addCleanup(tempdir.cleanup)

        with self.assertRaises(ProfileConfigError):
            load_tech_profiles(path)

    def test_keyword_matching_is_deterministic_when_multiple_profiles_match(self):
        tempdir, path = write_profiles(
            {
                "generic": {
                    "has_frontend": False,
                    "keywords": [],
                    "resolved_stack": {
                        "language": "go",
                        "framework": "kratos",
                        "delivery": "cli",
                        "ui": "none",
                    },
                    "role_focus": {
                        "analyst": [],
                        "architect": [],
                        "backend-dev": [],
                        "frontend-dev": [],
                        "code-reviewer": [],
                        "tester": [],
                    },
                },
                "go-kratos-api": {
                    "extends": "generic",
                    "keywords": ["kratos api"],
                },
                "go-kratos-web": {
                    "extends": "generic",
                    "keywords": ["kratos web"],
                },
            }
        )
        self.addCleanup(tempdir.cleanup)
        catalog = load_tech_profiles(path)

        resolved = resolve_tech_profile(catalog, text="kratos api and kratos web")

        self.assertEqual(resolved.name, "go-kratos-api")

    def test_keyword_merge_deduplicates_parent_entries(self):
        tempdir, path = write_profiles(
            {
                "generic": {
                    "has_frontend": False,
                    "keywords": ["shared", "base"],
                    "resolved_stack": {
                        "language": "go",
                        "framework": "kratos",
                        "delivery": "cli",
                        "ui": "none",
                    },
                    "role_focus": {
                        "analyst": [],
                        "architect": [],
                        "backend-dev": [],
                        "frontend-dev": [],
                        "code-reviewer": [],
                        "tester": [],
                    },
                },
                "go-kratos-web": {
                    "extends": "generic",
                    "keywords": ["shared", "kratos web"],
                },
            }
        )
        self.addCleanup(tempdir.cleanup)
        catalog = load_tech_profiles(path)

        resolved = resolve_tech_profile(catalog, explicit="go-kratos-web")

        self.assertEqual(resolved.data["keywords"], ["shared", "base", "kratos web"])

    def test_resolve_does_not_mutate_catalog(self):
        catalog = load_tech_profiles(self.path)
        catalog_snapshot = deepcopy(catalog)

        resolved = resolve_tech_profile(catalog, explicit="go-kratos-web")
        resolved.data["resolved_stack"]["runtime"]["frontend"] = "changed"
        resolved.data["role_focus"]["frontend-dev"].append("mutated")

        self.assertEqual(catalog, catalog_snapshot)


if __name__ == "__main__":
    unittest.main()
