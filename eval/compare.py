"""前后评测结果对比脚本。

用途：对比 eval_results/before.json 和 eval_results/after.json，
输出优化效果，直接用于简历量化数字。

用法：
    python eval/compare.py before after
"""
import json
import os
import sys


def load_result(tag: str) -> dict:
    path = os.path.join(os.path.dirname(__file__), "eval_results", f"{tag}.json")
    if not os.path.exists(path):
        print(f"❌ 找不到结果文件：{path}")
        print(f"   请先运行：python eval/run_eval.py --tag {tag}")
        sys.exit(1)
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def main():
    if len(sys.argv) != 3:
        print("用法：python eval/compare.py <before_tag> <after_tag>")
        print("示例：python eval/compare.py before after")
        sys.exit(1)

    before_tag, after_tag = sys.argv[1], sys.argv[2]
    before = load_result(before_tag)
    after = load_result(after_tag)

    print("=" * 60)
    print(f"📊 优化效果对比：{before_tag} → {after_tag}")
    print("=" * 60)

    # 整体
    b_overall = before["overall_coverage"]
    a_overall = after["overall_coverage"]
    delta = (a_overall - b_overall) * 100
    print(f"\n整体关键词覆盖率：{b_overall:.1%} → {a_overall:.1%}  ({delta:+.1f} 个百分点)")

    # 分类
    print("\n分类对比：")
    all_cats = set(before["category_stats"].keys()) | set(after["category_stats"].keys())
    for cat in sorted(all_cats):
        b = before["category_stats"].get(cat, {}).get("avg", 0)
        a = after["category_stats"].get(cat, {}).get("avg", 0)
        d = (a - b) * 100
        print(f"  {cat}: {b:.1%} → {a:.1%}  ({d:+.1f})")

    print("\n💡 可直接用于简历的表述：")
    print(f'   "构建 {after["total_cases"]} 题评测集，通过优化分块策略与提示词，')
    print(f'    将关键词覆盖率从 {b_overall:.0%} 提升至 {a_overall:.1%}"')


if __name__ == "__main__":
    main()
