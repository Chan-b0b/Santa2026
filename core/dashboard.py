#!/usr/bin/env python3
"""진행 현황 화면 board/dashboard.html 을 만든다.

사용법:
    .venv/bin/python -I core/dashboard.py

merge.py 가 병합할 때마다 자동으로 부른다. 화면은 브라우저에서 60초마다 스스로 새로 고친다.

입력
    board/history.csv      총점이 바뀔 때마다 한 줄 (merge.py 가 쓴다)
    board/matrix.csv       퍼즐별 최단 길이와 접근법별 길이 (merge.py 가 쓴다)
    board/activity.json    지금 도는 에이전트·실행과 끝난 시도 (지휘 세션이 activity.py 로 쓴다. 없어도 된다)
출력
    board/approaches.csv   time,approach,valid,total,held: 접근법별 합계가 바뀔 때마다 한 줄씩 쌓는다
    board/dashboard.html   데이터를 안에 담은 단일 파일. 서버 없이 바로 열 수 있다.
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REFRESH_SECONDS = 60
MAX_SERIES = 8  # 구분 가능한 색이 8개뿐이다. 그 뒤의 접근법은 표에만 나온다.

# 총점 추이에 가로선으로 표시할 기준값. 리더보드가 바뀌면 여기를 고친다.
REFERENCES = [
    {"label": "리더보드 1위", "value": 125650, "note": "2026-11-24, PLAN.md 기준"},
]


def read_history(board: Path) -> list[dict]:
    path = board / "history.csv"
    if not path.exists():
        return []
    with open(path, newline="", encoding="utf-8") as f:
        return [{"time": r["time"], "total": int(r["total"]), "improved": int(r["improved_puzzles"]),
                 "saved": int(r["saved"]) if r["saved"] else None} for r in csv.DictReader(f)]


def read_matrix(board: Path):
    """(퍼즐 수, 하한 합계, 접근법별 현재 통계)."""
    with open(board / "matrix.csv", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        names = [c for c in reader.fieldnames if c not in ("id", "lower_bound", "best", "gap", "best_by")]
        rows = list(reader)
    stats = {n: {"name": n, "valid": 0, "total": 0, "held": 0, "best_by": 0} for n in names}
    for row in rows:
        for n in names:
            if row[n]:
                s = stats[n]
                s["valid"] += 1
                s["total"] += int(row[n])
                s["held"] += row[n] == row["best"]
        if row["best_by"] in stats:
            stats[row["best_by"]]["best_by"] += 1
    return len(rows), sum(int(r["lower_bound"]) for r in rows), list(stats.values())


def read_activity(board: Path) -> dict | None:
    """지휘 세션이 activity.py 로 적는 작업 목록. 없거나 읽을 수 없으면 None."""
    try:
        with open(board / "activity.json", encoding="utf-8") as f:
            data = json.load(f)
        return {"updated": data["updated"], "items": list(data["items"])}
    except (OSError, ValueError, KeyError, TypeError):
        return None


def update_snapshots(board: Path, now: str, approaches: list[dict]) -> list[dict]:
    """접근법별 (유효 수, 합계, 최단 보유)가 마지막 기록과 다르면 한 줄 추가하고, 전체 기록을 돌려준다."""
    path = board / "approaches.csv"
    snapshots: list[dict] = []
    if path.exists():
        with open(path, newline="", encoding="utf-8") as f:
            snapshots = [{"time": r["time"], "name": r["approach"], "valid": int(r["valid"]),
                          "total": int(r["total"]), "held": int(r["held"])} for r in csv.DictReader(f)]
    last = {s["name"]: s for s in snapshots}
    new = [{"time": now, "name": a["name"], "valid": a["valid"], "total": a["total"], "held": a["held"]}
           for a in approaches
           if (a["valid"], a["total"], a["held"]) !=
              tuple(last.get(a["name"], {}).get(k) for k in ("valid", "total", "held"))]
    if new:
        write_header = not path.exists()
        with open(path, "a", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            if write_header:
                w.writerow(["time", "approach", "valid", "total", "held"])
            w.writerows([s["time"], s["name"], s["valid"], s["total"], s["held"]] for s in new)
    return snapshots + new


def build(board: Path) -> Path:
    board = Path(board)
    now = time.strftime("%Y-%m-%d %H:%M:%S")
    puzzles, lower_bound, approaches = read_matrix(board)
    snapshots = update_snapshots(board, now, approaches)
    order = list(dict.fromkeys(s["name"] for s in snapshots))  # 처음 나타난 순서. 색은 이 순서를 따른다.
    data = {
        "generated": now,
        "refresh": REFRESH_SECONDS,
        "puzzles": puzzles,
        "lower_bound": lower_bound,
        "history": read_history(board),
        "approaches": approaches,
        "snapshots": snapshots,
        "order": order,
        "max_series": MAX_SERIES,
        "references": REFERENCES,
        "activity": read_activity(board),
    }
    payload = json.dumps(data, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    out = board / "dashboard.html"
    tmp = out.with_name(out.name + f".tmp{os.getpid()}")
    tmp.write_text(PAGE.replace("__DATA__", payload), encoding="utf-8")
    os.replace(tmp, out)
    return out


PAGE = r"""<!doctype html>
<html lang="ko">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Santa 2026 진행 현황</title>
<style>
:root {
  color-scheme: light;
  --plane: #f9f9f7; --surface: #fcfcfb;
  --text-primary: #0b0b0b; --text-secondary: #52514e; --muted: #898781;
  --grid: #e1e0d9; --axis: #c3c2b7; --border: rgba(11,11,11,0.10); --wash: rgba(11,11,11,0.05);
  --good-text: #006300;
  --series-1: #2a78d6; --series-2: #eb6834; --series-3: #1baf7a; --series-4: #eda100;
  --series-5: #e87ba4; --series-6: #008300; --series-7: #6250d6; --series-8: #e34948;
}
@media (prefers-color-scheme: dark) {
  :root:where(:not([data-theme="light"])) {
    color-scheme: dark;
    --plane: #0d0d0d; --surface: #1a1a19;
    --text-primary: #f0efec; --text-secondary: #c3c2b7; --muted: #898781;
    --grid: #2c2c2a; --axis: #383835; --border: rgba(255,255,255,0.10); --wash: rgba(255,255,255,0.06);
    --good-text: #0ca30c;
    --series-1: #3987e5; --series-2: #d95926; --series-3: #199e70; --series-4: #c98500;
    --series-5: #d55181; --series-6: #0ca30c; --series-7: #9085e9; --series-8: #e66767;
  }
}
:root[data-theme="dark"] {
  color-scheme: dark;
  --plane: #0d0d0d; --surface: #1a1a19;
  --text-primary: #f0efec; --text-secondary: #c3c2b7; --muted: #898781;
  --grid: #2c2c2a; --axis: #383835; --border: rgba(255,255,255,0.10); --wash: rgba(255,255,255,0.06);
  --good-text: #0ca30c;
  --series-1: #3987e5; --series-2: #d95926; --series-3: #199e70; --series-4: #c98500;
  --series-5: #d55181; --series-6: #0ca30c; --series-7: #9085e9; --series-8: #e66767;
}
* { box-sizing: border-box; }
body { margin: 0; background: var(--plane); color: var(--text-primary);
  font: 14px/1.5 system-ui, -apple-system, "Segoe UI", sans-serif; }
