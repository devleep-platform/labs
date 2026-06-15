#!/usr/bin/env python3
"""Sync all lab YAML files to the Devloop platform API."""
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path


def main():
    api_url = os.environ.get("PLATFORM_API_URL", "").rstrip("/")
    secret = os.environ.get("LAB_SYNC_SECRET", "")

    if not api_url:
        print("ERROR: PLATFORM_API_URL environment variable is not set")
        sys.exit(1)
    if not secret:
        print("ERROR: LAB_SYNC_SECRET environment variable is not set")
        sys.exit(1)

    lab_files = sorted(Path("labs").rglob("*.yaml"))
    if not lab_files:
        print("No lab YAML files found in labs/ — nothing to sync")
        sys.exit(0)

    labs = []
    for path in lab_files:
        with open(path, encoding="utf-8") as f:
            content = f.read()
        labs.append({"filename": str(path), "content": content})

    print(f"Syncing {len(labs)} lab(s) to {api_url}/admin/labs/sync ...")

    payload = json.dumps({"labs": labs}).encode("utf-8")
    req = urllib.request.Request(
        f"{api_url}/admin/labs/sync",
        data=payload,
        headers={
            "Content-Type": "application/json",
            "X-Lab-Sync-Secret": secret,
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=60) as response:
            result = json.loads(response.read())
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        print(f"ERROR: HTTP {e.code} from platform API — {body}")
        sys.exit(1)
    except Exception as e:
        print(f"ERROR: {e}")
        sys.exit(1)

    synced = result.get("synced", 0)
    failed = result.get("failed", [])

    print(f"✅  Synced: {synced}")
    if failed:
        print(f"❌  Failed ({len(failed)}):")
        for f in failed:
            print(f"   • {f}")
        sys.exit(1)

    print("All labs are live on the platform.")


if __name__ == "__main__":
    main()
