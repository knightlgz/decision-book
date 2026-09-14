#!/usr/bin/env python3
"""LLM 转译：hexagram_interpretations.json（台繁）→ hexagram_interpretations_sc.json（大陆简体）

铁律（2026-09-14 Kyson 定）：产品全文本（内容 + webapp + 未来英法西葡）禁机翻，
一律 LLM 语际转写——不是字形转换，是语境级转译。

用法:
  python3 translate_interp_sc.py --test 18    # 单卦测试（打印结果）
  python3 translate_interp_sc.py --all        # 批量全量（断点续跑，逐卦保存）
"""
import json
import sys
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).parent
SRC = ROOT / "src/data/hexagram_interpretations.json"
OUT = ROOT / "src/data/hexagram_interpretations_sc.json"

SYS_PROMPT = """你是资深简体中文职场内容编辑，服务中国大陆读者。
任务：把台湾繁体中文的职场/商业解读文本「转写」为大陆简体中文。
这不是字形转换（不是简单繁转简），而是完整的语际转写：
1. 用词大陆化：專案→项目、簡報→汇报、透過→通过、職涯→职业、招募→招聘、履歷→简历、合約→合同、資遣→裁员、升遷→晋升、薪水→工资、溝通管道→沟通渠道、訊息→消息、品質→质量、行銷→营销、分潤→分红、年資→工龄、考績→绩效、應徵→应聘、職缺→岗位、特休→年假、留職停薪→停薪留职——凡台湾惯用而大陆不用的表达，一律换成大陆说法。
2. 语气贴合大陆职场语境，自然、专业，不保留任何台湾语气词与表达习惯。
3. 保留段落结构与 ||| 分隔符；将『』引号改写为「」；不增删任何信息，不添加解释。
输出：仅输出 JSON，格式 {"meaning": "...", "career": "...", "advice": "..."}，不要任何其他文字。"""


def load_key():
    for line in (Path.home() / ".hermes/.env").read_text().splitlines():
        if line.strip().startswith("DEEPSEEK_API_KEY"):
            return line.split("=", 1)[1].strip().strip("'\"")
    raise SystemExit("DEEPSEEK_API_KEY not found in ~/.hermes/.env")


def translate(api_key, obj):
    body = {
        "model": "deepseek-flash",
        "messages": [
            {"role": "system", "content": SYS_PROMPT},
            {"role": "user", "content": json.dumps(obj, ensure_ascii=False)},
        ],
        "temperature": 0.3,
        "response_format": {"type": "json_object"},
    }
    req = urllib.request.Request(
        "https://api.deepseek.com/chat/completions",
        data=json.dumps(body).encode(),
        headers={"Authorization": "Bearer " + api_key, "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=180) as r:
        resp = json.load(r)
    txt = resp["choices"][0]["message"]["content"]
    out = json.loads(txt)
    for k in ("meaning", "career", "advice"):
        if k not in out:
            raise ValueError(f"missing key {k}")
    return out


def main():
    args = sys.argv[1:]
    api_key = load_key()
    src = json.loads(SRC.read_text(encoding="utf-8"))
    out = json.loads(OUT.read_text(encoding="utf-8")) if OUT.exists() else {}

    if "--test" in args:
        n = args[args.index("--test") + 1]
        obj = src[n]
        res = translate(api_key, obj)
        print("=== 原（繁）meaning 前120字 ===")
        print(obj["meaning"][:120])
        print("=== 译（简）meaning 前120字 ===")
        print(res["meaning"][:120])
        print("=== career 前80字 ===")
        print(res["career"][:80])
        return

    keys = sorted(src.keys(), key=lambda x: int(x))
    done = 0
    for n in keys:
        if n in out and all(k in out[n] for k in ("meaning", "career", "advice")):
            continue
        for attempt in range(3):
            try:
                out[n] = translate(api_key, src[n])
                OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
                done += 1
                print(f"[{done}] 卦 {n} ✓", flush=True)
                break
            except Exception as e:
                print(f"卦 {n} 第{attempt+1}次失败: {e}", flush=True)
                time.sleep(5)
        time.sleep(1)
    print(f"完成：本次新增 {done} 卦，累计 {len(out)}/{len(src)}")


if __name__ == "__main__":
    main()