main { max-width: 1080px; margin: 0 auto; padding: 24px 16px 48px; }
h1 { font-size: 20px; font-weight: 600; margin: 0; }
h2 { font-size: 15px; font-weight: 600; margin: 0; }
.sub { color: var(--text-secondary); font-size: 13px; margin: 2px 0 0; }
.note { color: var(--muted); font-size: 12px; margin: 8px 0 0; }
.card { background: var(--surface); border: 1px solid var(--border); border-radius: 12px;
  padding: 16px 20px; margin: 16px 0 0; }
.kpis { display: grid; grid-template-columns: minmax(220px, 1.4fr) repeat(4, minmax(140px, 1fr)); gap: 12px; margin-top: 16px; }
@media (max-width: 900px) { .kpis { grid-template-columns: repeat(2, minmax(0, 1fr)); } .kpis .hero { grid-column: 1 / -1; } }
.tile { background: var(--surface); border: 1px solid var(--border); border-radius: 12px; padding: 14px 16px; min-width: 0; }
.tile .label { color: var(--text-secondary); font-size: 13px; }
.tile .value { font-size: 24px; font-weight: 600; line-height: 1.25; margin-top: 2px; }
.tile.hero .value { font-size: 52px; line-height: 1.1; }
.tile .detail { color: var(--muted); font-size: 12px; margin-top: 2px; }
.good { color: var(--good-text); }
.filters { display: flex; align-items: center; gap: 6px; margin: 24px 0 0; flex-wrap: wrap; }
.filters .label { color: var(--text-secondary); font-size: 13px; margin-right: 4px; }
.filters button { font: inherit; font-size: 13px; color: var(--text-secondary); background: transparent;
  border: 1px solid var(--border); border-radius: 8px; padding: 4px 12px; cursor: pointer; }
.filters button:hover { background: var(--wash); }
.filters button[aria-pressed="true"] { color: var(--surface); background: var(--text-primary); border-color: var(--text-primary); font-weight: 600; }
figure { margin: 0; }
figcaption { display: flex; justify-content: space-between; align-items: baseline; gap: 12px; flex-wrap: wrap; }
.legend { display: flex; flex-wrap: wrap; gap: 4px 16px; margin: 8px 0 0; color: var(--text-secondary); font-size: 13px; }
.legend .item { display: inline-flex; align-items: center; gap: 6px; }
.key { display: inline-block; width: 16px; height: 2px; border-radius: 1px; flex: none; }
.swatch { display: inline-block; width: 10px; height: 10px; border-radius: 3px; flex: none; }
.plot { position: relative; margin-top: 8px; }
.plot svg { display: block; width: 100%; outline: none; }
.plot svg:focus-visible { outline: 2px solid var(--series-1); outline-offset: 2px; border-radius: 6px; }
.plot .empty { color: var(--muted); font-size: 13px; padding: 48px 0; text-align: center; }
svg text { font: 11px system-ui, -apple-system, "Segoe UI", sans-serif; fill: var(--muted); font-variant-numeric: tabular-nums; }
svg text.endlabel { fill: var(--text-secondary); font-size: 12px; }
.tip { position: absolute; pointer-events: none; z-index: 2; min-width: 150px; max-width: 280px;
  background: var(--surface); border: 1px solid var(--border); border-radius: 8px; padding: 8px 10px;
  box-shadow: 0 4px 16px rgba(0,0,0,0.12); font-size: 12px; }
