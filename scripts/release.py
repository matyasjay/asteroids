#!/usr/bin/env python3
"""Prepare semver release metadata from commit messages.

This script:
- determines latest semver tag (vX.Y.Z)
- parses commits since that tag using Conventional Commits
- calculates next version (auto or override)
- generates release notes markdown
- optionally updates pyproject.toml + CHANGELOG.md
- writes outputs for GitHub Actions via GITHUB_OUTPUT
"""

from __future__ import annotations

import argparse
import datetime as dt
import os
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path


TAG_PATTERN = "v[0-9]*.[0-9]*.[0-9]*"
CC_RE = re.compile(
    r"^(?P<type>[a-zA-Z]+)(\([^)]+\))?(?P<breaking>!)?:\s+(?P<desc>.+)$"
)
SEMVER_RE = re.compile(r"^(\d+)\.(\d+)\.(\d+)$")

CHANGELOG_HEADER = """# Changelog

All notable changes to this project will be documented in this file.
"""


@dataclass
class Commit:
    sha: str
    subject: str
    body: str
    cc_type: str
    description: str
    breaking: bool


def sh(*args: str) -> str:
    return subprocess.check_output(args, text=True).strip()


def git_latest_tag() -> str | None:
    out = sh("git", "tag", "--list", TAG_PATTERN, "--sort=-v:refname")
    if not out:
        return None
    return out.splitlines()[0].strip()


def parse_commit(subject: str, body: str) -> tuple[str, str, bool]:
    match = CC_RE.match(subject)
    if not match:
        return "other", subject.strip(), "BREAKING CHANGE" in body

    cc_type = match.group("type").lower()
    desc = match.group("desc").strip()
    breaking = bool(match.group("breaking")) or ("BREAKING CHANGE" in body)
    return cc_type, desc, breaking


def git_commits_since(last_tag: str | None) -> list[Commit]:
    range_expr = "HEAD" if last_tag is None else f"{last_tag}..HEAD"
    raw = sh("git", "log", "--pretty=format:%H%x1f%s%x1f%b%x1e", range_expr)
    commits: list[Commit] = []
    for row in raw.split("\x1e"):
        if not row.strip():
            continue
        parts = row.split("\x1f")
        if len(parts) < 2:
            continue
        if len(parts) == 2:
            parts.append("")

        sha = parts[0].strip()
        subject = parts[1].strip()
        body = "\x1f".join(parts[2:]).strip()
        cc_type, desc, breaking = parse_commit(subject, body)
        commits.append(
            Commit(
                sha=sha,
                subject=subject,
                body=body,
                cc_type=cc_type,
                description=desc,
                breaking=breaking,
            )
        )
    return commits


def read_pyproject_version(pyproject_path: Path) -> str:
    content = pyproject_path.read_text(encoding="utf-8")
    in_project = False
    for line in content.splitlines():
        stripped = line.strip()
        if stripped.startswith("[") and stripped.endswith("]"):
            in_project = stripped == "[project]"
            continue
        if in_project and stripped.startswith("version"):
            match = re.match(r'version\s*=\s*"([^"]+)"', stripped)
            if match:
                return match.group(1)
    raise RuntimeError("Could not find [project].version in pyproject.toml")


def determine_bump(commits: list[Commit], strategy: str) -> str:
    if strategy in {"major", "minor", "patch"}:
        return strategy

    bump = "none"
    for commit in commits:
        if commit.breaking:
            return "major"
        if commit.cc_type == "feat":
            bump = "minor"
        elif commit.cc_type in {"fix", "perf", "refactor"} and bump == "none":
            bump = "patch"
    return bump


def bump_version(current_version: str, bump: str) -> str:
    match = SEMVER_RE.match(current_version)
    if not match:
        raise RuntimeError(
            f"Current version '{current_version}' is not strict semver (X.Y.Z)."
        )

    major, minor, patch = (int(match.group(1)), int(match.group(2)), int(match.group(3)))
    if bump == "major":
        return f"{major + 1}.0.0"
    if bump == "minor":
        return f"{major}.{minor + 1}.0"
    if bump == "patch":
        return f"{major}.{minor}.{patch + 1}"
    raise RuntimeError(f"Unsupported bump type: {bump}")


def build_sections(commits: list[Commit]) -> dict[str, list[str]]:
    sections: dict[str, list[str]] = {
        "Breaking Changes": [],
        "Added": [],
        "Fixed": [],
        "Changed": [],
        "Documentation": [],
        "Chore": [],
        "Other": [],
    }

    for commit in commits:
        short = commit.sha[:7]
        item = f"- {commit.description} (`{short}`)"
        if commit.breaking:
            sections["Breaking Changes"].append(item)

        if commit.cc_type == "feat":
            sections["Added"].append(item)
        elif commit.cc_type == "fix":
            sections["Fixed"].append(item)
        elif commit.cc_type in {"refactor", "perf"}:
            sections["Changed"].append(item)
        elif commit.cc_type == "docs":
            sections["Documentation"].append(item)
        elif commit.cc_type in {"chore", "ci", "build", "test"}:
            sections["Chore"].append(item)
        else:
            sections["Other"].append(f"- {commit.subject} (`{short}`)")

    return sections


