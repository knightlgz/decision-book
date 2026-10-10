#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""生成 64 卦「安心话术」reframe_gen.json（C 方案，2026-10-07）——起卦结果页情绪层。

用途：结果区「处境不是判决」原则下，每卦一句的逐卦安顿语（App.jsx 渲染于六爻卡下方/金句之上）。
素材：hexagrams.js（卦名）+ hexagram_originals.json（卦辞）+ insight_gen.json（现有金句·避重复）+ interpretations（释义摘要）。
输出：src/data/reframe_gen.json = {"1": {"tc": "...", "sc": "..."}, ...}

用法:
  python3 generate_reframe.py --test 3   # 前 3 卦测试打印（不保存）
  python3 generate_reframe.py            # 全量生成（断点续跑）
"""
import json
import subprocess
import sys
import tempfile
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).parent
DATA_FILE = ROOT / "src/data/hexagrams.js"
ORIG = ROOT / "src/data/hexagram_originals.json"
INSIGHT = ROOT / "src/data/insight_gen.json"
INTERP_TC = ROOT / "src/data/hexagram_interpretations.json"
INTERP_SC = ROOT / "src/data/hexagram_interpretations_sc.json"
OUT = ROOT / "src/data/reframe_gen.json"

BATCH = 8
API = "https://api.deepseek.com/chat/completions"
MODEL = "deepseek-flash"


def load_key():
    for line in (Path.home() / ".hermes/.env").read_text().splitlines():
        if line.strip().startswith("DEEPSEEK_API_KEY"):
            return line.split("=", 1)[1].strip().strip("'\"")
    raise SystemExit("DEEPSEEK_API_KEY not found in ~/.hermes/.env")


def load_hexagrams():
    tmp = Path(tempfile.gettempdir()) / "dump_hx_reframe.mjs"
    tmp.write_text(
        "import H from '%s';\nconsole.log(JSON.stringify(H));\n" % DATA_FILE.as_posix()
    )
    r = subprocess.run(["node", tmp.as_posix()], capture_output=True, text=True, cwd=ROOT)
    if r.returncode != 0:
        raise SystemExit("node dump failed: " + r.stderr[:300])
    return {int(h["number"]): h for h in json.loads(r.stdout)}


SYS_TC = "你是易經與商業決策內容編輯，服務台灣與海外華語讀者。只輸出 JSON，不要任何其他文字。"
SYS_SC = "你是简体中文商业决策内容编辑。只输出 JSON，不要任何其他文字。"


def build_prompt(items, lang):
    is_tc = lang == "tc"
    blocks = []
    for it in items:
        if is_tc:
            blocks.append(
                f"【卦號 {it['n']}｜{it['name']}】\n卦辭：{it['guaci']}\n"
                f"現有一句話解讀（禁止重複其措辭）：{it['insight']}\n白話釋義摘要：{it['meaning']}"
            )
        else:
            blocks.append(
                f"【卦号 {it['n']}｜{it['name']}】\n卦辞：{it['guaci']}\n"
                f"现有一句话解读（禁止重复其措辞）：{it['insight']}\n白话释义摘要：{it['meaning']}"
            )
    body = "\n\n".join(blocks)
    if is_tc:
        return f"""任務：為易經各卦各寫一句「安心話」（繁體中文）——放在起卦結果頁，用戶抽到該卦後讀到的一句安頓語。

場景：用戶帶著真實困擾來起卦，看到卦名或卦辭字面（例如「困」「剝」「坎」「蹇」「明夷」「否」「訟」）可能緊張，誤以為是被「判決」了。這句安心話要把他從「被宣判」拉回「看處境」：

要求：
1. 先給該卦一個平實的「此刻處境」定位，再帶一句溫厚的提醒或台階（先安頓，後指路）；
2. 消解「定數/判決/凶訊」的誤讀——尤其字面凶險的卦；平順的卦可帶一點「別大意」的提醒；
3. 24–44 字，一到兩句（可用逗號/破折號/分號）；繁體中文、台灣慣用語；
4. 禁止詞語：吉凶、凶兆、運勢、算命、占卜、靈驗、轉運、改運、注定、命中、神準、保證、一定會；不得預測未來結果、不得承諾；
5. 不得重複「現有一句話解讀」的措辭；
6. 句式自然多樣：不要每句都用同一模板（如「不是…而是…」），依卦氣變化。

