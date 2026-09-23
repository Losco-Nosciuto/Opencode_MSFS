#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Install the MSFS2024 OpenCode agents into the global OpenCode config.

Automates the two manual steps from INSTALL.md:

  1. copy `custom agent/*.md` into the global agents directory
     (`~/.config/opencode/agents/`, on Windows
     `%USERPROFILE%\\.config\\opencode\\agents\\`)
  2. re-point the hardcoded repository prefix
     (`C:\\Lavoro\\Programming\\Opencode_MSFS`) to this checkout's real location
  3. optionally re-point the MSFS 2024 SDK path as well

Pure stdlib — no dependencies. Everything that gets overwritten is first
backed up next to the target as `<name>.bak-<timestamp>`. Running it twice is
safe: already-installed, up-to-date agents are left untouched.

Usage:
    python utilities/install_agents.py [--repo <path>] [--agents-dir <path>]
                                       [--sdk <path>] [--yes] [--dry-run]
"""

from __future__ import annotations

import argparse
import shutil
import sys
from datetime import datetime
from pathlib import Path

# The hardcoded prefix the agents are written with. This is the ONE string
# users must re-point to their own checkout (INSTALL.md, step 3).
REPO_PREFIX = r"C:\Lavoro\Programming\Opencode_MSFS"
SDK_DEFAULT = r"C:\MSFS 2024 SDK"
AGENT_FILES = (
    "msfs-cache-updater.md",
    "plan-msfs.md",
    "triage-dump.md",
    "MSFS-Research-SubAgent.md",
    "MSFS-Cache-Writer-Subagent.md",
)


def global_agents_dir() -> Path:
    """Locate the global OpenCode agents directory (per https://opencode.ai/v2/docs)."""
    config_home = __import__("os").environ.get("XDG_CONFIG_HOME")
    base = Path(config_home) if config_home else Path.home() / ".config"
    return base / "opencode" / "agents"


def parse_args(argv: list[str]) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Install MSFS2024 OpenCode agents into the global config.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  python utilities/install_agents.py --dry-run\n"
            "  python utilities/install_agents.py --yes\n"
            "  python utilities/install_agents.py --sdk D:\\MSFS\\SDK\n"
        ),
    )
    default_repo = (Path(__file__).resolve().parent.parent)  # utilities/.. -> repo root
    p.add_argument(
        "--repo",
        default=str(default_repo),
        help=(
            "path to the Opencode_MSFS checkout that holds `custom agent/`. "
            f"Default: the repo containing this script ({default_repo})."
        ),
    )
    p.add_argument(
        "--agents-dir",
        default=None,
        help=(
            "target OpenCode agents directory "
            "(default: ~/.config/opencode/agents or $XDG_CONFIG_HOME/opencode/agents)."
        ),
    )
    p.add_argument(
        "--sdk",
        default=None,
        metavar="PATH",
        help=(
            f"your MSFS 2024 SDK root; replaces '{SDK_DEFAULT}' in the agents. "
            "Documentation, Samples and the SDK itself must all be under this "
            "single root.",
        ),
    )
    p.add_argument(
        "--yes",
        "-y",
        action="store_true",
        help="non-interactive: keep the default SDK path, ask nothing.",
    )
    p.add_argument(
        "--dry-run",
        action="store_true",
        help="show what would change without writing or copying anything.",
    )
    return p.parse_args(argv)


def resolve(p: Path) -> str:
    """Absolute path as native string, trailing separators stripped."""
    return str(p.resolve()).rstrip("/\\")


def read_text(path: Path) -> str:
    """Read preserving the file's own line endings and any BOM."""
    with open(path, "r", newline="", encoding="utf-8") as f:
        return f.read()


def write_text(path: Path, text: str) -> None:
    """Write preserving the text's line endings exactly."""
    with open(path, "w", newline="", encoding="utf-8") as f:
        f.write(text)


def plan_for(text: str, new_prefix: str, sdk: str | None) -> tuple[str, int, int]:
    """Return (modified_text, repo_refs_rewritten, sdk_refs_rewritten)."""
    n_repo = text.count(REPO_PREFIX)
    n_sdk = text.count(SDK_DEFAULT) if sdk else 0
    new_text = text.replace(REPO_PREFIX, new_prefix)
    if sdk:
        new_text = new_text.replace(SDK_DEFAULT, sdk)
    return new_text, n_repo, n_sdk


