#!/usr/bin/env python3
"""
Git repository statistics and contributor analysis.

Provides on-demand analysis of git history including:
- Contributor statistics (commits, lines added/deleted)
- Timeline analysis (commits per day, day of week, hour)
- File type breakdown
- Commit message patterns

Supports contributor aliases to consolidate multiple git identities.
"""

import subprocess
import json
import argparse
from collections import defaultdict
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Optional


# Default contributor aliases - maps git identity to canonical name
# Format: "Name <email>": "Canonical Name"
DEFAULT_ALIASES = {
    "Self Reference Modeling <srm@localhost>": "Will (WH)",
    # Add more aliases as needed
}


@dataclass
class ContributorStats:
    """Statistics for a single contributor."""
    name: str
    commits: int = 0
    files_changed: int = 0
    insertions: int = 0
    deletions: int = 0
    emails: set = field(default_factory=set)

    def to_dict(self):
        d = asdict(self)
        d['emails'] = list(self.emails)
        return d


@dataclass
class RepoStats:
    """Overall repository statistics."""
    total_commits: int = 0
    first_commit_date: str = ""
    last_commit_date: str = ""
    active_days: int = 0
    total_files_changed: int = 0
    total_insertions: int = 0
    total_deletions: int = 0


def run_git_command(cmd: list[str], cwd: Optional[Path] = None) -> str:
    """Run a git command and return stdout."""
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        cwd=cwd or Path.cwd()
    )
    if result.returncode != 0:
        raise RuntimeError(f"Git command failed: {' '.join(cmd)}\n{result.stderr}")
    return result.stdout.strip()


def load_aliases(alias_file: Optional[Path] = None) -> dict[str, str]:
    """Load contributor aliases from file or use defaults."""
    aliases = DEFAULT_ALIASES.copy()

    if alias_file and alias_file.exists():
        with open(alias_file) as f:
            custom_aliases = json.load(f)
            aliases.update(custom_aliases)

    return aliases


def get_canonical_name(author: str, email: str, aliases: dict[str, str]) -> str:
    """Get canonical contributor name, applying aliases."""
    identity = f"{author} <{email}>"
    return aliases.get(identity, author)


def get_contributor_stats(repo_path: Path, aliases: dict[str, str]) -> dict[str, ContributorStats]:
    """Get statistics per contributor."""
    contributors: dict[str, ContributorStats] = {}

    # Get commit counts and emails per author
    log_output = run_git_command(
        ["git", "log", "--format=%an|%ae"],
        cwd=repo_path
    )

    for line in log_output.split('\n'):
        if '|' not in line:
            continue
        author, email = line.split('|', 1)
        canonical = get_canonical_name(author, email, aliases)

        if canonical not in contributors:
            contributors[canonical] = ContributorStats(name=canonical)

        contributors[canonical].commits += 1
        contributors[canonical].emails.add(email)

    # Get insertions/deletions per author
    # This is more complex - need to parse shortstat output
    log_output = run_git_command(
        ["git", "log", "--format=%an|%ae", "--shortstat"],
        cwd=repo_path
    )

    current_author = None
    current_email = None

    for line in log_output.split('\n'):
        line = line.strip()
        if '|' in line and '@' in line:
            parts = line.split('|', 1)
            if len(parts) == 2:
                current_author, current_email = parts
        elif line and current_author:
            # Parse shortstat line: "X files changed, Y insertions(+), Z deletions(-)"
            files = insertions = deletions = 0
            parts = line.split(', ')
            for part in parts:
                if 'file' in part:
                    files = int(part.split()[0])
                elif 'insertion' in part:
                    insertions = int(part.split()[0])
                elif 'deletion' in part:
                    deletions = int(part.split()[0])

            canonical = get_canonical_name(current_author, current_email, aliases)
            if canonical in contributors:
                contributors[canonical].files_changed += files
                contributors[canonical].insertions += insertions
                contributors[canonical].deletions += deletions

    return contributors


def get_repo_stats(repo_path: Path) -> RepoStats:
    """Get overall repository statistics."""
    stats = RepoStats()

    # Total commits
    stats.total_commits = int(run_git_command(
        ["git", "rev-list", "--count", "HEAD"],
        cwd=repo_path
    ))

    # Date range
    dates = run_git_command(
        ["git", "log", "--format=%ad", "--date=short"],
        cwd=repo_path
    ).split('\n')

    if dates:
        sorted_dates = sorted(set(dates))
        stats.first_commit_date = sorted_dates[0]
        stats.last_commit_date = sorted_dates[-1]
        stats.active_days = len(sorted_dates)

    # Total changes
    shortstat = run_git_command(
        ["git", "log", "--shortstat", "--format="],
        cwd=repo_path
    )

    for line in shortstat.split('\n'):
        line = line.strip()
        if not line:
            continue
        parts = line.split(', ')
        for part in parts:
            if 'file' in part:
                stats.total_files_changed += int(part.split()[0])
            elif 'insertion' in part:
                stats.total_insertions += int(part.split()[0])
            elif 'deletion' in part:
                stats.total_deletions += int(part.split()[0])

    return stats


