#!/usr/bin/env python3
"""진행 현황 화면의 "지금 하는 일" 표에 나오는 작업 목록 board/activity.json 을 고친다.

지휘 세션만 쓴다. 고칠 때마다 board/dashboard.html 을 다시 만든다.

사용법:
    .venv/bin/python -I core/activity.py start "lend 에이전트" --kind 에이전트 --model sonnet --approach lend --trying "..."
    .venv/bin/python -I core/activity.py start "lns run11" --kind 실행 --approach lns --trying "..."
    .venv/bin/python -I core/activity.py end "lns run11" --status 끝남 --result "..."
    .venv/bin/python -I core/activity.py drop "lns run11"
    .venv/bin/python -I core/activity.py show

start 는 같은 이름이 있으면 그 줄을 덮어쓴다. 시각은 지금으로 찍히고, --at "2026-11-25 13:17:00" 으로 직접 줄 수 있다.
판정(--status): 채택(이득이 있어 쓰기로 함), 끝남(실행이 끝남), 접음(이득이 없어 그만둠), 중단.

이 파일의 내용은 board/ 와 함께 GitHub Pages 로 공개된다. 공개해도 되는 것만 적는다.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))  # python3 -I 로 실행해도 dashboard 를 찾도록
import dashboard

ROOT = Path(__file__).resolve().parent.parent
RUNNING = "실행 중"
VERDICTS = ["채택", "끝남", "접음", "중단"]


def load(path: Path) -> dict:
    if not path.exists():
        return {"updated": "", "items": []}
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def save(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + f".tmp{os.getpid()}")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    os.replace(tmp, path)


def find(items: list[dict], name: str) -> int:
    for i, item in enumerate(items):
        if item["name"] == name:
            return i
    return -1


def main() -> int:
    ap = argparse.ArgumentParser(description='진행 현황 화면의 "지금 하는 일" 목록을 고친다')
    ap.add_argument("--board", default=ROOT / "board")
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("start", help="작업을 실행 중으로 올린다 (같은 이름은 덮어쓴다)")
    s.add_argument("name")
    s.add_argument("--kind", required=True, help="세션, 에이전트, 실행 가운데 하나")
    s.add_argument("--model", default="", help="에이전트의 모델 (sonnet, opus, haiku, fable)")
    s.add_argument("--approach", default="")
    s.add_argument("--trying", required=True, help="무엇을 시도하는지 한 줄")
    s.add_argument("--at", default="")
    e = sub.add_parser("end", help="작업을 끝난 것으로 옮긴다")
    e.add_argument("name")
    e.add_argument("--status", required=True, choices=VERDICTS)
    e.add_argument("--result", required=True, help="측정값과 판단 한 줄")
    e.add_argument("--at", default="")
    d = sub.add_parser("drop", help="목록에서 뺀다")
    d.add_argument("name")
    sub.add_parser("show", help="목록을 찍고 화면만 다시 만든다")
    args = ap.parse_args()

    board = Path(args.board)
    path = board / "activity.json"
    data = load(path)
    items = data["items"]
    now = time.strftime("%Y-%m-%d %H:%M:%S")

    if args.cmd == "start":
        item = {"name": args.name, "kind": args.kind, "model": args.model, "approach": args.approach,
                "trying": args.trying, "status": RUNNING, "started": args.at or now, "ended": "", "result": ""}
        i = find(items, args.name)
        if i >= 0:
            items[i] = item
        else:
            items.append(item)
    elif args.cmd == "end":
        i = find(items, args.name)
        if i < 0:
            print(f"없는 이름: {args.name}")
            return 1
        items[i].update(status=args.status, result=args.result, ended=args.at or now)
    elif args.cmd == "drop":
        i = find(items, args.name)
        if i < 0:
            print(f"없는 이름: {args.name}")
            return 1
        del items[i]

    if args.cmd != "show":
        data["updated"] = now
        save(path, data)
    for item in items:
        when = item["started"][5:16] + (" ~ " + item["ended"][11:16] if item["ended"] else "")
        print(f'{item["status"]:5} {item["name"]} [{when}] {item["result"] or item["trying"]}')
    print(f"화면: {dashboard.build(board)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