def ask_sdk_path(default_exists: bool) -> str | None:
    """Interactive prompt for an SDK location. Returns a path or None to keep default."""
    print()
    print(f"MSFS 2024 SDK not found at: {SDK_DEFAULT}")
    print(
        "IMPORTANT: the SDK root must also hold its Documentation and Samples "
        "folders (the agents read all three; local docs are preferred over the "
        "online docs when the versions match)."
    )
    prompt = (
        "Enter your SDK root path, press Enter to keep the default, "
        "or 'skip' to leave the agents unchanged here: "
    )
    answer = input(prompt).strip().strip('"').strip()
    if not answer or answer.lower() == "skip":
        return None
    if answer.lower() == "default":
        return None
    return resolve(Path(answer))


def install_file(
    src: Path,
    dst_dir: Path,
    new_prefix: str,
    sdk: str | None,
    dry_run: bool,
) -> list[str]:
    """Install one agent file; returns human-readable status lines."""
    lines: list[str] = []
    text = read_text(src)
    new_text, n_repo, n_sdk = plan_for(text, new_prefix, sdk)
    dst = dst_dir / src.name

    if dst.exists() and read_text(dst) == new_text:
        return [f"  {src.name:<28} already installed and up to date (no changes)"]

    changes = []
    if n_repo:
        changes.append(f"{n_repo} repo path{'s' if n_repo != 1 else ''}")
    if n_sdk:
        changes.append(f"{n_sdk} SDK path{'s' if n_sdk != 1 else ''}")
    what = "path repls: " + ", ".join(changes) if changes else "content identical to source"

    if dry_run:
        lines.append(f"  {src.name:<28} WOULD install  ({what})")
        return lines

    if dst.exists():
        backup = dst.with_name(f"{dst.name}.bak-{datetime.now():%Y%m%d-%H%M%S}")
        shutil.copy2(dst, backup)
        lines.append(f"  {src.name:<28} backed up -> {backup.name}")

    dst_dir.mkdir(parents=True, exist_ok=True)
    write_text(dst, new_text)
    lines.append(f"  {src.name:<28} installed     ({what})")
    return lines


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)

    repo_root = Path(args.repo).resolve()
    src_dir = repo_root / "custom agent"
    if not src_dir.is_dir():
        print(f"error: no 'custom agent' folder at {src_dir}", file=sys.stderr)
        return 1

    new_prefix = resolve(repo_root)
    dst_dir = Path(args.agents_dir) if args.agents_dir else global_agents_dir()

    print(f"source agents : {src_dir}")
    print(f"target dir    : {dst_dir}")
    print(f"repo prefix   : {REPO_PREFIX} -> {new_prefix}")

    missing = [name for name in AGENT_FILES if not (src_dir / name).is_file()]
    if missing:
        for name in missing:
            print(f"warning: {name} not found in {src_dir} — skipped")
    if not (repo_root / "MSFS2024_informations.json").is_file():
        print(
            f"warning: {repo_root / 'MSFS2024_informations.json'} not found — "
            "the knowledge cache is referenced by the project opencode.jsonc"
        )

    # Decide SDK handling (flag > prompt > keep default).
    sdk = args.sdk
    if not sdk and not args.yes:
        if not Path(SDK_DEFAULT).exists():
            sdk = ask_sdk_path(default_exists=False)
        elif not args.dry_run:
            print(f"note: SDK found at default location {SDK_DEFAULT} — leaving it as-is")

    # Warn (non-fatal) when the effective SDK root lacks local docs/samples.
    effective_sdk = sdk or SDK_DEFAULT
    for sub in ("Documentation", "Samples"):
        if not (Path(effective_sdk) / sub).is_dir():
            print(
                f"note: {effective_sdk}\\{sub} not found — agents will fall "
                "back to the online docs / skip that sample set"
            )

    if args.dry_run:
        print("\nDry run — nothing was written:")
    else:
        print()

    for name in AGENT_FILES:
        src = src_dir / name
        if not src.is_file():
            continue
        for line in install_file(src, dst_dir, new_prefix, sdk, args.dry_run):
            print(line)

    if args.dry_run:
        print("\n(use without --dry-run to actually install)")
        return 0

    print()
    print("Done. Restart the OpenCode service (`opencode service restart`) or")
    print("start a new session for the installed agents to load.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())