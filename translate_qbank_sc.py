#!/usr/bin/env python3
"""LLM 重转：QUESTIONS_BANK（台繁）→ QUESTIONS_BANK_SC（大陆简体，写回 question_bank.py）

禁机翻铁律（2026-09-14）：不用 opencc 等机械转换，全部 LLM 语际转写。
分批转写（每批 5 分类），逐批校验条数一致，全部成功后一次性写回。
"""
import json
import sys
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).parent
QF = ROOT / 'question_bank.py'
sys.path.insert(0, str(ROOT))
import question_bank as qb  # noqa: E402

SYS = """你是资深简体中文职场内容编辑，服务中国大陆读者。
把以下台湾繁体中文的职场提问（JSON 格式 {分类: [问题列表…]}）转写为大陆简体中文。
要求：
1. 语际转写而非字形转换——台湾用词一律换成大陆说法（專案→项目、簡報→汇报、透過→通过、職涯→职业、資遣→裁员、升遷→晋升、主管→主管、履歷→简历、薪資→工资 等）。
2. 语气保持口语化（这些是用户在职场论坛的求救式提问），自然真实，不书面化。
3. 只转写问题本身，不增删信息、不加解释。
4. 分类键（JSON 的键名）保持不变，每个分类下的问题条数不变。
仅输出 JSON，格式与输入一致。不要任何其他文字。"""


def load_key():
    for line in (Path.home() / '.hermes/.env').read_text().splitlines():
        if line.strip().startswith('DEEPSEEK_API_KEY'):
            return line.split('=', 1)[1].strip().strip("'\"")
    raise SystemExit('DEEPSEEK_API_KEY not found')


def call(api_key, payload):
    body = {
        "model": "deepseek-flash",
        "messages": [
            {"role": "system", "content": SYS},
            {"role": "user", "content": json.dumps(payload, ensure_ascii=False)},
        ],
        "temperature": 0.3,
        "response_format": {"type": "json_object"},
    }
    req = urllib.request.Request(
        "https://api.deepseek.com/chat/completions",
        data=json.dumps(body).encode(),
        headers={"Authorization": "Bearer " + api_key, "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=240) as r:
        txt = json.load(r)["choices"][0]["message"]["content"]
    return json.loads(txt)


def main():
    api_key = load_key()
    tc = qb.QUESTIONS_BANK
    cats = list(tc.keys())
    result = {}
    BATCH = 5
    for i in range(0, len(cats), BATCH):
        batch = {c: tc[c] for c in cats[i:i + BATCH]}
        ok = False
        for attempt in range(3):
            try:
                out = call(api_key, batch)
                for c in batch:
                    assert c in out and isinstance(out[c], list) and len(out[c]) == len(batch[c]), f'{c} 校验失败'
                result.update(out)
                print(f'批 {i // BATCH + 1}/{(len(cats) + BATCH - 1) // BATCH}: {list(batch.keys())[0]}… ✓', flush=True)
                ok = True
                break
            except Exception as e:
                print(f'批 {i // BATCH + 1} 第{attempt + 1}次失败: {e}', flush=True)
                time.sleep(5)
        if not ok:
            raise SystemExit(f'批 {i // BATCH + 1} 三次失败，中止（未写回）')
        time.sleep(1)

    # 校验通过 → 写回 question_bank.py（括号匹配替换 SC 块）
    src = QF.read_text(encoding='utf-8')
    i = src.find('QUESTIONS_BANK_SC')
    assert i > 0, 'SC 块未找到'
    j = src.find('{', i)
    depth = 0
    k = j
    while k < len(src):
        if src[k] == '{':
            depth += 1
        elif src[k] == '}':
            depth -= 1
            if depth == 0:
                break
        k += 1
    new_block = 'QUESTIONS_BANK_SC = ' + json.dumps(result, ensure_ascii=False, indent=4)
    QF.write_text(src[:i] + new_block + src[k + 1:], encoding='utf-8')
    print(f'✅ 写回完成：{len(result)} 分类 / {sum(len(v) for v in result.values())} 条')

    # 验证 import
    import importlib
    importlib.reload(qb)
    n = sum(len(v) for v in qb.QUESTIONS_BANK_SC.values())
    print(f'✅ 验证：reload 后 {n} 条可读')


if __name__ == '__main__':
    main()