def render_section_lines(sections: dict[str, list[str]]) -> list[str]:
    lines: list[str] = []
    for name in (
        "Breaking Changes",
        "Added",
        "Fixed",
        "Changed",
        "Documentation",
        "Chore",
        "Other",
    ):
        items = sections[name]
        if not items:
            continue
        lines.append(f"### {name}")
        lines.extend(items)
        lines.append("")
    return lines


def render_release_notes(version: str, last_tag: str | None, commits: list[Commit]) -> str:
    sections = build_sections(commits)
    lines = [f"## v{version}", ""]
    if last_tag:
        lines.append(f"Changes since `{last_tag}`:")
    else:
        lines.append("Initial tagged release notes:")
    lines.append("")
    lines.extend(render_section_lines(sections))

    if lines[-1] != "":
        lines.append("")
    return "\n".join(lines)


def render_changelog_entry(version: str, commits: list[Commit]) -> str:
    date = dt.date.today().isoformat()
    sections = build_sections(commits)
    body = "\n".join(render_section_lines(sections)).strip()
    return f"## [{version}] - {date}\n\n{body}\n"


def update_pyproject_version(pyproject_path: Path, new_version: str) -> None:
    content = pyproject_path.read_text(encoding="utf-8")
    updated, count = re.subn(
        r'(?m)^(version\s*=\s*")[^"]+(")$',
        rf"\g<1>{new_version}\g<2>",
        content,
        count=1,
    )
    if count != 1:
        raise RuntimeError("Failed to update version in pyproject.toml")
    pyproject_path.write_text(updated, encoding="utf-8")


def update_changelog(changelog_path: Path, version: str, entry: str) -> None:
    if changelog_path.exists():
        content = changelog_path.read_text(encoding="utf-8")
    else:
        content = CHANGELOG_HEADER + "\n"

    if f"## [{version}]" in content:
        raise RuntimeError(f"CHANGELOG already has an entry for version {version}")

    if content.startswith("# Changelog"):
        header, _, rest = content.partition("\n\n")
        new_content = f"{header}\n\n{entry}\n{rest.lstrip()}"
    else:
        new_content = f"{CHANGELOG_HEADER}\n{entry}\n{content}"

    changelog_path.write_text(new_content, encoding="utf-8")


def write_github_output(values: dict[str, str]) -> None:
    output_path = os.getenv("GITHUB_OUTPUT")
    if not output_path:
        return

    with open(output_path, "a", encoding="utf-8") as file:
        for key, value in values.items():
            file.write(f"{key}={value}\n")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Prepare release metadata.")
    parser.add_argument(
        "--strategy",
        choices=["auto", "major", "minor", "patch"],
        default="auto",
        help="Version bump strategy.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Do not modify files; only compute outputs.",
    )
    parser.add_argument(
        "--prerelease",
        action="store_true",
        help="Flag release as prerelease (metadata output only).",
    )
    parser.add_argument(
        "--notes-file",
        default=".release/release-notes.md",
        help="Path for generated release notes markdown.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    pyproject_path = Path("pyproject.toml")
    changelog_path = Path("CHANGELOG.md")
    notes_path = Path(args.notes_file)
    notes_path.parent.mkdir(parents=True, exist_ok=True)

    current_version = read_pyproject_version(pyproject_path)
    last_tag = git_latest_tag()
    commits = git_commits_since(last_tag)

    if not commits:
        print("No commits available for release range.", file=sys.stderr)
        return 1

    bump = determine_bump(commits, args.strategy)
    if bump == "none":
        print(
            "No SemVer-eligible commits found for auto strategy. "
            "Use --strategy major|minor|patch to force a release.",
            file=sys.stderr,
        )
        return 1

    next_version = bump_version(current_version, bump)
    tag = f"v{next_version}"
    release_notes = render_release_notes(next_version, last_tag, commits)
    notes_path.write_text(release_notes, encoding="utf-8")

    if not args.dry_run:
        update_pyproject_version(pyproject_path, next_version)
        changelog_entry = render_changelog_entry(next_version, commits)
        update_changelog(changelog_path, next_version, changelog_entry)

    write_github_output(
        {
            "current_version": current_version,
            "version": next_version,
            "tag": tag,
            "last_tag": last_tag or "",
            "bump": bump,
            "notes_file": str(notes_path),
            "prerelease": "true" if args.prerelease else "false",
            "dry_run": "true" if args.dry_run else "false",
        }
    )

    print(f"Current version: {current_version}")
    print(f"Last tag: {last_tag or 'none'}")
    print(f"Selected bump: {bump}")
    print(f"Next version: {next_version}")
    print(f"Release notes: {notes_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
