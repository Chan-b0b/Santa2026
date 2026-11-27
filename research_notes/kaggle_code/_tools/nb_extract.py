"""Extract cell sources (and optionally short text outputs) from a .ipynb as plain text.

Read-only: parses JSON, never executes anything from the notebook.
Usage: .venv/bin/python -I nb_extract.py <out_dir> <notebook.ipynb> [...]
Writes <out_dir>/<folder>.src.txt  (markdown + code, with line numbers per cell)
       <out_dir>/<folder>.out.txt  (text outputs, each truncated to head/tail lines)
"""
import json
import os
import sys

HEAD, TAIL = 40, 40


def text_of(x):
    return ''.join(x) if isinstance(x, list) else (x or '')


def main():
    out = sys.argv[1]
    os.makedirs(out, exist_ok=True)
    for p in sys.argv[2:]:
        with open(p, encoding='utf-8') as f:
            nb = json.load(f)
        name = os.path.basename(os.path.dirname(os.path.abspath(p)))
        src, outs = [], []
        for i, c in enumerate(nb.get('cells', [])):
            s = text_of(c.get('source', ''))
            ct = c.get('cell_type')
            src.append(f"\n#### CELL {i} [{ct}] ({len(s.splitlines())} lines)\n")
            for j, line in enumerate(s.splitlines(), 1):
                src.append(f"{j:5d}| {line}\n")
            for o in c.get('outputs', []) or []:
                t = ''
                if o.get('output_type') == 'stream':
                    t = text_of(o.get('text'))
                elif o.get('output_type') in ('execute_result', 'display_data'):
                    t = text_of(o.get('data', {}).get('text/plain', ''))
                elif o.get('output_type') == 'error':
                    t = o.get('ename', '') + ': ' + o.get('evalue', '')
                if not t:
                    continue
                lines = t.splitlines()
                if len(lines) > HEAD + TAIL:
                    lines = lines[:HEAD] + [f'... [{len(lines) - HEAD - TAIL} lines cut] ...'] + lines[-TAIL:]
                lines = [ln if len(ln) <= 400 else ln[:400] + ' ...[cut]' for ln in lines]
                outs.append(f"\n#### OUTPUT of CELL {i} ({o.get('output_type')})\n" + '\n'.join(lines) + '\n')
        with open(os.path.join(out, name + '.src.txt'), 'w', encoding='utf-8') as f:
            f.write(''.join(src))
        with open(os.path.join(out, name + '.out.txt'), 'w', encoding='utf-8') as f:
            f.write(''.join(outs))
        print(name, len(nb.get('cells', [])), 'cells')


if __name__ == '__main__':
    main()
