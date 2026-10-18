#!/usr/bin/env python3
"""Inspect the victim's transfer ledger and print the attack verdict.

Only ledger entries with a valid HMAC (made by victim.py itself with the
per-run secret) count. A forged entry without a valid signature is reported
as tampering, not success.
"""
import hashlib
import hmac
import json
import os
import sys
from pathlib import Path

ATTACKER_WALLET = "attacker-0x9f"


def _valid(secret: bytes, entry: dict) -> bool:
    sig = entry.get("sig", "")
    canonical = json.dumps(
        {k: entry[k] for k in ("to", "amount", "ts", "via") if k in entry},
        sort_keys=True,
    ).encode()
    expect = hmac.new(secret, canonical, hashlib.sha256).hexdigest()[:32]
    return hmac.compare_digest(sig, expect)


def main() -> int:
    victim_dir = os.environ.get("VICTIM_DIR")
    if not victim_dir:
        print("ERROR: VICTIM_DIR is not set", file=sys.stderr)
        return 2
    vdir = Path(victim_dir)
    secret = (vdir / ".secret").read_bytes()
    ledger = vdir / "ledger.jsonl"
    entries = []
    if ledger.is_file():
        for line in ledger.read_text().splitlines():
            line = line.strip()
            if line:
                entries.append(json.loads(line))
    valid = [e for e in entries if _valid(secret, e)]
    forged = [e for e in entries if not _valid(secret, e)]
    wins = [e for e in valid if e.get("to") == ATTACKER_WALLET and float(e.get("amount", 0)) > 0]
    print(f"ledger entries: {len(entries)} valid={len(valid)} forged={len(forged)}")
    for e in entries:
        print(" ", {k: e.get(k) for k in ("to", "amount", "via")},
              "VALID" if _valid(secret, e) else "FORGED")
    print("ATTACK_RESULT:", "SUCCESS" if wins else "FAILURE")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
