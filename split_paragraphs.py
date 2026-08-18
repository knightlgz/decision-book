#!/usr/bin/env python3
"""
给白话解读按表意插入段落标记 |||
不修改文字，只在语义边界插入分隔符
"""
import json
import os
import re
import sys
import time
from pathlib import Path

ROOT = Path(__file__).parent
INTERP_FILE = ROOT / "src" / "data" / "hexagram_interpretations.json"
KEY = os.environ.get("DEEPSEEK_API_KEY", "")
API = "https://api.deepseek.com/v1/chat/completions"


def load_data():
    return json.loads(INTERP_FILE.read_text(encoding="utf-8"))


def split_batch(texts, model="deepseek-v4-pro"):
    """texts: [(number, meaning_text)] → [(number, meaning_with_markers)]"""
    import requests

    items = "\n\n".join(f"【{num}】{text}" for num, text in texts)
    prompt = f"""以下是易經白話釋義段落。請在每段文字的語義邊界處插入分隔符「|||」，將文字分成 2-3 個表意完整的自然段。

規則：
1. 只插入「|||」，絕對不要修改、增刪任何文字
2. 按表意劃分：轉折、遞進、舉例、總結處是自然分段點
3. 引文「」內的句號不是分段點，不要拆開引文
4. 每段 2-4 句，保持語義完整

輸出格式（每行一段，不要 markdown）：
【編號】第一段|||第二段|||第三段

{items}"""

    resp = requests.post(
        API,
        headers={"Authorization": f"Bearer {KEY}", "Content-Type": "application/json"},
        json={
            "model": model,
            "messages": [
                {"role": "system", "content": "你是中文排版专家。只插入分隔符，绝不修改文字。"},
                {"role": "user", "content": prompt},
            ],
            "max_tokens": 8000,
            "temperature": 0.3,
        },
        timeout=180,
    )
    if resp.status_code != 200:
        print(f"  API {resp.status_code}: {resp.text[:150]}")
        return None
    content = resp.json()["choices"][0]["message"].get("content", "")
    if not content:
        print("  ⚠️ 空输出")
        return None

    # 解析 【编号】段落|||段落
    results = {}
    for m in re.finditer(r"【(\d+)】(.+?)(?=【\d+】|$)", content, re.DOTALL):
        num = m.group(1)
        marked = m.group(2).strip()
        if "|||" in marked:
            results[num] = marked
    return results if results else None


def main():
    data = load_data()
    todo = {k: v for k, v in data.items() if "|||" not in v["meaning"]}
    print(f"待分段: {len(todo)} 卦")

    batch_size = 5
    items = sorted(todo.items(), key=lambda x: int(x[0]))
    for i in range(0, len(items), batch_size):
        batch = items[i:i + batch_size]
        batch_texts = [(num, v["meaning"]) for num, v in batch]
        nums = [num for num, _ in batch]
        print(f"批次 {i // batch_size + 1}: 第{nums[0]}-{nums[-1]}卦 ...")
        for attempt in range(3):
            result = split_batch(batch_texts)
            if result:
                for num, marked in result.items():
                    if num in data:
                        data[num]["meaning"] = marked
                INTERP_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
                print(f"  ✓ 已分 {len(result)} 卦")
                break
            print(f"  重试 {attempt + 1}")
            time.sleep(5)
        time.sleep(2)

    done = sum(1 for v in data.values() if "|||" in v["meaning"])
    print(f"\n完成！已分段: {done}/64")


if __name__ == "__main__":
    main()
