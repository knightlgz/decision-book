#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""生成「{卦名}卦 × 工作/事業」FAQ 回答（非试点页用），供卦页 FAQ 区 + FAQPage schema。

背景：词池实收 57 组 {卦名}工作/事業 组合词；GSC 已有 明夷卦工作/益卦工作/天山遯卦工作
真实曝光（位 46-72）。本生成器为非试点页 54 卦各产出 1 则 FAQ 问答（tc+sc）。

用法:
  python3 generate_work_faq.py --test 2     # 前 2 卦测试打印（不保存）
  python3 generate_work_faq.py --all        # 全量生成（断点续跑）

输出: src/data/work_faq.json = {卦号: {"tc": {"q":..., "a":...}, "sc": {...}}}
"""
import json
import subprocess
import sys
import tempfile
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).parent
INTERP_TC = ROOT / "src/data/hexagram_interpretations.json"
INTERP_SC = ROOT / "src/data/hexagram_interpretations_sc.json"
DATA_FILE = ROOT / "src/data/hexagrams.js"
OUT = ROOT / "src/data/work_faq.json"

PILOT_SKIP = {3, 5, 16, 27, 29, 33, 38, 41, 47, 52}  # SEO_PILOT 试点页跳过（保持实验干净）
BATCH = 4
API = "https://api.deepseek.com/chat/completions"
MODEL = "deepseek-flash"


def load_key():
    for line in (Path.home() / ".hermes/.env").read_text().splitlines():
        if line.strip().startswith("DEEPSEEK_API_KEY"):
            return line.split("=", 1)[1].strip().strip("'\"")
    raise SystemExit("DEEPSEEK_API_KEY not found in ~/.hermes/.env")


def load_hexagrams():
    tmp = Path(tempfile.gettempdir()) / "dump_hx_faq.mjs"
    tmp.write_text(
        "import H from '%s';\nconsole.log(JSON.stringify(H));\n" % DATA_FILE.as_posix()
    )
    r = subprocess.run(["node", tmp.as_posix()], capture_output=True, text=True, cwd=ROOT)
    if r.returncode != 0:
        raise SystemExit("node dump failed: " + r.stderr[:300])
    return {int(h["number"]): h for h in json.loads(r.stdout)}


SYS_TC = "你是易經職場內容編輯，服務台灣與海外華語讀者。只輸出 JSON，不要任何其他文字。"
SYS_SC = "你是简体中文职场内容编辑，服务海外华语与简体中文读者。只输出 JSON，不要任何其他文字。"


def build_prompt(items, lang):
    is_tc = lang == "tc"
    blocks = []
    for it in items:
        blocks.append(
            f"【卦號 {it['n']}｜{it['name']}】\n白話釋義：{it['meaning']}\n職場啟示：{it['career']}"
            if is_tc
            else f"【卦号 {it['n']}｜{it['name']}】\n白话释义：{it['meaning']}\n职场启示：{it['career']}"
        )
    body = "\n\n".join(blocks)
    if is_tc:
        return f"""任務：根據每卦提供的素材，各撰寫一則 FAQ 回答（繁體中文）。

每則要求：
1. 開頭固定為「在職場與事業上，{{卦名}}卦提醒你：」（{{卦名}} 用該卦名稱）
2. 冒號之後 40–70 字，概括此卦給工作與事業的核心提醒，須體現該卦卦義關鍵（自然帶到卦辭核心詞或核心意象）
3. 只能依據素材改寫，不得添加素材以外的斷言、數字、案例或承諾；語氣溫厚務實
4. 整則回答（含開頭）不超過 100 字
5. 台灣慣用語（勿用港澳或大陸用詞）

素材：

{body}

輸出 JSON（鍵=卦號字串，值={{"a": "..."}}）："""
    return f"""任务：根据每卦提供的素材，各撰写一则 FAQ 回答（简体中文）。

每则要求：
1. 开头固定为「在职场和事业上，{{卦名}}卦提醒你：」（{{卦名}} 用该卦名称）
2. 冒号之后 40–70 字，概括此卦给工作和事业的核心提醒，须体现该卦卦义关键（自然带到卦辞核心词或核心意象）
3. 只能依据素材改写，不得添加素材以外的断言、数字、案例或承诺；语气温厚务实
4. 整则回答（含开头）不超过 100 字
5. 大陆惯用用语（勿用台湾用词）

