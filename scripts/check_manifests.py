#!/usr/bin/env python3
"""매니페스트 정합성 — 다섯 파일이 같은 버전, 같은 이름을 말하는지 확인한다.

Codex(portable + .codex-plugin)와 Claude Code(.claude-plugin)가 같은 저장소를
읽기 때문에 버전이 갈라지면 한쪽만 옛날 스킬을 설치한다. 눈으로 지킬 수 있는
불변식이 아니라서 CI 에 박아 둔다.

    python3 scripts/check_manifests.py
"""
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent

# (파일, 버전 꺼내는 함수, 이름 꺼내는 함수)
SOURCES = [
    ("plugin.json", lambda d: d["version"], lambda d: d["name"]),
    (".codex-plugin/plugin.json", lambda d: d["version"], lambda d: d["name"]),
    (".claude-plugin/plugin.json", lambda d: d["version"], lambda d: d["name"]),
    (".agents/plugins/marketplace.json",
     lambda d: None, lambda d: d["plugins"][0]["name"]),
    (".claude-plugin/marketplace.json",
     lambda d: d["plugins"][0]["version"], lambda d: d["plugins"][0]["name"]),
]


def main():
    # CI 로그로 리다이렉트되면 윈도우에서 로케일 인코딩으로 떨어진다. 화살표가 있다.
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")
    versions, names, failed = {}, {}, 0
    for rel, get_version, get_name in SOURCES:
        data = json.loads((ROOT / rel).read_text(encoding="utf-8"))
        version = get_version(data)
        if version is not None:
            versions[rel] = version
        names[rel] = get_name(data)

    for label, values in [("version", versions), ("name", names)]:
        distinct = sorted(set(values.values()))
        ok = len(distinct) == 1
        failed += not ok
        print(f"{'ok  ' if ok else 'FAIL'}  {label}: {', '.join(distinct)}")
        if not ok:
            for rel, value in values.items():
                print(f"        {rel}: {value}")

    # 스킬 심볼릭 링크가 복사본으로 바뀌면 두 에이전트의 스킬이 갈라진다.
    link = ROOT / ".agents/skills/notion-doc"
    ok = link.is_symlink() and (link.resolve() == (ROOT / "skills/notion-doc").resolve())
    failed += not ok
    print(f"{'ok  ' if ok else 'FAIL'}  .agents/skills/notion-doc → skills/notion-doc 심볼릭 링크")

    print(f"\n{'실패 ' + str(failed) + '건' if failed else '전부 통과'}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