素材：

{body}

輸出 JSON（鍵=卦號字串，值={{"text": "..."}}）："""
    return f"""任务：为易经各卦各写一句「安心话」（简体中文）——放在起卦结果页，用户得到该卦后读到的一句安顿语。

场景：用户带着真实困扰来起卦，看到卦名或卦辞字面（例如「困」「剥」「坎」「蹇」「明夷」「否」「讼」）可能紧张，误以为是被「判决」了。这句安心话要把他从「被宣判」拉回「看处境」：

要求：
1. 先给该卦一个平实的「此刻处境」定位，再带一句温厚的提醒或台阶（先安顿，后指路）；
2. 消解「定数/判决/凶讯」的误读——尤其字面凶险的卦；平顺的卦可带一点「别大意」的提醒；
3. 24–44 字，一到两句（可用逗号/破折号/分号）；简体中文、大陆惯用语；
4. 禁止词语：吉凶、凶兆、运势、算命、占卜、灵验、转运、改运、注定、命中、神准、保证、一定会；不得预测未来结果、不得承诺；
5. 不得重复「现有一句话解读」的措辞；
6. 句式自然多样：不要每句都用同一模板（如「不是…而是…」），依卦气变化。

素材：

{body}

输出 JSON（键=卦号字符串，值={{"text": "..."}}）："""


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
        "temperature": 0.5,
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


def make_items(nums, hx, orig, insight, interp, lang):
    items = []
    for n in nums:
        name = hx[n]["tc"]["name"] if lang == "tc" else hx[n]["sc"]["name"]
        o = orig.get(n) or {}
        g = (o.get("guaci_tc") if lang == "tc" else o.get("guaci_sc")) or ""
        iv = interp.get(str(n)) or interp.get(n) or {}
        entry = insight.get(str(n)) or insight.get(n) or {}
        ins = entry.get("tc") if lang == "tc" else entry.get("sc")
        items.append(
            {
                "n": n,
                "name": name,
                "guaci": g[:60],
                "insight": ins or "",
                "meaning": (iv.get("meaning") or "")[:300],
            }
        )
    return items


def main():
    args = sys.argv[1:]
    test_mode = "--test" in args
    test_n = int(args[args.index("--test") + 1]) if test_mode else 0

    api_key = load_key()
    hx = load_hexagrams()
    orig = {int(o["id"]): o for o in json.loads(ORIG.read_text(encoding="utf-8"))}
    insight = {str(o["id"]): o for o in json.loads(INSIGHT.read_text(encoding="utf-8"))}
    interp_tc = json.loads(INTERP_TC.read_text(encoding="utf-8"))
    interp_sc = json.loads(INTERP_SC.read_text(encoding="utf-8"))

    done = {}
    if OUT.exists() and not test_mode:
        done = json.loads(OUT.read_text(encoding="utf-8"))

    def complete(k):
        v = done.get(k) or {}
        return bool(v.get("tc") and v.get("sc"))

    targets = [n for n in sorted(hx) if not complete(str(n))]
    if test_mode:
        targets = targets[:test_n]
    print(f"目标 {len(targets)} 卦（打头: {targets[:10]}）", flush=True)

    for i in range(0, len(targets), BATCH):
        chunk = targets[i: i + BATCH]
        for lang, interp in (("tc", interp_tc), ("sc", interp_sc)):
            items = make_items(chunk, hx, orig, insight, interp, lang)
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
                    print(f"[{lang}] {n}: {v.get('text', '')}", flush=True)
            else:
                for c in chunk:
                    if str(c) in out:
                        text = (out[str(c)].get("text") or out[str(c)].get("a") or "").strip()
                        done.setdefault(str(c), {})[lang] = text
                OUT.write_text(json.dumps(done, ensure_ascii=False, indent=2), encoding="utf-8")
                print(f"  批次 {chunk} 完成（{lang}）累计 {len(done)} 卦", flush=True)
            time.sleep(1.2)
    print("完成。输出:", OUT)


if __name__ == "__main__":
    main()
