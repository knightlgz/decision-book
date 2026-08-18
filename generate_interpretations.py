#!/usr/bin/env python3
"""
批量生成 64 卦白话解读（SEO 优化版）
每卦输出：meaning(白话释义) + career(职场映射) + advice(行动建议)
繁体生成，简体由转换工具生成
"""
import json
import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).parent
DATA_FILE = ROOT / "src" / "data" / "hexagrams.js"
ORIGINAL_FILE = ROOT / "src" / "data" / "iching_original.json"
OUT_FILE = ROOT / "src" / "data" / "hexagram_interpretations.json"

KEY = os.environ.get("DEEPSEEK_API_KEY", "")
API = "https://api.deepseek.com/v1/chat/completions"


def load_hexagrams():
    import subprocess, tempfile
    tmp_js = Path(tempfile.gettempdir()) / "dump_hexagrams2.mjs"
    tmp_js.write_text("""
import HEXAGRAMS from '%s';
console.log(JSON.stringify(HEXAGRAMS));
""" % DATA_FILE.as_posix(), encoding="utf-8")
    r = subprocess.run(["node", tmp_js.as_posix()], capture_output=True, text=True, cwd=ROOT)
    return json.loads(r.stdout)


def load_original():
    return {d["id"]: d for d in json.loads(ORIGINAL_FILE.read_text(encoding="utf-8"))}


def gen_batch(batch, model="deepseek-v4-pro"):
    """batch: [{number, name, insight, scripture, lines_text}]"""
    import requests

    items_desc = []
    for b in batch:
        items_desc.append(
            f"第{b['number']}卦「{b['name']}」\n卦辭：{b['scripture']}\n現有商業解讀：{b['insight']}"
        )

    prompt = f"""你是易經與職場內容專家。為以下卦象各撰寫一段 SEO 優化的白話解讀（繁體中文）。

要求：
1. meaning：白話釋義 150-200 字，用日常語言解釋卦辭含義。自然融入關鍵詞如「{batch[0]['name']}卦」「易經」「曾仕強」「職場」「事業」「決策」。
2. career：職場應用 150-200 字，描寫這個卦在職場中的典型情境（如與主管相處、轉職、創業、同事競爭），讓讀者有「這就是我」的共鳴。融入「{batch[0]['name']}卦 職場」「職場困境」「商業決策」等詞。
3. advice：行動建議 80-120 字，具體可執行，語氣溫暖務實。

卦象資料：
{chr(10).join(items_desc)}

輸出純 JSON（不要 markdown 代碼塊）：
{{"{batch[0]['number']}":{{"meaning":"...","career":"...","advice":"..."}},"XX":{{...}}}}"""

    resp = requests.post(
        API,
        headers={"Authorization": f"Bearer {KEY}", "Content-Type": "application/json"},
        json={
            "model": model,
            "messages": [
                {"role": "system", "content": "你是易经内容专家。直接输出JSON，不要任何解释。"},
                {"role": "user", "content": prompt},
            ],
            "max_tokens": 8000,
            "temperature": 0.75,
        },
        timeout=180,
    )
    if resp.status_code != 200:
        print(f"  API {resp.status_code}: {resp.text[:200]}")
        return None
    content = resp.json()["choices"][0]["message"].get("content", "")
    if not content:
        print("  ⚠️ 空输出（推理吃光token）")
        return None
    # 提取 JSON
    import re
    m = re.search(r"\{.*\}", content, re.DOTALL)
    if not m:
        print(f"  ⚠️ 无JSON: {content[:200]}")
        return None
    try:
        return json.loads(m.group())
    except json.JSONDecodeError:
        print(f"  ⚠️ JSON解析失败: {content[:200]}")
        return None


def main():
    start = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    end = int(sys.argv[2]) if len(sys.argv) > 2 else 65
    batch_size = 3

    hexagrams = load_hexagrams()
    original = load_original()

    # 已有结果续跑
    results = {}
    if OUT_FILE.exists():
        results = json.loads(OUT_FILE.read_text(encoding="utf-8"))

    todo = [h for h in hexagrams if int(h["number"]) >= start and int(h["number"]) < end and h["number"] not in results]
    print(f"待生成: {len(todo)} 卦 (已有 {len(results)})")

    for i in range(0, len(todo), batch_size):
        batch = todo[i:i + batch_size]
        batch_info = []
        for h in batch:
            num = int(h["number"])
            orig = original.get(num, {})
            lines_text = " ".join(l["scripture"] for l in orig.get("lines", []))
            batch_info.append({
                "number": h["number"],
                "name": h["tc"]["name"],
                "insight": h["tc"]["insight"],
                "scripture": orig.get("scripture", ""),
                "lines_text": lines_text,
            })

        print(f"批次 {i // batch_size + 1}: 第{batch[0]['number']}-{batch[-1]['number']}卦 ...")
        for attempt in range(3):
            result = gen_batch(batch_info)
            if result:
                for k, v in result.items():
                    if "meaning" in v and "career" in v and "advice" in v:
                        results[k] = v
                OUT_FILE.write_text(json.dumps(results, ensure_ascii=False, indent=1), encoding="utf-8")
                print(f"  ✓ 已存 {len(results)} 卦")
                break
            print(f"  重试 {attempt + 1} ...")
            time.sleep(5)
        else:
            print("  ✗ 批次失败，跳到下一批")
        time.sleep(2)

    print(f"\n完成！共 {len(results)} 卦 → {OUT_FILE}")


if __name__ == "__main__":
    main()
