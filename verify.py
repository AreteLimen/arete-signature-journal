"""Recompute the public signature journal chain from scratch, using only the standard library.

Why standalone: a counterpart must be able to check the head without trusting the author's code.
"""
import hashlib
import json
import sys
import unicodedata


def canon(text: str) -> str:
    # "nfc-lf-trim": the same text must hash the same regardless of how a client normalised it.
    return unicodedata.normalize("NFC", text).replace("\r\n", "\n").replace("\r", "\n").strip()


def text_sha256(text: str) -> str:
    return hashlib.sha256(canon(text).encode("utf-8")).hexdigest()


def entry_hash(entry: dict) -> str:
    # The hash covers every field except itself, so any edit of an earlier line breaks every later prev.
    body = {k: v for k, v in entry.items() if k != "hash"}
    return hashlib.sha256(json.dumps(body, ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()


def verify(path: str) -> dict:
    previous, problems, count = "GENESIS", [], 0
    with open(path, encoding="utf-8") as stream:
        for index, line in enumerate(stream):
            count += 1
            entry = json.loads(line)
            if entry.get("seq") != index:
                problems.append(f"line {index}: seq mismatch")
            if entry.get("prev") != previous:
                problems.append(f"line {index}: prev mismatch")
            if entry.get("hash") != entry_hash(entry):
                problems.append(f"line {index}: hash mismatch")
            previous = entry.get("hash")
    return {"entries": count, "head": previous, "problems": problems}


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "text":
        # Usage: python3 verify.py text < message.txt  — prints text_sha256 to match against the journal.
        print(text_sha256(sys.stdin.read()))
    else:
        result = verify(sys.argv[1] if len(sys.argv) > 1 else "journal_b.jsonl")
        print(json.dumps(result, ensure_ascii=False))
        sys.exit(1 if result["problems"] else 0)
