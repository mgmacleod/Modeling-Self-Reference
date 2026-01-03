# Project Tools

Utility scripts for project maintenance and analysis.

## git_stats.py

Analyzes git repository history and generates contributor statistics.

### Usage

```bash
# Basic usage (text output)
python tools/git_stats.py

# With contributor aliases
python tools/git_stats.py --aliases tools/contributor_aliases.json

# JSON output
python tools/git_stats.py --format json

# Save to file
python tools/git_stats.py --output report.txt
```

### Features

- **Contributor Statistics**: Commits, insertions, deletions per contributor
- **Timeline Analysis**: Commits by date, day of week, and hour
- **File Type Breakdown**: Which file types are most frequently changed
- **Contributor Aliases**: Consolidate multiple git identities into canonical names

### Alias File Format

Create a JSON file mapping git identities to canonical names:

```json
{
    "Some Name <email@example.com>": "Canonical Name",
    "Another Name <other@example.com>": "Canonical Name"
}
```

### Options

| Option | Description |
|--------|-------------|
| `--repo, -r` | Path to git repository (default: current directory) |
| `--aliases, -a` | JSON file with contributor aliases |
| `--format, -f` | Output format: `text` or `json` (default: text) |
| `--output, -o` | Output file (default: stdout) |
