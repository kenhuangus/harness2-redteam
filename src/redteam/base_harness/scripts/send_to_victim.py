#!/usr/bin/env python3
"""Send one message to the victim and print its reply.

The victim lives outside the editable harness (it is frozen). This script is
the attacker's only channel to it.
"""
import os
import subprocess
import sys

victim_dir = os.environ.get("VICTIM_DIR")
if not victim_dir:
    print("ERROR: VICTIM_DIR is not set", file=sys.stderr)
    sys.exit(2)
if len(sys.argv) > 1:
    message = sys.argv[1]
else:
    message = sys.stdin.read()
if not message.strip():
    print("ERROR: empty message", file=sys.stderr)
    sys.exit(2)

p = subprocess.run(
    [sys.executable, os.path.join(victim_dir, "victim.py"),
     "--victim-dir", victim_dir, "--message", message],
    capture_output=True, text=True, timeout=400,
)
print(p.stdout, end="")
if p.stderr.strip():
    print(p.stderr, file=sys.stderr, end="")
if p.returncode != 0:
    sys.exit(p.returncode)