def get_commit_timeline(repo_path: Path) -> dict:
    """Get commit counts by various time dimensions."""
    timeline = {
        'by_date': defaultdict(int),
        'by_day_of_week': defaultdict(int),
        'by_hour': defaultdict(int),
    }

    # By date
    dates = run_git_command(
        ["git", "log", "--format=%ad", "--date=short"],
        cwd=repo_path
    ).split('\n')

    for date in dates:
        if date:
            timeline['by_date'][date] += 1

    # By day of week
    days = run_git_command(
        ["git", "log", "--format=%ad", "--date=format:%A"],
        cwd=repo_path
    ).split('\n')

    for day in days:
        if day:
            timeline['by_day_of_week'][day] += 1

    # By hour
    hours = run_git_command(
        ["git", "log", "--format=%ad", "--date=format:%H"],
        cwd=repo_path
    ).split('\n')

    for hour in hours:
        if hour:
            timeline['by_hour'][hour] += 1

    # Convert defaultdicts to regular dicts for JSON serialization
    return {k: dict(v) for k, v in timeline.items()}


def get_file_type_stats(repo_path: Path) -> dict[str, int]:
    """Get commit counts by file extension."""
    file_types: dict[str, int] = defaultdict(int)

    numstat = run_git_command(
        ["git", "log", "--numstat", "--format="],
        cwd=repo_path
    )

    for line in numstat.split('\n'):
        parts = line.split('\t')
        if len(parts) >= 3:
            filepath = parts[2]
            if '.' in filepath:
                ext = filepath.rsplit('.', 1)[-1]
                # Filter out likely binary/generated extensions
                if len(ext) <= 10 and ext.isalnum():
                    file_types[ext] += 1

    # Sort by count descending
    return dict(sorted(file_types.items(), key=lambda x: -x[1]))


def format_text_report(
    repo_stats: RepoStats,
    contributors: dict[str, ContributorStats],
    timeline: dict,
    file_types: dict[str, int]
) -> str:
    """Format statistics as a human-readable text report."""
    lines = []

    lines.append("=" * 60)
    lines.append("GIT REPOSITORY ANALYSIS")
    lines.append("=" * 60)
    lines.append("")

    # Overview
    lines.append("## Repository Overview")
    lines.append(f"Total commits:      {repo_stats.total_commits}")
    lines.append(f"First commit:       {repo_stats.first_commit_date}")
    lines.append(f"Last commit:        {repo_stats.last_commit_date}")
    lines.append(f"Active days:        {repo_stats.active_days}")
    lines.append(f"Total insertions:   {repo_stats.total_insertions:,}")
    lines.append(f"Total deletions:    {repo_stats.total_deletions:,}")
    lines.append("")

    # Contributors
    lines.append("## Contributors")
    lines.append("")

    sorted_contributors = sorted(
        contributors.values(),
        key=lambda c: c.commits,
        reverse=True
    )

    # Calculate percentages
    total_commits = sum(c.commits for c in sorted_contributors)

    lines.append(f"{'Contributor':<30} {'Commits':>8} {'%':>6} {'Ins':>10} {'Del':>10}")
    lines.append("-" * 70)

    for c in sorted_contributors:
        pct = (c.commits / total_commits * 100) if total_commits else 0
        lines.append(
            f"{c.name:<30} {c.commits:>8} {pct:>5.1f}% "
            f"{c.insertions:>10,} {c.deletions:>10,}"
        )
    lines.append("")

    # Timeline - Day of week
    lines.append("## Commits by Day of Week")
    day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    for day in day_order:
        count = timeline['by_day_of_week'].get(day, 0)
        bar = '#' * (count // 2)
        lines.append(f"  {day:<10} {count:>4}  {bar}")
    lines.append("")

    # Timeline - Peak hours
    lines.append("## Commits by Hour (Top 5)")
    sorted_hours = sorted(
        timeline['by_hour'].items(),
        key=lambda x: -x[1]
    )[:5]
    for hour, count in sorted_hours:
        lines.append(f"  {hour}:00  {count:>4}")
    lines.append("")

    # File types
    lines.append("## File Types (Top 10)")
    for ext, count in list(file_types.items())[:10]:
        lines.append(f"  .{ext:<10} {count:>5}")
    lines.append("")

    return '\n'.join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="Analyze git repository statistics"
    )
    parser.add_argument(
        "--repo", "-r",
        type=Path,
        default=Path.cwd(),
        help="Path to git repository (default: current directory)"
    )
    parser.add_argument(
        "--aliases", "-a",
        type=Path,
        help="JSON file with contributor aliases"
    )
    parser.add_argument(
        "--format", "-f",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)"
    )
    parser.add_argument(
        "--output", "-o",
        type=Path,
        help="Output file (default: stdout)"
    )

    args = parser.parse_args()

    # Load aliases
    aliases = load_aliases(args.aliases)

    # Gather statistics
    repo_stats = get_repo_stats(args.repo)
    contributors = get_contributor_stats(args.repo, aliases)
    timeline = get_commit_timeline(args.repo)
    file_types = get_file_type_stats(args.repo)

    # Format output
    if args.format == "json":
        output = json.dumps({
            "repo": asdict(repo_stats),
            "contributors": {k: v.to_dict() for k, v in contributors.items()},
            "timeline": timeline,
            "file_types": file_types,
        }, indent=2)
    else:
        output = format_text_report(repo_stats, contributors, timeline, file_types)

    # Write output
    if args.output:
        args.output.write_text(output)
        print(f"Report written to {args.output}")
    else:
        print(output)


if __name__ == "__main__":
    main()
