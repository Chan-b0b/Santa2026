"""쓰이지 않는 명령 제거 (dead code elimination).

명령 i 가 살아 있는 경우: (a) 아직 안 나온 목표값을 처음 만드는 명령이거나,
(b) 그 결과를 살아 있는 뒤 명령이 (덮어쓰이기 전에) 읽는 경우.
죽은 명령을 빼도 살아 있는 명령이 읽는 레지스터 값은 바뀌지 않는다.
"""


def prune(puzzle, prog):
    n = len(prog)
    reg_def = {}                 # 레지스터 -> 지금 그 값을 쓴 명령 번호 (없으면 시작값)
    deps = [None] * n            # 명령 i 가 읽는 값의 정의 명령들
    reg = [None] * puzzle.registers
    for i, v in enumerate(puzzle.start):
        reg[i] = v
    missing = set(puzzle.targets) - set(puzzle.start)
    need = []
    for i, (op, a, b, d) in enumerate(prog):
        deps[i] = (reg_def.get(a), reg_def.get(b))
        x, y = reg[a], reg[b]
        if op == "+":
            v = x + y
        elif op == "-":
            v = x - y
        elif op == "*":
            v = x * y
        else:
            v = x // y
        reg[d] = v
        reg_def[d] = i
        if v in missing:
            missing.discard(v)
            need.append(i)
    live = [False] * n
    stack = list(need)
    while stack:
        i = stack.pop()
        if live[i]:
            continue
        live[i] = True
        for j in deps[i]:
            if j is not None and not live[j]:
                stack.append(j)
    return [ins for i, ins in enumerate(prog) if live[i]]
