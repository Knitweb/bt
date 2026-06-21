from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import subprocess
from pathlib import Path


def run_git(args: list[str]) -> str:
    return subprocess.check_output(["git", *args], text=True).strip()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def remote_rows() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    output = run_git(["remote", "-v"])
    for line in output.splitlines():
        parts = line.split()
        if len(parts) != 3:
            continue
        rows.append({"name": parts[0], "url": parts[1], "mode": parts[2].strip("()")})
    return rows


def is_tagged_head() -> bool:
    result = subprocess.run(
        ["git", "describe", "--tags", "--exact-match", "HEAD"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    return result.returncode == 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Create a self-contained BT Git bundle and release manifest."
    )
    parser.add_argument("--output-dir", default="dist", help="directory for bundle output")
    parser.add_argument(
        "--allow-dirty",
        action="store_true",
        help="allow bundle creation when the working tree has uncommitted changes",
    )
    args = parser.parse_args(argv)

    status = run_git(["status", "--porcelain"])
    if status and not args.allow_dirty:
        raise SystemExit(
            "refusing to bundle a dirty working tree; commit changes or pass --allow-dirty"
        )

    commit = run_git(["rev-parse", "HEAD"])
    branch = run_git(["branch", "--show-current"]) or "detached"
    tag = run_git(["describe", "--tags", "--exact-match", "HEAD"]) if is_tagged_head() else None
    git_version = subprocess.check_output(["git", "--version"], text=True).strip()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    bundle = output_dir / f"bt-{commit[:12]}.bundle"
    manifest = output_dir / f"bt-{commit[:12]}.manifest.json"

    subprocess.check_call(
        ["git", "bundle", "create", str(bundle), "HEAD", "--branches", "--tags"]
    )
    bundle_hash = sha256_file(bundle)

    manifest_data = {
        "project": "BT",
        "repository": "Knitweb/bt",
        "created_at": dt.datetime.now(dt.UTC).isoformat(),
        "branch": branch,
        "head_commit": commit,
        "tag": tag,
        "dirty_worktree_allowed": bool(args.allow_dirty),
        "git_version": git_version,
        "bundle": {
            "path": str(bundle),
            "sha256": bundle_hash,
            "bytes": bundle.stat().st_size,
        },
        "remotes": remote_rows(),
        "included_refs": ["HEAD", "local branches", "tags"],
        "authority_rule": [
            "Verify the commit hash.",
            "Verify the signed tag when present.",
            "Verify the bundle SHA-256.",
            "Recover from any mirror or bundle with matching Git objects.",
        ],
        "restore_commands": [
            f"git bundle verify {bundle}",
            f"git clone {bundle} bt-restored",
            "git -C bt-restored fsck --strict",
        ],
        "non_github_routes_to_add": [
            "Knitweb-owned Forgejo mirror",
            "bare SSH mirror",
            "Radicle repository ID",
            "IPFS CID with multiple pins",
            "BitTorrent info hash with web seeds",
            "Software Heritage SWHID",
        ],
    }

    manifest.write_text(json.dumps(manifest_data, indent=2, sort_keys=True) + "\n")
    print(f"bundle: {bundle}")
    print(f"sha256: {bundle_hash}")
    print(f"manifest: {manifest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
