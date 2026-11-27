#!/usr/bin/env bash
# 컴파일한 실행 파일을 다시 만든다. 실행 파일은 git에 올리지 않으므로(.gitignore)
# 저장소를 새로 받은 머신에서 한 번 돌린다.
#
# 사용법:
#     core/build.sh
#
# 엔진을 고친 뒤 다시 돌려도 된다. 다만 다른 접근법이 쓰는 lns 사본(아래 cp 줄)도 함께 바뀐다.
set -eu
cd "$(dirname "$0")/.."
CXX="${CXX:-g++}"

build() {  # build <소스> <출력> [추가 옵션]
    echo "빌드: $2"
    "$CXX" -O2 -std=c++17 ${3:-} -o "$2" "$1"
}

# 엔진 (시간 제한으로 도는 탐색이라 -march=native 로 만든다)
build solvers/lns/elf_lns.cpp solvers/lns/elf_lns -march=native
build solvers/walk/walk.cpp solvers/walk/walk -march=native
build solvers/exact/exact.cpp solvers/exact/exact -march=native
build solvers/regfit/elf_regfit.cpp solvers/regfit/elf_regfit -march=native

# 숨은 정수 훑기 도구
for f in solvers/chain/basescan solvers/factor/hidscan \
         solvers/quirk/basescan solvers/quirk/basescan2 solvers/quirk/pairscan solvers/quirk/oracle \
         solvers/search/basescan solvers/search/pairscan solvers/search/partnerscan; do
    build "$f.cpp" "$f"
done

# 다른 접근법이 자기 폴더에 두고 쓰는 lns 사본
cp solvers/lns/elf_lns solvers/fresh/elf_lns       # solvers/fresh/drive.py, drive2.py
cp solvers/lns/elf_lns solvers/lend/elf_lns        # solvers/lend/lib.py
cp solvers/lns/elf_lns solvers/quirk/elf_lns_snap3 # solvers/quirk/polish.py
echo "끝"