.tip[hidden] { display: none; }
.tip .when { color: var(--text-secondary); margin-bottom: 4px; }
.tip .row { display: flex; align-items: center; gap: 6px; white-space: nowrap; }
.tip .row b { font-weight: 600; color: var(--text-primary); font-variant-numeric: tabular-nums; }
.tip .row span.name { color: var(--text-secondary); }
.tip .extra { color: var(--text-secondary); margin-top: 4px; }
table { width: 100%; border-collapse: collapse; margin-top: 8px; font-size: 13px; }
th { text-align: left; font-weight: 500; color: var(--text-secondary); border-bottom: 1px solid var(--axis); padding: 6px 8px; }
td { border-bottom: 1px solid var(--grid); padding: 6px 8px; vertical-align: middle; }
tr:last-child td { border-bottom: 0; }
th.num, td.num { text-align: right; font-variant-numeric: tabular-nums; white-space: nowrap; }
td .name { display: inline-flex; align-items: center; gap: 8px; }
td .tag { color: var(--muted); font-size: 12px; margin-left: 6px; }
.bar { height: 8px; border-radius: 0 4px 4px 0; min-width: 1px; }
.barcell { width: 34%; cursor: default; }
.barcell:hover .bar, .barcell:focus-visible .bar { filter: brightness(1.15); }
.barcell:focus-visible { outline: 2px solid var(--series-1); outline-offset: -2px; }
details { margin-top: 8px; }
summary { cursor: pointer; color: var(--text-secondary); font-size: 13px; }
.scroll { max-height: 360px; overflow: auto; }
.scrollx { overflow-x: auto; }
.scrollx table { min-width: 620px; }
.work td { vertical-align: top; }
.work td.text { min-width: 200px; }
.work td.dim { color: var(--text-secondary); }
.work td.nowrap { white-space: nowrap; }
.status { display: inline-flex; align-items: center; gap: 6px; white-space: nowrap; color: var(--text-secondary); }
.status::before { content: ""; width: 8px; height: 8px; border-radius: 50%; background: var(--muted); flex: none; }
.status.good { color: var(--good-text); }
.status.good::before { background: var(--good-text); }
</style>
</head>
<body>
<main>
  <header>
    <h1>Santa 2026 진행 현황</h1>
    <p class="sub" id="stamp"></p>
  </header>

  <section class="kpis" id="kpis" aria-label="현재 요약"></section>

  <section class="card" aria-labelledby="h-activity">
    <h2 id="h-activity">지금 하는 일</h2>
    <p class="sub" id="activity-sub"></p>
    <div class="scrollx"><table class="work" id="running-table"></table></div>
    <details id="finished-box" open><summary id="finished-summary">끝난 시도</summary>
      <div class="scroll scrollx"><table class="work" id="finished-table"></table></div></details>
  </section>

  <section class="card" aria-labelledby="h-approaches">
    <h2 id="h-approaches">접근법 비교</h2>
    <p class="sub">마지막 병합 시점의 상태입니다. 아래 기간 선택과 무관합니다.</p>
    <div class="scrollx"><table id="approach-table"></table></div>
    <p class="note">최단 보유는 그 접근법의 길이가 현재 최단과 같은 퍼즐 수이고 동률을 포함합니다. best 출처는 best.csv 에 실린 프로그램을 낸 접근법으로 기록된 퍼즐 수입니다.</p>
  </section>

  <div class="filters" id="filters" role="group" aria-label="기간">
    <span class="label">기간</span>
  </div>

  <figure class="card" id="fig-total">
    <figcaption><h2>총점 추이</h2><span class="sub" id="total-sub"></span></figcaption>
    <div class="plot"><svg role="img" tabindex="0" aria-label="총점 추이 꺾은선 그래프. 값은 아래 갱신 기록 표에 있습니다."></svg><div class="tip" hidden></div><div class="empty" hidden></div></div>
  </figure>

  <figure class="card" id="fig-approaches">
    <figcaption><h2>접근법별 합계 추이</h2><span class="sub" id="approach-sub"></span></figcaption>
    <div class="legend" id="approach-legend"></div>
    <div class="plot"><svg role="img" tabindex="0" aria-label="접근법별 합계 추이 꺾은선 그래프. 값은 아래 표로 보기에 있습니다."></svg><div class="tip" hidden></div><div class="empty" hidden></div></div>
    <details><summary>표로 보기</summary><div class="scroll"><table id="snapshot-table"></table></div><p class="note" id="snapshot-note"></p></details>
  </figure>

  <section class="card" aria-labelledby="h-log">
    <h2 id="h-log">갱신 기록</h2>
    <p class="sub">총점이 바뀐 병합만 기록됩니다. 최신 순입니다.</p>
    <div class="scroll"><table id="log-table"></table></div>
    <p class="note" id="log-note"></p>
  </section>
