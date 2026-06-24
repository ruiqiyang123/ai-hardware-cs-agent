"""评测历史趋势查看脚本。

读取 eval_results/history.jsonl（由 run_eval.py --record 产生），
按时间顺序打印整体覆盖率与各分类的演进，用于量化多次优化的效果。

用法：
    python eval/trend.py
"""
import json
import os
import sys


def load_history() -> list[dict]:
    path = os.path.join(os.path.dirname(__file__), "eval_results", "history.jsonl")
    if not os.path.exists(path):
        print(f"❌ 找不到历史文件：{path}")
        print("   请先运行：python eval/run_eval.py --tag <name> --record")
        sys.exit(1)

    records = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    return records


def main():
    records = load_history()
    if not records:
        print("历史文件为空")
        return

    print("=" * 64)
    print(f"📈 评测历史趋势（共 {len(records)} 次记录）")
    print("=" * 64)

    # 收集所有分类
    all_cats = set()
    for r in records:
        all_cats.update(r.get("category_stats", {}).keys())

    # 表头
    header = f"{'时间':<26}{'标签':<10}{'题数':<6}{'整体':<8}" + "".join(f"{c:<10}" for c in sorted(all_cats))
    print(header)
    print("-" * len(header))

    for r in records:
        ts = r.get("timestamp", "")[:19]
        tag = r.get("tag", "")
        total = r.get("total_cases", 0)
        overall = r.get("overall_coverage", 0)
        cats = r.get("category_stats", {})
        row = f"{ts:<26}{tag:<10}{total:<6}{overall:<8.0%}" + "".join(
            f"{cats.get(c, {}).get('avg', 0):<10.0%}" for c in sorted(all_cats)
        )
        print(row)

    # 整体趋势小结
    if len(records) >= 2:
        first, last = records[0], records[-1]
        delta = (last["overall_coverage"] - first["overall_coverage"]) * 100
        print(f"\n💡 整体覆盖率：{first['overall_coverage']:.0%} → {last['overall_coverage']:.1%} "
              f"({delta:+.1f} 个百分点，共 {len(records)} 次评测)")


if __name__ == "__main__":
    main()
