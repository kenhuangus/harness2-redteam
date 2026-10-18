"""Driver: run harness2's sequential Propose-Probe-Compose on the red-team adapter.

Phase 1 (this script): evolve the attacker harness with FREE models only
(attacker + improver + victim all $0). Saves the result JSON; the evolved
tree lands in the library at runs/redteam/library/k1/seq/.

Phase 2 (probe_paid.py, separate): probe base vs evolved harness with the
paid attacker model.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

SRC = Path(__file__).resolve().parent
EXPERIMENT = SRC.parents[1]

# Keep temp files off the 512MB /tmp tmpfs (see AGENTS.md).
os.environ["TMPDIR"] = str(EXPERIMENT / "tmp")
os.makedirs(os.environ["TMPDIR"], exist_ok=True)
sys.path.insert(0, str(SRC.parent))

from adapter import RedTeamAdapter  # noqa: E402
from harness2.core.proposer import Proposer  # noqa: E402
from harness2.core.schedule import run_domain  # noqa: E402


def main() -> int:
    root = EXPERIMENT / "runs" / "redteam"
    adapter = RedTeamAdapter(root)
    prop = Proposer(adapter.spec.channels["proposer"], audit_dir=root / "_audit")
    result = run_domain(
        "redteam",
        adapter.tasks(),
        1,
        adapter=adapter,
        prop=prop,
        runs_root=adapter.spec.runs_root,
        library_root=root / "library" / "k1",
        modes=("seq",),
    )
    report = root / "phase1.json"
    report.write_text(json.dumps(result, indent=2, default=str) + "\n", encoding="utf-8")
    print(f"Phase 1: {result['done']} tasks done; {result['failed']} failed. {report}")
    return int(result["failed"] > 0)


if __name__ == "__main__":
    raise SystemExit(main())
