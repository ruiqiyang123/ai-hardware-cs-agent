"""RAG 问答效果评测脚本。

用途：对 eval_cases.json 里的每道题跑 Agent，统计关键词覆盖率，
输出分类报告，用于量化优化效果（分块策略、Top-K、Prompt 等）。

用法：
    python eval/run_eval.py                    # 用当前配置评测
    python eval/run_eval.py --tag before       # 标记为"优化前"，结果存 eval_results/before.json
    python eval/run_eval.py --tag after        # 标记为"优化后"
    python eval/run_eval.py --tag after --record  # 同时追加到 eval_results/history.jsonl

产出：
    - 控制台打印整体 + 分类的关键词覆盖率
    - eval_results/<tag>.json 保存详细结果，方便前后对比
    - --record 时追加一行到 eval_results/history.jsonl，供 trend.py 查看优化趋势
"""
import argparse
import json
import os
import sys
from collections import defaultdict
from datetime import datetime
from typing import Any

# 确保能 import 项目模块
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


def load_cases(path: str) -> list:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def run_agent(agent: Any, question: str) -> str:
    """跑一遍 Agent，把最终回答事件拼成完整字符串。

    ReactAgent.execute_stream 现在返回 (kind, content) 事件流：
    thought/tool_call/tool_result 用于前端过程展示，评测只统计 answer。
    兼容旧版纯字符串流，方便历史脚本或测试桩复用。
    """
    chunks = []
    for chunk in agent.execute_stream(question):
        if isinstance(chunk, tuple) and len(chunk) == 2:
            kind, content = chunk
            if kind == "answer":
                chunks.append(content)
        else:
            chunks.append(str(chunk))
    return "".join(chunks)


def score_answer(answer: str, expected_keywords: list) -> dict:
    """计算关键词覆盖率：命中关键词数 / 期望关键词数。"""
    hit = [kw for kw in expected_keywords if kw in answer]
    missed = [kw for kw in expected_keywords if kw not in answer]
    coverage = len(hit) / len(expected_keywords) if expected_keywords else 0
    return {
        "coverage": coverage,
        "hit_keywords": hit,
        "missed_keywords": missed,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--tag", default="default", help="结果标签，如 before/after")
    parser.add_argument("--cases", default=None, help="评测集路径，默认 eval/eval_cases.json")
    parser.add_argument("--record", action="store_true", help="追加本次结果到 eval_results/history.jsonl")
    args = parser.parse_args()

    cases_path = args.cases or os.path.join(os.path.dirname(__file__), "eval_cases.json")
    cases = load_cases(cases_path)

    print(f"📋 评测集：{len(cases)} 题　标签：{args.tag}")
    print("=" * 60)

    from agent.react_agent import ReactAgent

    agent = ReactAgent()
    results = []
    cat_stats = defaultdict(lambda: {"total_cov": 0, "count": 0})

    for i, case in enumerate(cases, 1):
        question = case["question"]
        print(f"\n[{i}/{len(cases)}] {question}")

        try:
            answer = run_agent(agent, question)
        except Exception as e:
            print(f"  ❌ Agent 执行失败：{e}")
            answer = ""

        score = score_answer(answer, case["expected_keywords"])
        print(f"  覆盖率：{score['coverage']:.0%}　命中：{score['hit_keywords']}")

        if score["missed_keywords"]:
            print(f"  漏掉：{score['missed_keywords']}")

        cat = case["category"]
        cat_stats[cat]["total_cov"] += score["coverage"]
        cat_stats[cat]["count"] += 1

        results.append({
            "question": question,
            "category": cat,
            "expected_keywords": case["expected_keywords"],
            "answer": answer,
            "coverage": score["coverage"],
            "hit_keywords": score["hit_keywords"],
            "missed_keywords": score["missed_keywords"],
        })

    # 汇总
    overall = sum(r["coverage"] for r in results) / len(results) if results else 0
    print("\n" + "=" * 60)
    print(f"🎯 整体关键词覆盖率：{overall:.1%}")
    print("\n分类覆盖率：")
    for cat, s in sorted(cat_stats.items()):
        avg = s["total_cov"] / s["count"]
        print(f"  {cat}: {avg:.1%} ({s['count']} 题)")

    # 保存结果
    result_dir = os.path.join(os.path.dirname(__file__), "eval_results")
    os.makedirs(result_dir, exist_ok=True)
    output_path = os.path.join(result_dir, f"{args.tag}.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump({
            "tag": args.tag,
            "timestamp": datetime.now().isoformat(),
            "total_cases": len(results),
            "overall_coverage": overall,
            "category_stats": {cat: {"avg": s["total_cov"] / s["count"], "count": s["count"]}
                               for cat, s in cat_stats.items()},
            "results": results,
        }, f, ensure_ascii=False, indent=2)

    print(f"\n💾 结果已保存：{output_path}")

    # 可选：追加到历史趋势文件，供 trend.py 查看优化演进
    if args.record:
        history_path = os.path.join(result_dir, "history.jsonl")
        with open(history_path, "a", encoding="utf-8") as f:
            f.write(json.dumps({
                "tag": args.tag,
                "timestamp": datetime.now().isoformat(),
                "total_cases": len(results),
                "overall_coverage": overall,
                "category_stats": {cat: {"avg": s["total_cov"] / s["count"], "count": s["count"]}
                                   for cat, s in cat_stats.items()},
            }, ensure_ascii=False) + "\n")
        print(f"📈 已追加到历史趋势：{history_path}")


if __name__ == "__main__":
    main()
