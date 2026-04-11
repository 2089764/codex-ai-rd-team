from pathlib import Path


def main() -> int:
    repo_root = Path(__file__).resolve().parents[1]
    src = repo_root / "config" / "tech-profiles.json"
    dst = repo_root / "rd-team" / "shared-rd-resources" / "tech-profiles" / "tech-profiles.json"

    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(src.read_text(encoding="utf-8"), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
