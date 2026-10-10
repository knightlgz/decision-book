#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""解读正文商业向重写（2026-10-10）：職場語境 → 商業／生意語境

范围：hexagram_interpretations.json（tc）在 meaning/career/advice 三字段中
凡含职场词的字段就地重写；重写后同一字段再经语际转写生成 sc 对应字段。
- 多线程（默认 8 workers）；断点续跑（进度存 ~/.hermes/cache/scratch/）
- 只输出 .new 文件（校验通过后由外部脚本换入正式文件）

用法：
  python3 rewrite_interp_business.py --test 48    # 单卦冒烟（打印，不落盘）
  python3 rewrite_interp_business.py --all        # 全量（多线程）
"""
import json
import re
import sys
import time
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
import urllib.request

ROOT = Path(__file__).parent
TC_FILE = ROOT / "src/data/hexagram_interpretations.json"
SC_FILE = ROOT / "src/data/hexagram_interpretations_sc.json"
TC_OUT = ROOT / "src/data/hexagram_interpretations.new.json"
SC_OUT = ROOT / "src/data/hexagram_interpretations_sc.new.json"
PROG = Path.home() / ".hermes/cache/scratch/interp_rewrite_progress.json"

BANNED = ['職場', '职场', '上班', '同事', '主管', '上司', '升遷', '升职', '晋升', '離職', '离职',
          '辭職', '辞职', '跳槽', '轉職', '转职', '裁員', '裁员', '失業', '失业', '加班',
          '求職', '求职', '打工', '職涯', '職位', '职位', '職級', '白領', '白领', '打工人',
          '職員', '职员', '在職', '在职', '面试', '面試', '資遣', '上級', '上级']

SYS_REWRITE = """你是曾仕強易經思想體系的資深內容編輯，台灣繁體用字。
任務：把易經解讀段落中的「職場／上班族」語境，全面改寫為「商業／做生意」語境。
讀者＝華人中小微企業老闆、創業者、生意人。

改寫規則：
1. 場景按上下文自然映射，不硬套：職場→生意場／商場／經營一線；主管、上司→合夥人、關鍵夥伴、重要客戶（按情境選最順的）；
   同事競爭→同業競爭；升遷→事業更上一層樓；離職／跳槽／轉職→收攤轉行、另闢戰場；加薪→業績與進帳；
   裁員／失業→生意收縮、經營低谷；面試→談合作（按情境）；公司內部→自己的生意裡；上班族→生意人。