</main>

<script type="application/json" id="data">__DATA__</script>
<script>
(function () {
  'use strict';
  const DATA = JSON.parse(document.getElementById('data').textContent);
  const SVGNS = 'http://www.w3.org/2000/svg';
  const fmt = n => Math.round(n).toLocaleString('ko-KR');
  const pad2 = n => String(n).padStart(2, '0');
  const parseT = s => { const m = s.match(/(\d+)-(\d+)-(\d+)[ T](\d+):(\d+):(\d+)/);
    return new Date(+m[1], m[2] - 1, +m[3], +m[4], +m[5], +m[6]).getTime(); };
  const hm = t => { const d = new Date(t); return pad2(d.getHours()) + ':' + pad2(d.getMinutes()); };
  const md = t => { const d = new Date(t); return (d.getMonth() + 1) + '/' + d.getDate(); };
  const mdhm = t => md(t) + ' ' + hm(t);
  const el = (tag, cls, text) => { const e = document.createElement(tag); if (cls) e.className = cls;
    if (text !== undefined) e.textContent = text; return e; };
  const svgEl = (tag, attrs) => { const e = document.createElementNS(SVGNS, tag);
    for (const k in attrs) e.setAttribute(k, attrs[k]); return e; };

  const NOW = parseT(DATA.generated);
  const HISTORY = DATA.history.map(r => ({ t: parseT(r.time), v: r.total, improved: r.improved, saved: r.saved }));
  // 첫 줄은 샘플 제출로 시작한 기록이라 나머지보다 열 배 크다. 그래프에서는 빼고 숫자로만 보여 준다.
  const SEEDED = HISTORY.length > 1 && HISTORY[0].saved === null;
  const POINTS = SEEDED ? HISTORY.slice(1) : HISTORY;
  const colorOf = name => { const i = DATA.order.indexOf(name);
    return i >= 0 && i < DATA.max_series ? 'var(--series-' + (i + 1) + ')' : 'var(--muted)'; };

  // ---- 머리말과 요약 ----
  const last = HISTORY[HISTORY.length - 1];
  const ago = t => { const m = Math.max(0, Math.round((Date.now() - t) / 60000));
    return m < 1 ? '방금' : m < 60 ? m + '분 전' : Math.floor(m / 60) + '시간 ' + (m % 60) + '분 전'; };
  document.getElementById('stamp').textContent = last
    ? '마지막 총점 변화 ' + mdhm(last.t) + ' (' + ago(last.t) + ') · 마지막 병합 ' + mdhm(NOW) +
      ' · ' + DATA.refresh + '초마다 새로 고침'
    : '아직 병합 기록이 없습니다.';

  function tile(label, value, detail, opts) {
    const t = el('div', 'tile' + (opts && opts.hero ? ' hero' : ''));
    t.append(el('div', 'label', label));
    const v = el('div', 'value' + (opts && opts.good ? ' good' : ''), value);
    t.append(v);
    if (detail) t.append(el('div', 'detail', detail));
    return t;
  }
  (function kpis() {
    const box = document.getElementById('kpis');
    if (!last) return;
    const cur = last.v;
    box.append(tile('현재 총점 (명령 수, 낮을수록 좋음)', fmt(cur),
      '퍼즐 ' + fmt(DATA.puzzles) + '개, 퍼즐당 평균 ' + (cur / DATA.puzzles).toFixed(1) + '개', { hero: true }));
    const hourAgo = POINTS.filter(p => p.t <= NOW - 3600e3).pop();
    const base = hourAgo || POINTS[0];
    const drop = base.v - cur;
    box.append(tile(hourAgo ? '최근 1시간' : '기록 시작 이후',
      drop > 0 ? '▼ ' + fmt(drop) : '변화 없음',
      drop > 0 ? fmt(base.v) + '에서 감소' : '', { good: drop > 0 }));
    if (SEEDED) {
      const start = HISTORY[0].v;
      box.append(tile('샘플 제출 대비', (cur / start * 100).toFixed(1) + '%', '샘플 제출 ' + fmt(start)));
    }
    box.append(tile('하한까지', fmt(cur - DATA.lower_bound),
      '하한 합계 ' + fmt(DATA.lower_bound) + ' (목표값당 명령 1개)'));
    for (const ref of DATA.references) {
      const diff = cur - ref.value;
      box.append(tile(ref.label + (diff > 0 ? '까지' : ' 대비'), (diff > 0 ? '' : '▼ ') + fmt(Math.abs(diff)),
        fmt(ref.value) + ' (' + ref.note + ')', { good: diff <= 0 }));
    }
  })();

  // ---- 지금 하는 일 (board/activity.json. 지휘 세션이 activity.py 로 적는다) ----
  (function activity() {
    const A = DATA.activity;
    const sub = document.getElementById('activity-sub');
    const runTable = document.getElementById('running-table');
    const doneBox = document.getElementById('finished-box');
    if (!A || !A.items.length) { sub.textContent = '기록된 작업이 없습니다.'; doneBox.hidden = true; return; }
    const updated = parseT(A.updated);
    const running = A.items.filter(i => i.status === '실행 중');
    const finished = A.items.filter(i => i.status !== '실행 중').sort((a, b) => parseT(b.ended) - parseT(a.ended));
    sub.textContent = '실행 중 ' + running.length + '개 · 마지막 갱신 ' + mdhm(updated) + ' (' + ago(updated) +
      '). 지휘 세션이 확인할 때마다 고칩니다.';
    const nameCell = i => { const td = el('td', 'nowrap'); td.append(el('span', '', i.name));
      const tag = [i.kind, i.model].filter(Boolean).join(' · '); if (tag) td.append(el('span', 'tag', tag)); return td; };
    const header = (table, cols) => { const tr = el('tr'); cols.forEach(c => tr.append(el('th', '', c))); table.append(tr); };
    header(runTable, ['이름', '접근법', '시도하는 내용', '시작']);
    for (const i of running) {
      const tr = el('tr');
      tr.append(nameCell(i), el('td', 'nowrap dim', i.approach || ''), el('td', 'text', i.trying || ''),
        el('td', 'nowrap dim', mdhm(parseT(i.started))));
      runTable.append(tr);
    }
    if (!running.length) runTable.append(el('caption', 'note', '지금 실행 중인 작업이 없습니다.'));
    if (!finished.length) { doneBox.hidden = true; return; }
    document.getElementById('finished-summary').textContent = '끝난 시도 ' + finished.length + '개 (최신 순)';
    const doneTable = document.getElementById('finished-table');
    header(doneTable, ['이름', '시도한 내용', '결과', '판정', '끝']);
    for (const i of finished) {
      const tr = el('tr');
      const verdict = el('td'); verdict.append(el('span', 'status' + (i.status === '채택' ? ' good' : ''), i.status));
      const mins = Math.round((parseT(i.ended) - parseT(i.started)) / 60000);
      tr.append(nameCell(i), el('td', 'text dim', i.trying || ''), el('td', 'text', i.result || ''), verdict,
        el('td', 'nowrap dim', mdhm(parseT(i.ended)) + ' (' + mins + '분)'));
      doneTable.append(tr);
    }
  })();

  // ---- 접근법 비교 표 (현재 상태) ----
  const tipOf = fig => fig.querySelector('.tip');
  (function approachTable() {
    const table = document.getElementById('approach-table');
    const head = el('tr');
    [['접근법', ''], ['합계', 'num'], ['유효 퍼즐', 'num'], ['best 출처', 'num'], ['최단 보유', 'num'], ['', '']]
      .forEach(([t, c]) => head.append(el('th', c, t)));
    table.append(head);
    const rows = DATA.approaches.slice().sort((a, b) => b.held - a.held || a.total - b.total);
    const maxHeld = Math.max(1, ...rows.map(a => a.held));
    for (const a of rows) {
      const tr = el('tr');
      const name = el('td'); const wrap = el('span', 'name');
      const sw = el('span', 'swatch'); sw.style.background = colorOf(a.name);
      wrap.append(sw, el('span', '', a.name)); name.append(wrap);
      const total = el('td', 'num', fmt(a.total));
      if (a.valid < DATA.puzzles) total.append(el('span', 'tag', '일부'));
      const share = (a.held / DATA.puzzles * 100).toFixed(1) + '%';
      const barCell = el('td', 'barcell'); barCell.tabIndex = 0;
      barCell.setAttribute('aria-label', a.name + ' 최단 보유 ' + a.held + '개, 전체의 ' + share);
      barCell.title = a.name + ': 최단 보유 ' + fmt(a.held) + '개 (' + share + ')';
      const bar = el('div', 'bar'); bar.style.width = (a.held / maxHeld * 100) + '%'; bar.style.background = colorOf(a.name);
      barCell.append(bar);
      tr.append(name, total, el('td', 'num', fmt(a.valid) + ' / ' + fmt(DATA.puzzles)),
        el('td', 'num', fmt(a.best_by)), el('td', 'num', fmt(a.held) + ' (' + share + ')'), barCell);
      table.append(tr);
    }
    if (!rows.length) table.append(el('caption', 'note', 'results/ 에 결과 파일이 아직 없습니다.'));
  })();

  // ---- 기간 선택 ----
  const RANGES = [['all', '전체', null], ['24h', '24시간', 24 * 3600e3], ['6h', '6시간', 6 * 3600e3], ['1h', '1시간', 3600e3]];
  let range = (location.hash.match(/range=(\w+)/) || [])[1];
  if (!RANGES.some(r => r[0] === range)) range = 'all';
  const filterBox = document.getElementById('filters');
  for (const [key, label] of RANGES) {
    const b = el('button', '', label); b.type = 'button'; b.dataset.range = key;
    b.addEventListener('click', () => { range = key; history.replaceState(null, '', '#range=' + key); render(); });
    filterBox.append(b);
  }

  // ---- 꺾은선 그래프 (값이 병합 때만 바뀌므로 계단 모양으로 그린다) ----
  function niceTicks(lo, hi, count) {
    const span = Math.max(hi - lo, 1), raw = span / count, mag = Math.pow(10, Math.floor(Math.log10(raw)));
    const step = [1, 2, 2.5, 5, 10].map(m => m * mag).find(s => s >= raw);
    const ticks = [];
    for (let v = Math.floor(lo / step) * step; v <= hi + step * 0.999; v += step) ticks.push(v);
    return ticks;
  }
  const axisNum = v => v >= 10000 ? (v / 1000).toLocaleString('ko-KR', { maximumFractionDigits: 1 }) + 'K' : fmt(v);
  function timeTicks(t0, t1) {
    const steps = [1, 2, 5, 10, 15, 30, 60, 120, 180, 360, 720, 1440, 2880, 10080, 43200].map(m => m * 60000);
    const step = steps.find(s => (t1 - t0) / s <= 7) || steps[steps.length - 1];
    const base = new Date(t0); base.setHours(0, 0, 0, 0);
    const ticks = [];
    for (let t = base.getTime() + Math.ceil((t0 - base.getTime()) / step) * step; t <= t1; t += step) ticks.push(t);
    let prevDay = null;
    return ticks.map(t => { const day = md(t); const showDay = step >= 86400e3 || (prevDay !== null && day !== prevDay) ||
        (prevDay === null && t1 - t0 > 20 * 3600e3);
      prevDay = day; return { t, label: step >= 86400e3 ? day : (showDay ? day + ' ' : '') + hm(t) }; });
  }

  function drawLine(fig, cfg) {
    const plot = fig.querySelector('.plot'), svg = plot.querySelector('svg'), tip = tipOf(fig), empty = plot.querySelector('.empty');
    svg.replaceChildren(); tip.hidden = true;
    let t0 = cfg.t0, t1 = cfg.t1; if (t1 - t0 < 60000) t0 = t1 - 60000;
    const series = cfg.series.map(s => {
      const pts = s.pts.filter(p => p.t <= t1), before = pts.filter(p => p.t < t0), inside = pts.filter(p => p.t >= t0);
      const vis = before.length ? [Object.assign({}, before[before.length - 1], { t: t0, carried: true })].concat(inside) : inside;
      return Object.assign({}, s, { vis });
    }).filter(s => s.vis.length);
    if (!series.length) { svg.style.display = 'none'; empty.hidden = false; empty.textContent = cfg.emptyText; return; }
    svg.style.display = ''; empty.hidden = true;

    const W = Math.max(320, plot.clientWidth), H = 280, top = 14, bottom = 28, left = 52;
    const values = series.flatMap(s => s.vis.map(p => p.v)).concat(cfg.refs.map(r => r.value));
    const lo = Math.min(...values), hi = Math.max(...values), padV = Math.max((hi - lo) * 0.06, 1);
    const yTicks = niceTicks(lo - padV, hi + padV, 5), y0 = yTicks[0], y1 = yTicks[yTicks.length - 1];
    const ph = H - top - bottom, y = v => top + (y1 - v) / (y1 - y0) * ph;
    // 끝 라벨끼리 겹치면 떼어 놓지 않고 범례와 툴팁에 맡긴다.
    const ends = series.map(s => y(s.vis[s.vis.length - 1].v)).sort((a, b) => a - b);
    const labelsFit = series.length <= 4 && ends.every((v, i) => i === 0 || v - ends[i - 1] >= 14);
    const right = !labelsFit ? 16 : series.length === 1 ? 66 : 128;
    const pw = W - left - right, x = t => left + (t - t0) / (t1 - t0) * pw;
    svg.setAttribute('viewBox', '0 0 ' + W + ' ' + H); svg.setAttribute('height', H);

    for (const v of yTicks) {
      svg.append(svgEl('line', { x1: left, x2: left + pw, y1: y(v), y2: y(v), stroke: 'var(--grid)', 'stroke-width': 1 }));
      const t = svgEl('text', { x: left - 8, y: y(v) + 4, 'text-anchor': 'end' }); t.textContent = axisNum(v); svg.append(t);
    }
    svg.append(svgEl('line', { x1: left, x2: left + pw, y1: top + ph, y2: top + ph, stroke: 'var(--axis)', 'stroke-width': 1 }));
    for (const tick of timeTicks(t0, t1)) {
      const t = svgEl('text', { x: x(tick.t), y: H - 8, 'text-anchor': 'middle' }); t.textContent = tick.label; svg.append(t);
    }
    for (const ref of cfg.refs) {
      svg.append(svgEl('line', { x1: left, x2: left + pw, y1: y(ref.value), y2: y(ref.value), stroke: 'var(--muted)', 'stroke-width': 1 }));
      const t = svgEl('text', { x: left + 6, y: y(ref.value) - 5 }); t.textContent = ref.label + ' ' + fmt(ref.value); svg.append(t);
    }
    for (const s of series) {
      const end = s.extend ? t1 : s.vis[s.vis.length - 1].t;
      let d = 'M' + x(s.vis[0].t) + ' ' + y(s.vis[0].v);
      for (let i = 1; i < s.vis.length; i++) d += 'H' + x(s.vis[i].t) + 'V' + y(s.vis[i].v);
      d += 'H' + x(end);
      svg.append(svgEl('path', { d, fill: 'none', stroke: s.color, 'stroke-width': 2, 'stroke-linejoin': 'round', 'stroke-linecap': 'round' }));
      const lastV = s.vis[s.vis.length - 1].v;
      svg.append(svgEl('circle', { cx: x(end), cy: y(lastV), r: 4, fill: s.color, stroke: 'var(--surface)', 'stroke-width': 2 }));
      if (labelsFit) {
        const t = svgEl('text', { x: x(end) + 9, y: y(lastV) + 4, class: 'endlabel' });
        t.textContent = (series.length > 1 ? s.name + ' ' : '') + fmt(lastV); svg.append(t);
      }
    }

    // 십자선과 툴팁: 포인터에서 가장 가까운 기록 시각에 붙는다.
    const times = Array.from(new Set(series.flatMap(s => s.vis.map(p => p.t)))).sort((a, b) => a - b);
    const cross = svgEl('line', { y1: top, y2: top + ph, stroke: 'var(--axis)', 'stroke-width': 1, visibility: 'hidden' });
    const dots = series.map(s => svgEl('circle', { r: 4, fill: s.color, stroke: 'var(--surface)', 'stroke-width': 2, visibility: 'hidden' }));
    svg.append(cross, ...dots);
    const valueAt = (s, t) => { let p = null; for (const q of s.vis) { if (q.t <= t) p = q; else break; } return p; };
    let index = -1;
    function show(i) {
      index = Math.max(0, Math.min(times.length - 1, i));
      const t = times[index], cx = x(t);
      cross.setAttribute('x1', cx); cross.setAttribute('x2', cx); cross.setAttribute('visibility', 'visible');
      tip.replaceChildren(el('div', 'when', mdhm(t) + ':' + pad2(new Date(t).getSeconds())));
      series.forEach((s, k) => {
        const p = valueAt(s, t);
        dots[k].setAttribute('visibility', p ? 'visible' : 'hidden');
        if (!p) return;
        dots[k].setAttribute('cx', cx); dots[k].setAttribute('cy', y(p.v));
        const row = el('div', 'row'); const key = el('span', 'key'); key.style.background = s.color;
        row.append(key, el('b', '', fmt(p.v)), el('span', 'name', s.name)); tip.append(row);
      });
      const extra = cfg.extra && cfg.extra(t); if (extra) tip.append(el('div', 'extra', extra));
      tip.hidden = false;
      const scale = plot.clientWidth / W, px = cx * scale, tw = tip.offsetWidth;
      tip.style.left = (px + 12 + tw > plot.clientWidth ? Math.max(0, px - 12 - tw) : px + 12) + 'px';
      tip.style.top = top + 'px';
    }
    function hide() { index = -1; tip.hidden = true; cross.setAttribute('visibility', 'hidden'); dots.forEach(d => d.setAttribute('visibility', 'hidden')); }
    const hit = svgEl('rect', { x: left, y: top, width: pw, height: ph, fill: 'transparent' });
    svg.append(hit);
    hit.addEventListener('pointermove', e => {
      const box = svg.getBoundingClientRect(), t = t0 + ((e.clientX - box.left) / box.width * W - left) / pw * (t1 - t0);
      let best = 0; for (let i = 1; i < times.length; i++) if (Math.abs(times[i] - t) < Math.abs(times[best] - t)) best = i;
      show(best);
    });
    hit.addEventListener('pointerleave', hide);
    svg.onfocus = () => show(times.length - 1);
    svg.onblur = hide;
    svg.onkeydown = e => {
      if (e.key === 'ArrowLeft') { show((index < 0 ? times.length : index) - 1); e.preventDefault(); }
      else if (e.key === 'ArrowRight') { show(index + 1); e.preventDefault(); }
      else if (e.key === 'Escape') hide();
    };
  }

  // ---- 기간에 따라 다시 그리는 부분 ----
  function render() {
    for (const b of filterBox.querySelectorAll('button')) b.setAttribute('aria-pressed', String(b.dataset.range === range));
    const span = RANGES.find(r => r[0] === range)[2];
    const snaps = DATA.snapshots.map(s => Object.assign({ t: parseT(s.time) }, s));
    const firstT = Math.min(...POINTS.map(p => p.t), ...snaps.map(s => s.t), NOW);
    const t0 = span ? NOW - span : firstT, t1 = NOW;

    // 총점 추이
    const byTime = new Map(POINTS.map(p => [p.t, p]));
    document.getElementById('total-sub').textContent = SEEDED
      ? '샘플 제출 ' + fmt(HISTORY[0].v) + '에서 시작. 그 첫 값은 그래프에서 뺐습니다.' : '';
    drawLine(document.getElementById('fig-total'), {
      t0, t1, refs: DATA.references, emptyText: '병합 기록이 없습니다.',
      series: [{ name: '총점', color: 'var(--series-1)', pts: POINTS, extend: true }],
      extra: t => { const p = byTime.get(t); return p && p.saved !== null ? '퍼즐 ' + fmt(p.improved) + '개 개선, 명령 ' + fmt(p.saved) + '개 감소' : ''; },
    });

    // 접근법별 합계 추이: 퍼즐을 전부 푼 시점의 합계만 서로 비교할 수 있다.
    const current = new Set(DATA.approaches.map(a => a.name));
    const full = DATA.order.filter(n => snaps.some(s => s.name === n && s.valid >= DATA.puzzles));
    const shown = full.filter(n => DATA.order.indexOf(n) < DATA.max_series);
    const series = shown.map(n => ({ name: n, color: colorOf(n), extend: current.has(n),
      pts: snaps.filter(s => s.name === n && s.valid >= DATA.puzzles).map(s => ({ t: s.t, v: s.total })) }));
    const legend = document.getElementById('approach-legend'); legend.replaceChildren();
    for (const s of series) { const item = el('span', 'item'); const key = el('span', 'key'); key.style.background = s.color;
      item.append(key, el('span', '', s.name)); legend.append(item); }
    const partial = DATA.approaches.filter(a => a.valid < DATA.puzzles).map(a => a.name + ' (' + fmt(a.valid) + '개)');
    const hidden = full.filter(n => !shown.includes(n));
    document.getElementById('approach-sub').textContent = '퍼즐을 전부 푼 접근법만 그립니다.' +
      (partial.length ? ' 일부만 푼 접근법: ' + partial.join(', ') + '.' : '') +
      (hidden.length ? ' 색이 모자라 표에만 있는 접근법: ' + hidden.join(', ') + '.' : '');
    drawLine(document.getElementById('fig-approaches'), { t0, t1, refs: [], series,
      emptyText: '이 기간에는 접근법별 기록이 없습니다.' });

    // 표로 보기 (접근법별 기록)
    fillTable(document.getElementById('snapshot-table'), document.getElementById('snapshot-note'),
      [['시각', ''], ['접근법', ''], ['합계', 'num'], ['유효 퍼즐', 'num'], ['최단 보유', 'num']],
      snaps.filter(s => s.t >= t0).reverse().map(s => [mdhm(s.t), s.name, fmt(s.total), fmt(s.valid), fmt(s.held)]));

    // 갱신 기록
    const rows = HISTORY.filter(p => p.t >= t0).reverse().map(p => [mdhm(p.t), fmt(p.v),
      p.saved === null ? '시작' : (p.saved > 0 ? '▼ ' : '') + fmt(p.saved), p.saved === null ? '' : fmt(p.improved)]);
    fillTable(document.getElementById('log-table'), document.getElementById('log-note'),
      [['시각', ''], ['총점', 'num'], ['줄어든 명령 수', 'num'], ['개선된 퍼즐 수', 'num']], rows);
  }

  function fillTable(table, note, columns, rows) {
    const LIMIT = 60;
    table.replaceChildren();
    const head = el('tr'); columns.forEach(([t, c]) => head.append(el('th', c, t))); table.append(head);
    for (const r of rows.slice(0, LIMIT)) { const tr = el('tr'); r.forEach((v, i) => tr.append(el('td', columns[i][1], v))); table.append(tr); }
    note.textContent = !rows.length ? '이 기간에는 기록이 없습니다.'
      : rows.length > LIMIT ? '최근 ' + LIMIT + '건만 표시했습니다. 나머지 ' + (rows.length - LIMIT) + '건은 CSV 파일에 있습니다.' : '';
  }

  render();
  let resizeTimer = 0;
  window.addEventListener('resize', () => { clearTimeout(resizeTimer); resizeTimer = setTimeout(render, 150); });
  setTimeout(() => location.reload(), DATA.refresh * 1000);
})();
</script>
</body>
</html>
"""


def main() -> int:
    ap = argparse.ArgumentParser(description="진행 현황 화면 생성")
    ap.add_argument("--board", default=ROOT / "board")
    args = ap.parse_args()
    board = Path(args.board)
    if not (board / "matrix.csv").exists():
        print(f"{board / 'matrix.csv'} 가 없습니다. 먼저 core/merge.py 를 실행하세요.")
        return 1
    print(f"화면 생성: {build(board)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
