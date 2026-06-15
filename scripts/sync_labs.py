#!/usr/bin/env python3
"""Sync all lab YAML files to the Devloop platform API."""
import os
import sys
from pathlib import Path

import requests

BOM = "﻿"


def clean(value):
    """Strip whitespace and BOM from an env var value."""
    return value.strip().strip(BOM)


def main():
    api_url = clean(os.environ.get("PLATFORM_API_URL", "")).rstrip("/")
    secret = clean(os.environ.get("LAB_SYNC_SECRET", ""))

    print(f"DEBUG: secret_len={len(secret)} url_len={len(api_url)}")

    if not api_url:
        print("ERROR: PLATFORM_API_URL environment variable is not set")
        sys.exit(1)
    if not secret:
        print("ERROR: LAB_SYNC_SECRET environment variable is not set")
        sys.exit(1)

    lab_files = sorted(Path("labs").rglob("*.yaml"))
    if not lab_files:
        print("No lab YAML files found in labs/ -- nothing to sync")
        sys.exit(0)

    labs = []
    for path in lab_files:
        with open(path, encoding="utf-8-sig") as f:
            content = f.read()
        labs.append({"filename": str(path), "content": content})

    print(f"Syncing {len(labs)} lab(s) to {api_url}/admin/labs/sync ...")

    try:
        resp = requests.post(
            f"{api_url}/admin/labs/sync",
            json={"labs": labs},
            headers={"X-Lab-Sync-Secret": secret},
            timeout=60,
        )
        resp.raise_for_status()
        result = resp.json()
    except requests.HTTPError as e:
        print(f"ERROR: HTTP {e.response.status_code} -- {e.response.text}")
        sys.exit(1)
    except Exception as e:
        print(f"ERROR: {e}")
        sys.exit(1)

    synced = result.get("synced", 0)
    failed = result.get("failed", [])

    print(f"Synced: {synced}")
    if failed:
        print(f"Failed ({len(failed)}):")
        for f in failed:
            print(f"  - {f}")
        sys.exit(1)

    print("All labs are live on the platform.")


if __name__ == "__main__":
    main()
