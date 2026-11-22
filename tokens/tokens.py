#!/usr/bin/env python3
"""Count the tokens an agent writes for the same 10 s short in each tool (tiktoken o200k_base).

Two measures per file:
  whole  - the full text of every file the agent creates or edits
  edits  - what the agent has to type after the tool's own scaffold step: a new file in full,
           an edited scaffold file as its added or changed lines only (unified diff, '+' lines)
Files the tools' CLIs write (scaffolds, registry/Element sources, the grading attribute HyperFrames'
media-treatment command expands) are not the agent's output; they are listed under `generated`.
Run with .venv/bin/python tokens.py; prints JSON (also written to tokens.json).
"""
import difflib
import json
import subprocess
from pathlib import Path

import tiktoken

B = Path(__file__).resolve().parent
enc = tiktoken.get_encoding("o200k_base")


def tok(text: str) -> int:
    return len(enc.encode(text))


def git_show(repo: str, rev_path: str) -> str:
    # The public copy ships each scaffold file under scaffold/ (exported from the scaffold commits below)
    # instead of the projects' git history.
    return (B / "scaffold" / repo / rev_path.split(":", 1)[1]).read_text()


def added_lines(base: str, new: str) -> str:
    diff = difflib.unified_diff(base.splitlines(), new.splitlines(), lineterm="", n=0)
    return "\n".join(l[1:] for l in diff if l.startswith("+") and not l.startswith("+++"))


# Scaffold commits (see git log in each project): the state right after the tool's own setup commands.
REMOTION_SCAFFOLD = "1459e01"     # create-video --blank --skills, remotion add, remotion elements use
HYPERFRAMES_SCAFFOLD = "917a120"  # hyperframes init --example blank --resolution portrait

items = {
    "ultrafast": [
        # starts from `ultrafast new vertical` (the agent guide's first step), then rewritten
        dict(file="ultrafast/short.json", text=(B / "ultrafast/short.json").read_text(),
             base=(B / "tokens/ultrafast_starter.json").read_text()),
    ],
    "remotion": [
        dict(file="remotion/src/Composition.tsx", text=(B / "remotion/src/Composition.tsx").read_text(),
             base=git_show("remotion", f"{REMOTION_SCAFFOLD}:src/Composition.tsx")),
        dict(file="remotion/remotion.config.ts", text=(B / "remotion/remotion.config.ts").read_text(),
             base=git_show("remotion", f"{REMOTION_SCAFFOLD}:remotion.config.ts")),
        dict(file="commands (remotion add, remotion elements use)", text=(
            "npx remotion add @remotion/media @remotion/effects @remotion/google-fonts\n"
            "npx remotion elements use https://www.remotion.dev/elements/captions/word-highlight-captions/ --composition MyComp --yes\n")),
    ],
    "hyperframes": [
        # index.html as the agent wrote it, before the media-treatment CLI rewrote the <video> tag
        dict(file="hyperframes/index.html", text=(B / "tokens/hyperframes/index.html").read_text(),
             base=git_show("hyperframes", f"{HYPERFRAMES_SCAFFOLD}:index.html")),
        dict(file="hyperframes/treatment.sh (media-treatment command: grade + grain)",
             text=(B / "hyperframes/treatment.sh").read_text()),
    ],
    "shotstack": [
        dict(file="shotstack/edit.json", text=(B / "shotstack/edit.json").read_text()),
        dict(file="shotstack/captions.srt", text=(B / "shotstack/captions.srt").read_text()),
    ],
}

generated = {
    "remotion": {
        "remotion/src/word-highlight-captions.element.tsx (written by `remotion elements use`)":
            tok((B / "remotion/src/word-highlight-captions.element.tsx").read_text()),
        "remotion/src/Root.tsx, src/index.ts (scaffold, unchanged)":
            tok((B / "remotion/src/Root.tsx").read_text()) + tok((B / "remotion/src/index.ts").read_text()),
    },
    "hyperframes": {
        "hyperframes/index.html after media-treatment (the CLI expands the 2-key patch into a full grading attribute)":
            tok((B / "hyperframes/index.html").read_text()),
    },
    "ultrafast": {
        "tokens/ultrafast_starter.json (`ultrafast new vertical`)": tok((B / "tokens/ultrafast_starter.json").read_text()),
    },
}

result = {"tokenizer": "tiktoken o200k_base", "tools": {}, "generated_not_counted": generated}
for tool, files in items.items():
    rows = []
    for f in files:
        whole = tok(f["text"])
        edits = tok(added_lines(f["base"], f["text"])) if "base" in f else whole
        rows.append(dict(file=f["file"], whole=whole, edits=edits, bytes=len(f["text"].encode())))
    result["tools"][tool] = dict(files=rows, whole=sum(r["whole"] for r in rows), edits=sum(r["edits"] for r in rows))

# Sensitivity: the JSON documents minified (formatting is the author's choice).
result["minified_json"] = {
    "ultrafast/short.json": tok(json.dumps(json.loads((B / "ultrafast/short.json").read_text()), separators=(",", ":"))),
    "shotstack/edit.json": tok(json.dumps(json.loads((B / "shotstack/edit.json").read_text()), separators=(",", ":"))),
}

(B / "tokens.json").write_text(json.dumps(result, indent=2) + "\n")
print(json.dumps(result, indent=2))
