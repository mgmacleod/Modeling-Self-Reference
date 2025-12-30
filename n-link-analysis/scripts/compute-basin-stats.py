#!/usr/bin/env python3
"""Compute basin / terminal statistics for fixed N-link rules.

Status: Placeholder (intentionally no implementation yet).

Planned:
- Input: data/wikipedia/processed/nlink_sequences.parquet
- For each N in a configured set:
  - Build f_N(page_id) = link_sequence[N-1] else HALT
  - Compute terminals (HALT or CYCLE) and basin sizes
  - Write per-N stats to data/wikipedia/processed/analysis/

See: ../implementation.md
"""


def main() -> None:
    raise NotImplementedError("Placeholder script; implement basin stats computation.")


if __name__ == "__main__":
    main()
