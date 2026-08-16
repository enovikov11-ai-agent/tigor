#!/usr/bin/env python3
"""
GitHub sync — merges github-pull.py + github-in.sh.
Source of truth: projects.yml (entries with `github` + `sync: in/out`).

Fast mode (default): rsync only, no git/network.
Full mode (--full): clone missing repos, git-pull existing ones, then rsync.

  sync: in   →  github clone → monorepo  (skip if monorepo dir has uncommitted changes)
  sync: out  →  monorepo → github clone  (skip if github clone or monorepo dir has uncommitted changes)

In --full mode, git pull is skipped if the github clone has uncommitted changes
or is on a non-default branch.
"""
import sys
import subprocess
import re
import argparse
from pathlib import Path

import yaml  # PyYAML

MONOREPO = Path(__file__).resolve().parents[2]
GITHUB_DIR = Path.home() / "Desktop" / "github"
IS_TTY = sys.stdout.isatty()

parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
parser.add_argument("--full", action="store_true", help="Clone missing repos and git-pull before rsyncing")
args = parser.parse_args()


def _ok(label):
    if IS_TTY:
        sys.stdout.write(f"\r\033[K  {label}")
        sys.stdout.flush()
    else:
        print(f"  {label}")


def _fail(label, reason):
    if IS_TTY:
        sys.stdout.write("\r\033[K")
    print(f"SKIP {label}: {reason}")


def _changed(label, n):
    if IS_TTY:
        sys.stdout.write("\r\033[K")
    print(f"CHANGED {label}: {n} file(s)")


def _done():
    if IS_TTY:
        sys.stdout.write("\r\033[K")
    print("done")


def run(*cmd, cwd):
    return subprocess.run(list(cmd), cwd=str(cwd), capture_output=True, text=True)


def git_has_changes(path):
    return bool(run("git", "status", "--porcelain", cwd=path).stdout.strip())


def git_current_branch(path):
    return run("git", "branch", "--show-current", cwd=path).stdout.strip()


def git_default_branch(path):
    r = run("git", "symbolic-ref", "refs/remotes/origin/HEAD", cwd=path)
    if r.returncode == 0:
        return r.stdout.strip().split("/")[-1]
    for b in ("main", "master"):
        if run("git", "rev-parse", "--verify", f"refs/remotes/origin/{b}", cwd=path).returncode == 0:
            return b
    return "main"


def monorepo_dir_has_changes(monorepo_path):
    rel = str(monorepo_path.relative_to(MONOREPO))
    return bool(run("git", "status", "--porcelain", "--", rel, cwd=MONOREPO).stdout.strip())


with open(MONOREPO / "projects.yml") as f:
    projects = yaml.safe_load(f)

syncs = []
for domain, items in projects.items():
    for name, meta in items.items():
        if not isinstance(meta, dict):
            continue
        github_url = meta.get("github", "")
        sync_dir = meta.get("sync", "")
        if not github_url or not sync_dir:
            continue
        m = re.match(r"https://github\.com/([^/]+)/([^/]+?)(?:\.git)?$", github_url)
        if not m:
            continue
        org, repo = m.group(1), m.group(2)
        syncs.append({
            "label": f"{org}/{repo}",
            "direction": sync_dir,
            "monorepo": MONOREPO / domain / str(name),
            "github": GITHUB_DIR / org / repo,
            "clone_url": f"https://github.com/{org}/{repo}.git",
        })

for s in syncs:
    label = s["label"]
    direction = s["direction"]
    monorepo_path = s["monorepo"]
    github_path = s["github"]

    _ok(label)

    # Ensure github clone exists
    if not github_path.exists():
        if not args.full:
            _fail(label, "not cloned locally (run --full to clone)")
            continue
        _ok(f"cloning {label}")
        github_path.parent.mkdir(parents=True, exist_ok=True)
        r = run("git", "clone", s["clone_url"], str(github_path), cwd=github_path.parent)
        if r.returncode != 0:
            _fail(label, f"clone failed: {r.stderr.strip()[:100]}")
            continue

    # Full mode: git pull (with safety checks)
    if args.full:
        if git_has_changes(github_path):
            _fail(label, "github clone has uncommitted changes, skipping pull+sync")
            continue
        default = git_default_branch(github_path)
        current = git_current_branch(github_path)
        if current != default:
            _fail(label, f"github clone on '{current}' not '{default}', skipping pull+sync")
            continue
        _ok(f"pulling {label}")
        r = run("git", "pull", "--ff-only", cwd=github_path)
        if r.returncode != 0:
            _fail(label, f"pull failed: {r.stderr.strip()[:100]}")
            continue

    # Rsync
    if direction == "in":
        if monorepo_dir_has_changes(monorepo_path):
            _fail(label, "monorepo dir has uncommitted changes")
            continue
        src, dst = github_path, monorepo_path
    elif direction == "out":
        if git_has_changes(github_path):
            _fail(label, "github clone has uncommitted changes")
            continue
        if monorepo_dir_has_changes(monorepo_path):
            _fail(label, "monorepo dir has uncommitted changes")
            continue
        src, dst = monorepo_path, github_path
    else:
        _fail(label, f"unknown sync direction '{direction}'")
        continue

    dst.mkdir(parents=True, exist_ok=True)
    r = subprocess.run(
        ["rsync", "-rc", "--delete", "--exclude=.git", "--itemize-changes",
         str(src) + "/", str(dst) + "/"],
        capture_output=True, text=True,
    )
    if r.returncode != 0:
        _fail(label, f"rsync error: {r.stderr.strip()[:100]}")
        continue

    # Remove LFS pointer stubs — GitHub repos with LFS produce these instead of real files
    lfs_removed = 0
    for f in dst.rglob("*"):
        if not f.is_file() or f.stat().st_size > 200:
            continue
        try:
            with open(f, "r") as fh:
                if fh.readline().startswith("version https://git-lfs.github.com/spec/v1"):
                    f.unlink()
                    lfs_removed += 1
        except (UnicodeDecodeError, OSError):
            pass
    if lfs_removed:
        _fail(label, f"removed {lfs_removed} LFS pointer stub(s)")

    if r.stdout.strip():
        _changed(label, r.stdout.strip().count("\n") + 1)

_done()
