"""Phase 2: probe base vs evolved attacker harness with the PAID attacker model.

Usage: probe_paid.py --model <openrouter-model-id> [--episodes N]

Loads the evolved tree from the Phase-1 library, then runs N episodes each of
(base harness, paid model) and (evolved harness, paid model). Prints verdicts
and saves JSON. Hard-stops via the $10 spend cap in adapter.check_spend().
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

SRC = Path(__file__).resolve().parent
EXPERIMENT = SRC.parents[1]

os.environ["TMPDIR"] = str(EXPERIMENT / "tmp")
os.makedirs(os.environ["TMPDIR"], exist_ok=True)
sys.path.insert(0, str(SRC.parent))

from adapter import RedTeamAdapter, check_spend  # noqa: E402
from harness2.core import tree as HT  # noqa: E402
from harness2.core.library import Library  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True, help="OpenRouter model id for the paid attacker")
    ap.add_argument("--episodes", type=int, default=2)
    args = ap.parse_args()

    root = EXPERIMENT / "runs" / "redteam"
    adapter = RedTeamAdapter(root, attacker_model=args.model)
    surface = adapter.substrate.surface()

    lib = Library(root=root / "library" / "k1" / "seq", domain="redteam", surface=surface)
    evolved = lib.tree_of("invoice-scam")
    evolved_dir = root / "evolved_tree"
    HT.write_tree(surface, evolved, evolved_dir, stubs=False)
    print(f"evolved tree: {len(evolved)} files -> {evolved_dir}")

    spend, remaining = check_spend()
    print(f"spend before phase 2: ${spend:.4f} (remaining ${remaining:.2f})")

    results: dict = {"model": args.model, "episodes": []}
    for harness_name, harness_dir in (("base", adapter.base_harness()), ("evolved", evolved_dir)):
        for i in range(1, args.episodes + 1):
            run_id = f"paid-{harness_name}-{i}"
            run_dir = adapter.execute("invoice-scam", Path(harness_dir), run_id, timeout=1500)
            verdict = (run_dir / "verdict.txt").read_text().strip()
            results["episodes"].append(
                {"harness": harness_name, "run_id": run_id, "verdict": verdict,
                 "run_dir": str(run_dir)}
            )
            print(f"[{harness_name} #{i}] ATTACK_RESULT={verdict}")

    spend, remaining = check_spend()
    results["spend_usd"] = spend
    out = root / "phase2.json"
    out.write_text(json.dumps(results, indent=2) + "\n", encoding="utf-8")

    base_wins = sum(1 for e in results["episodes"] if e["harness"] == "base" and e["verdict"] == "SUCCESS")
    evo_wins = sum(1 for e in results["episodes"] if e["harness"] == "evolved" and e["verdict"] == "SUCCESS")
    print(f"paid attacker {args.model}: base {base_wins}/{args.episodes}, evolved {evo_wins}/{args.episodes}")
    print(f"total spend: ${spend:.4f}. {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
