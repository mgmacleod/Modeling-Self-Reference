# Deprecated Scripts

These scripts were superseded by improved versions. Kept for reference.

## Contents

| Script | Reason Deprecated | Replacement |
|--------|-------------------|-------------|
| `build-nlink-sequences.py` | DuckDB OOM on list aggregation | `build-nlink-sequences-v3.py` |
| `build-nlink-sequences-v2.py` | Used slow `iterrows()` iteration | `build-nlink-sequences-v3.py` |

## Notes

- **build-nlink-sequences.py**: Attempted DuckDB-native approach but OOM'd during `list()` aggregation of 206M links
- **build-nlink-sequences-v2.py**: Memory-efficient streaming but used Pandas `iterrows()` which is ~1000x slower than vectorized operations
