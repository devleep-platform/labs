#!/usr/bin/env python3
"""Validate lab YAML files against the Devloop schema."""
import sys
from pathlib import Path
import yaml

REQUIRED_FIELDS = [
    "schema_version", "id", "title", "description", "track", "module",
    "sort_order", "difficulty", "engineer_level", "mode", "tags",
    "estimated_minutes", "timeout_minutes", "terraform_module",
    "scenario_id", "prerequisites", "objectives", "success_criteria",
    "hints", "hint_policy", "validation",
]

VALID_DIFFICULTIES  = {"beginner", "intermediate", "advanced", "expert"}
VALID_TERRAFORM     = {"labs/linux-ec2", "labs/docker-ec2", "labs/kubernetes-eks"}
VALID_TRACKS        = {"linux", "docker", "kubernetes", "ansible", "git", "jenkins"}
VALID_MODES         = {"guided", "incident", "challenge"}
VALID_HINT_POLICIES = {"show_level_1_automatically", "manual_only"}
VALID_CHECK_TYPES   = {"ssh", "output_matches", "http_get", "multi_check"}


def validate_file(path: Path) -> list:
    errors = []
    try:
        with open(path, encoding="utf-8") as f:
            lab = yaml.safe_load(f)
    except yaml.YAMLError as e:
        return [f"YAML parse error: {e}"]

    if not isinstance(lab, dict):
        return ["File does not contain a YAML mapping"]

    # Required fields
    for field in REQUIRED_FIELDS:
        if field not in lab:
            errors.append(f"Missing required field: {field}")

    if errors:
        return errors  # stop early — basic structure is broken

    # schema_version
    if lab.get("schema_version") != 1:
        errors.append("schema_version must be 1")

    # id must match filename (without extension)
    if lab.get("id") != path.stem:
        errors.append(f"id '{lab.get('id')}' must match filename '{path.stem}'")

    # enums
    if lab.get("difficulty") not in VALID_DIFFICULTIES:
        errors.append(f"difficulty must be one of: {', '.join(sorted(VALID_DIFFICULTIES))}")

    if lab.get("terraform_module") not in VALID_TERRAFORM:
        errors.append(f"terraform_module must be one of: {', '.join(sorted(VALID_TERRAFORM))}")

    if lab.get("track") not in VALID_TRACKS:
        errors.append(f"track must be one of: {', '.join(sorted(VALID_TRACKS))}")

    if lab.get("mode") not in VALID_MODES:
        errors.append(f"mode must be one of: {', '.join(sorted(VALID_MODES))}")

    if lab.get("hint_policy") not in VALID_HINT_POLICIES:
        errors.append(f"hint_policy must be one of: {', '.join(sorted(VALID_HINT_POLICIES))}")

    # title length
    if len(lab.get("title", "")) > 100:
        errors.append("title must be 100 characters or fewer")

    # objectives: at least 1
    objectives = lab.get("objectives", [])
    if not isinstance(objectives, list) or len(objectives) < 1:
        errors.append("objectives must have at least 1 item")

    # hints: must have levels 1, 2, 3
    hints = lab.get("hints", [])
    if not isinstance(hints, list):
        errors.append("hints must be a list")
    else:
        levels = {h.get("level") for h in hints if isinstance(h, dict)}
        for lvl in [1, 2, 3]:
            if lvl not in levels:
                errors.append(f"hints must include level {lvl}")
        for i, h in enumerate(hints):
            if not isinstance(h, dict):
                errors.append(f"hints[{i}] must be a mapping")
                continue
            if not h.get("text", "").strip():
                errors.append(f"hints[{i}] (level {h.get('level')}) text must not be empty")

    # validation.checks: at least 1
    validation = lab.get("validation", {})
    checks = validation.get("checks", []) if isinstance(validation, dict) else []
    if not isinstance(checks, list) or len(checks) < 1:
        errors.append("validation.checks must have at least 1 check")
    else:
        for i, check in enumerate(checks):
            if not isinstance(check, dict):
                errors.append(f"validation.checks[{i}] must be a mapping")
                continue
            for req in ["id", "name", "type"]:
                if req not in check:
                    errors.append(f"validation.checks[{i}] missing required field: {req}")
            if check.get("type") not in VALID_CHECK_TYPES:
                errors.append(
                    f"validation.checks[{i}].type must be one of: {', '.join(sorted(VALID_CHECK_TYPES))}"
                )

    # estimated_minutes sanity
    mins = lab.get("estimated_minutes", 0)
    if not isinstance(mins, int) or mins < 5 or mins > 480:
        errors.append("estimated_minutes must be an integer between 5 and 480")

    return errors


def main():
    # If files passed as arguments, validate only those; otherwise validate all
    if len(sys.argv) > 1:
        files = [Path(f) for f in sys.argv[1:] if f.strip() and f.endswith(".yaml")]
    else:
        files = sorted(Path("labs").rglob("*.yaml"))

    if not files:
        print("No YAML files to validate.")
        return 0

    total_errors = 0
    results = []

    for path in files:
        errs = validate_file(path)
        results.append((path, errs))
        total_errors += len(errs)

    for path, errs in results:
        if errs:
            print(f"\n❌  {path}")
            for e in errs:
                print(f"   • {e}")
        else:
            print(f"✅  {path}")

    print(f"\n{'─' * 48}")
    print(f"Validated {len(files)} file(s). {total_errors} error(s) found.")

    return 1 if total_errors > 0 else 0


if __name__ == "__main__":
    sys.exit(main())