2. 必須保留：卦名（如「水風井卦」）、卦辭引用、曾仕強／曾師的提及、原文全部信息量與論點——不增不減、不添加新例子。
3. 保留 ||| 分隔符與段落結構；字數與原文相近（±20%）。
4. 只輸出 JSON 物件：{"欄位名": "改寫後文本", ...}，欄位名與輸入一致，不要任何其他文字。"""

SYS_TRANS = """你是資深簡體中文商業內容編輯。
任務：把台灣繁體中文的商業解讀文本「轉寫」為簡體中文（不是字形轉換，是語境級轉寫）：
1. 用詞大陸化：專案→项目、簡報→汇报、透過→通过、招募→招聘、合約→合同、溝通→沟通、訊息→消息、品質→质量、行銷→营销、分潤→分红 等，凡台灣慣用而大陸不用的表達一律換。
2. 保留 ||| 分隔符與段落結構；『』引號改「」；不增刪信息、不添加解釋。
3. 只輸出 JSON：{"欄位名": "...", ...}，欄位名與輸入一致，不要任何其他文字。"""


def load_key():
    for line in (Path.home() / ".hermes/.env").read_text().splitlines():
        if line.strip().startswith("DEEPSEEK_API_KEY"):
            return line.split("=", 1)[1].strip().strip("'\"")
    raise SystemExit("DEEPSEEK_API_KEY not found in ~/.hermes/.env")


OPENER = urllib.request.build_opener(urllib.request.ProxyHandler({}))  # 强制直连，不被 shell 代理干扰


def call(api_key, sys_prompt, user_text, model, temperature, retries=3):
    for att in range(retries):
        try:
            body = {"model": model,
                    "messages": [{"role": "system", "content": sys_prompt},
                                 {"role": "user", "content": user_text}],
                    "temperature": temperature,
                    "response_format": {"type": "json_object"}}
            req = urllib.request.Request("https://api.deepseek.com/chat/completions",
                                         data=json.dumps(body).encode(),
                                         headers={"Authorization": "Bearer " + api_key,
                                                  "Content-Type": "application/json"})
            with OPENER.open(req, timeout=180) as r:
                resp = json.load(r)
            return json.loads(resp["choices"][0]["message"]["content"])
        except Exception as e:
            if att == retries - 1:
                raise
            time.sleep(3 * (att + 1))


def dirty_fields(item):
    return [f for f in ("meaning", "career", "advice")
            if any(w in item.get(f, "") for w in BANNED)]


def hex_name(item):
    m = re.search(r'([\u4e00-\u9fff]{2,4}卦)', item.get("meaning", "") + item.get("career", ""))
    return m.group(1) if m else ""


def validate(n, fl, txt, orig, tag=""):
    if not txt:
        raise ValueError(f"{n}/{fl}{tag} 空输出")
    bad = [w for w in BANNED if w in txt]
    if bad:
        raise ValueError(f"{n}/{fl}{tag} 残留职场词 {bad}")
    ratio = len(txt) / max(len(orig), 1)
    if not (0.65 <= ratio <= 1.45):
        raise ValueError(f"{n}/{fl}{tag} 长度异常 {ratio:.2f}")
    if txt.count("|||") != orig.count("|||"):
        raise ValueError(f"{n}/{fl}{tag} ||| 数量变化")
    return txt


def process(n, tc_item, sc_item, api_key, rw_model, tr_model):
    dirty = sorted(set(dirty_fields(tc_item)) | set(dirty_fields(sc_item)))
    if not dirty:
        return None
    name = hex_name(tc_item)
    # 1) 重写 tc（只针对 tc 脏字段；校验失败自动重掷，最多 3 次）
    tc_dirty = [f for f in dirty if any(w in tc_item.get(f, "") for w in BANNED)]
    new_tc = {}
    if tc_dirty:
        for attempt in range(3):
            res = call(api_key, SYS_REWRITE,
                       f"第{int(n)}卦「{name}」\n" + json.dumps({f: tc_item[f] for f in tc_dirty}, ensure_ascii=False),
                       rw_model, 0.6)
            try:
                new_tc = {fl: validate(n, fl, res.get(fl, ""), tc_item[fl]) for fl in tc_dirty}
                break
            except ValueError:
                if attempt == 2:
                    raise
                time.sleep(1)
    # 2) 转写 sc（从最终 tc 转写全部脏字段；校验失败重掷，最多 3 次）
    final_tc = {**tc_item, **new_tc}
    new_sc = {}
    for attempt in range(3):
        res_sc = call(api_key, SYS_TRANS,
                      json.dumps({f: final_tc[f] for f in dirty}, ensure_ascii=False),
                      tr_model, 0.3)
        try:
            new_sc = {}
            for fl in dirty:
                txt = res_sc.get(fl, "")
                if not txt:
                    raise ValueError(f"{n}/{fl} sc 空输出")
                bad = [w for w in BANNED if w in txt]
                if bad:
                    raise ValueError(f"{n}/{fl} sc 残留职场词 {bad}")
                if txt.count("|||") != final_tc[fl].count("|||"):
                    raise ValueError(f"{n}/{fl} sc ||| 数量变化")
                new_sc[fl] = txt
            break
        except ValueError:
            if attempt == 2:
                raise
            time.sleep(1)
    return {"tc": new_tc, "sc": new_sc, "dirty": dirty}


def merge_and_write(tc, sc, prog):
    tc_out = json.loads(json.dumps(tc))
    sc_out = json.loads(json.dumps(sc))
    for n, upd in prog.items():
        for f, v in upd["tc"].items():
            tc_out[n][f] = v
        for f, v in upd["sc"].items():
            sc_out[n][f] = v
    TC_OUT.write_text(json.dumps(tc_out, ensure_ascii=False, indent=1), encoding="utf-8")
    SC_OUT.write_text(json.dumps(sc_out, ensure_ascii=False, indent=1), encoding="utf-8")


def main():
    api_key = load_key()
    rw_model = "deepseek-v4-pro"
    tr_model = "deepseek-flash"
    tc = json.loads(TC_FILE.read_text(encoding="utf-8"))
    sc = json.loads(SC_FILE.read_text(encoding="utf-8"))

    if "--test" in sys.argv:
        n = sys.argv[sys.argv.index("--test") + 1]
        r = process(n, tc[n], sc[n], api_key, rw_model, tr_model)
        print(json.dumps(r, ensure_ascii=False, indent=1))
        return

    prog = json.loads(PROG.read_text(encoding="utf-8")) if PROG.exists() else {}
    lock = threading.Lock()
    todo = [n for n in tc if n not in prog]
    print(f"待处理 {len(todo)} 卦（已完成 {len(prog)}）", flush=True)

    failed = []

    def job(n):
        try:
            r = process(n, tc[n], sc[n], api_key, rw_model, tr_model)
        except Exception as e:  # 单卦失败不拖垮全局
            with lock:
                failed.append((n, str(e)[:120]))
                print(f"  ✗ 卦 {n} 失败: {str(e)[:120]}", flush=True)
            return
        with lock:
            if r:
                prog[n] = r
                PROG.write_text(json.dumps(prog, ensure_ascii=False), encoding="utf-8")
                print(f"  ✓ 卦 {n}（{len(r['dirty'])} 字段：{','.join(r['dirty'])}）", flush=True)
            else:
                print(f"  - 卦 {n} 干净，跳过", flush=True)

    with ThreadPoolExecutor(max_workers=8) as ex:
        futs = [ex.submit(job, n) for n in todo]
        for f in as_completed(futs):
            f.result()

    merge_and_write(tc, sc, prog)
    # 校验汇总
    tc_out = json.loads(TC_OUT.read_text(encoding="utf-8"))
    sc_out = json.loads(SC_OUT.read_text(encoding="utf-8"))
    for label, d in (("tc", tc_out), ("sc", sc_out)):
        remain = sum(1 for it in d.values() for f in ("meaning", "career", "advice")
                     if any(w in it.get(f, "") for w in BANNED))
        print(f"[{label}] 残留职场字段: {remain}")
    print(f"完成：{len(prog)}/64 卦已重写；失败 {len(failed)} 个: {failed}；输出 {TC_OUT.name} / {SC_OUT.name}")


if __name__ == "__main__":
    main()
