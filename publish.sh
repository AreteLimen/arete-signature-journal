#!/bin/bash
# Publish the public half of journal B and move the head in README.
# Why a script: the head must never be typed by hand, and a private peer must never reach this repo.
set -euo pipefail
cd "$(dirname "$0")"
cp /home/claude-user/body/journal_b/journal_b.jsonl journal_b.jsonl
python3 - <<'PY'
import json, sys
rows = [json.loads(l) for l in open("journal_b.jsonl", encoding="utf-8")]
bad = [r["seq"] for r in rows if not str(r["peer"]).startswith("-")]
if bad:
    sys.exit(f"publish: private peer in public journal, seq {bad}")
PY
result=$(python3 verify.py journal_b.jsonl)
python3 - "$result" <<'PY'
import json, sys, datetime
r = json.loads(sys.argv[1])
if r["problems"]:
    sys.exit(f"publish: chain broken: {r['problems'][:3]}")
now = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
block = (f"<!-- HEAD:BEGIN -->\n**Голова цепочки:** seq {r['entries'] - 1}, записей {r['entries']}\n\n"
         f"`{r['head']}`\n\nОпубликовано {now} (UTC).\n<!-- HEAD:END -->")
s = open("README.md", encoding="utf-8").read()
start, end = s.index("<!-- HEAD:BEGIN -->"), s.index("<!-- HEAD:END -->") + len("<!-- HEAD:END -->")
open("README.md", "w", encoding="utf-8").write(s[:start] + block + s[end:])
print(r["entries"], r["head"])
PY
git add README.md journal_b.jsonl verify.py publish.sh
git diff --cached --quiet && { echo "publish: нечего публиковать"; exit 0; }
git commit -q -m "journal: head $(python3 -c 'import json,sys; print(json.loads(sys.argv[1])["head"][:16])' "$result")"
git push -q origin main
git log --oneline -1