素材：

{body}

输出 JSON（键=卦号字符串，值={{"a": "..."}}）："""


def _parse_json_loose(txt):
    """容忍 markdown 围栏/前后缀噪音的 JSON 解析；空内容直接抛错触发重试。"""
    if not txt or not txt.strip():
        raise ValueError("empty content")
    t = txt.strip()
    if t.startswith("```"):
        t = t.strip("`")
        t = t[t.find("{"):]
    try:
        return json.loads(t)
    except Exception:
        i, j = t.find("{"), t.rfind("}")
        if i >= 0 and j > i:
            return json.loads(t[i:j + 1])
        raise


def call(api_key, prompt, system):
    body = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.4,
        "response_format": {"type": "json_object"},
        "max_tokens": 4096,
    }
    req = urllib.request.Request(
        API,
        data=json.dumps(body).encode(),
        headers={"Authorization": "Bearer " + api_key, "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=240) as resp:
        d = json.loads(resp.read())
    return _parse_json_loose(d["choices"][0]["message"].get("content") or "")


def make_items(nums, hx, interp, lang):
    items = []
    for n in nums:
        name = hx[n]["tc"]["name"] if lang == "tc" else hx[n]["sc"]["name"]
        iv = interp.get(str(n)) or interp.get(n) or {}
        items.append(
            {
                "n": n,
                "name": name,
                "meaning": (iv.get("meaning") or "")[:400],
                "career": (iv.get("career") or "")[:500],
            }
        )
    return items


def q_for(name, lang):
    if lang == "tc":
        return f"{name}卦在工作與事業上有什麼啟示？"
    return f"{name}卦在工作和事业上有什么启示？"


def main():
    args = sys.argv[1:]
    test_mode = "--test" in args
    test_n = int(args[args.index("--test") + 1]) if test_mode else 0

    api_key = load_key()
    hx = load_hexagrams()
    interp_tc = json.loads(INTERP_TC.read_text(encoding="utf-8"))
    interp_sc = json.loads(INTERP_SC.read_text(encoding="utf-8"))

    done = {}
    if OUT.exists() and not test_mode:
        done = json.loads(OUT.read_text(encoding="utf-8"))

    targets = [n for n in sorted(hx) if n not in PILOT_SKIP and str(n) not in done]
    if test_mode:
        targets = targets[:test_n]
    print(f"目标 {len(targets)} 卦（打头: {targets[:8]}）")

    for i in range(0, len(targets), BATCH):
        chunk = targets[i : i + BATCH]
        for lang, interp in (("tc", interp_tc), ("sc", interp_sc)):
            items = make_items(chunk, hx, interp, lang)
            prompt = build_prompt(items, lang)
            sysp = SYS_TC if lang == "tc" else SYS_SC
            for attempt in range(4):
                try:
                    out = call(api_key, prompt, sysp)
                    break
                except Exception as e:  # noqa: BLE001
                    print(f"  批次 {chunk} {lang} 第{attempt+1}次失败: {e}", flush=True)
                    time.sleep(5 + attempt * 6)
            else:
                raise SystemExit("重试耗尽，退出（可重跑续传）")
            missing = [c for c in chunk if str(c) not in out]
            if missing:
                print(f"  ⚠ 缺号 {missing} ({lang})")
            if test_mode:
                for n, v in out.items():
                    print(f"[{lang}] {n}: {v.get('a','')}")
            else:
                for c in chunk:
                    if str(c) in out:
                        a = out[str(c)].get("a", "").strip()
                        name = hx[c]["tc"]["name"] if lang == "tc" else hx[c]["sc"]["name"]
                        done.setdefault(str(c), {})[lang] = {"q": q_for(name, lang), "a": a}
                OUT.write_text(json.dumps(done, ensure_ascii=False, indent=2), encoding="utf-8")
                print(f"  批次 {chunk} 完成（{lang}）累计 {len(done)} 卦")
            time.sleep(1.2)
    print("完成。输出:", OUT)


if __name__ == "__main__":
    main()
