#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""生成「第一页页群 × 场景痛点」FAQ 问答（B 方案，2026-10-07），供卦页 FAQ 区 + FAQPage schema。

针对 SEO_SCENARIO 覆盖的 18 个场景卦（generate_hexagram_pages.py），每卦产出 1 则
「场景问题 → 卦义回应」问答（tc+sc）。场景词均经 Google suggest 实测（2026-10-07）。

用法:
  python3 generate_scenario_faq.py --test 2     # 前 2 卦测试打印（不保存）
  python3 generate_scenario_faq.py              # 全量生成（断点续跑）

输出: src/data/scenario_faq.json = {卦号: {"tc": {"q","a"}, "sc": {...}}}
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
OUT = ROOT / "src/data/scenario_faq.json"

# 场景词表（与 generate_hexagram_pages.py 的 SEO_SCENARIO 同步；键=归一化卦号）
SCENARIOS = {
    "24": ("低谷期怎麼辦", "低谷期怎么办"),
    "18": ("公司管理混亂怎麼辦", "公司管理混乱怎么办"),
    "30": ("人生迷茫怎麼辦", "人生迷茫怎么办"),
    "43": ("猶豫不決怎麼辦", "犹豫不决怎么办"),
    "58": ("嘴笨怎麼辦", "嘴笨怎么办"),
    "15": ("老實人吃虧怎麼辦", "老实人吃亏怎么办"),
    "8": ("怎麼累積人脈", "怎么积累人脉"),
    "7": ("怎麼帶團隊", "怎么带团队"),
    "57": ("不會拒絕別人怎麼辦", "不会拒绝别人怎么办"),
}
BATCH = 4
API = "https://api.deepseek.com/chat/completions"
MODEL = "deepseek-flash"


def load_key():
    for line in (Path.home() / ".hermes/.env").read_text().splitlines():
        if line.strip().startswith("DEEPSEEK_API_KEY"):
            return line.split("=", 1)[1].strip().strip("'\"")
    raise SystemExit("DEEPSEEK_API_KEY not found in ~/.hermes/.env")


def load_hexagrams():
    tmp = Path(tempfile.gettempdir()) / "dump_hx_sfaq.mjs"
    tmp.write_text(
        "import H from '%s';\nconsole.log(JSON.stringify(H));\n" % DATA_FILE.as_posix()
    )
    r = subprocess.run(["node", tmp.as_posix()], capture_output=True, text=True, cwd=ROOT)
    if r.returncode != 0:
        raise SystemExit("node dump failed: " + r.stderr[:300])
    return {int(h["number"]): h for h in json.loads(r.stdout)}


SYS_TC = "你是易經與商業內容編輯，服務台灣與海外華語讀者。只輸出 JSON，不要任何其他文字。"
SYS_SC = "你是简体中文商业内容编辑，服务海外华语与简体中文读者。只输出 JSON，不要任何其他文字。"


def build_prompt(items, lang):
    is_tc = lang == "tc"
    blocks = []
    for it in items:
        blocks.append(
            f"【卦號 {it['n']}｜{it['name']}｜場景問題：{it['kw']}】\n白話釋義：{it['meaning']}\n職場啟示：{it['career']}"
            if is_tc
            else f"【卦号 {it['n']}｜{it['name']}｜场景问题：{it['kw']}】\n白话释义：{it['meaning']}\n职场启示：{it['career']}"
        )
    body = "\n\n".join(blocks)
    if is_tc:
        return f"""任務：針對每卦的「場景問題」，各撰寫一則 FAQ 回答（繁體中文），直接回應這個處境。

每則要求：
1. 開頭 10 字內自然帶出該卦名（如「{{卦名}}卦的提醒是：」或行文自然融入，不強制句式）
2. 全則 50–100 字、2–3 句；要給具體可執行的方向（先做什麼、別做什麼），不要空泛安慰
3. 內容須扣住該卦卦義關鍵（自然帶到卦辭核心詞或核心意象）；只能依據素材改寫，不得編造案例、數字、承諾
4. 語氣溫厚務實，台灣慣用語（勿用港澳或大陸用詞）

素材：

{body}

輸出 JSON（鍵=卦號字串，值={{"a": "..."}}）："""
    return f"""任务：针对每卦的「场景问题」，各撰写一则 FAQ 回答（简体中文），直接回应这个处境。

每则要求：
1. 开头 10 字内自然带出该卦名（如「{{卦名}}卦的提醒是：」或行文自然融入，不强制句式）
2. 全则 50–100 字、2–3 句；要给出具体可执行的方向（先做什么、别做什么），不要空泛安慰
3. 内容须扣住该卦卦义关键（自然带到卦辞核心词或核心意象）；只能依据素材改写，不得编造案例、数字、承诺
4. 语气温厚务实，大陆惯用语（勿用台湾用词）

素材：

{body}

输出 JSON（键=卦号字符串，值={{"a": "..."}}）："""


def _parse_json_loose(txt):
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
        kw = SCENARIOS[str(n)][0] if lang == "tc" else SCENARIOS[str(n)][1]
        items.append(
            {
                "n": n,
                "name": name,
                "kw": kw,
                "meaning": (iv.get("meaning") or "")[:400],
                "career": (iv.get("career") or "")[:500],
            }
        )
    return items


def q_for(n, lang):
    kw = SCENARIOS[str(n)][0] if lang == "tc" else SCENARIOS[str(n)][1]
    return kw + "？"


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

    targets = [int(k) for k in sorted(SCENARIOS, key=int) if k not in done]
    if test_mode:
        targets = targets[:test_n]
    print(f"目标 {len(targets)} 卦（打头: {targets[:8]}）", flush=True)

    for i in range(0, len(targets), BATCH):
        chunk = targets[i: i + BATCH]
        for lang, interp in (("tc", interp_tc), ("sc", interp_sc)):
            items = make_items(chunk, hx, interp, lang)
            prompt = build_prompt(items, lang)
            sysp = SYS_TC if lang == "tc" else SYS_SC
            out = None
            for attempt in range(4):
                try:
                    out = call(api_key, prompt, sysp)
                    break
                except Exception as e:  # noqa: BLE001
                    print(f"  批次 {chunk} {lang} 第{attempt+1}次失败: {e}", flush=True)
                    time.sleep(5 + attempt * 6)
            if out is None:
                raise SystemExit("重试耗尽，退出（可重跑续传）")
            missing = [c for c in chunk if str(c) not in out]
            if missing:
                print(f"  ⚠ 缺号 {missing} ({lang})", flush=True)
            if test_mode:
                for n, v in out.items():
                    print(f"[{lang}] {n}: Q={q_for(int(n), lang)} A={v.get('a','')}", flush=True)
            else:
                for c in chunk:
                    if str(c) in out:
                        a = out[str(c)].get("a", "").strip()
                        done.setdefault(str(c), {})[lang] = {"q": q_for(c, lang), "a": a}
                OUT.write_text(json.dumps(done, ensure_ascii=False, indent=2), encoding="utf-8")
                print(f"  批次 {chunk} 完成（{lang}）累计 {len(done)} 卦", flush=True)
            time.sleep(1.2)
    print("完成。输出:", OUT)


if __name__ == "__main__":
    main()
