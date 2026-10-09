#!/usr/bin/env python3
"""
Lint Positive / Negative callouts in codelab Markdown before running claat.

apply_devsite_theme.py turns a paragraph that starts with "Positive :" / "Negative :"
into a styled callout, but only that one paragraph. claat splits a callout into
several paragraphs in these cases, so the rest spills out of the box:

  1. bold text that contains inline code, e.g. **看 `http_req_duration`**
  2. more than one ": " line in the same callout
  3. a callout whose text starts with a list marker, e.g. ": 1. ..."

Usage: python3 lint_callouts.py tutorials/*.md   (exit 1 if any problem is found)
"""
import re
import sys


def lint(path):
    problems = []
    lines = open(path, encoding="utf-8").read().split("\n")
    in_fence = False
    for i, line in enumerate(lines):
        if line.startswith("```"):
            in_fence = not in_fence
        if in_fence or line.strip() not in ("Positive", "Negative"):
            continue
        j = i + 1
        body = []
        while j < len(lines) and lines[j].startswith(": "):
            body.append((j + 1, lines[j]))
            j += 1
        if not body:
            continue
        if len(body) > 1:
            problems.append((body[1][0], "callout has more than one ': ' line; merge it into one paragraph"))
        for n, text in body:
            if re.match(r": \s*\d+\.\s", text):
                problems.append((n, "callout text starts with a list marker"))
            segs = text.split("**")
            for k in range(1, len(segs), 2):
                if "`" in segs[k]:
                    problems.append((n, f"bold text contains inline code: **{segs[k][:50]}**; move the code outside the bold"))
    return problems


def main(paths):
    failed = False
    for path in paths:
        for n, msg in lint(path):
            failed = True
            print(f"{path}:{n}: {msg}")
    if failed:
        sys.exit(1)
    print(f"callouts OK ({len(paths)} file(s))")


if __name__ == "__main__":
    main(sys.argv[1:])
