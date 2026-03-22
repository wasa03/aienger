"""
課題2.csvのデータを読み込み、
各参加者のスコアの平均、最高点、最低点と、
科目ごとの平均、最高点、最低点を算出するプログラム
"""

import csv
from collections import defaultdict


def main():
    # 参加者ごとの(スコア, 科目)を格納する辞書
    participant_scores = defaultdict(list)
    # 科目ごとのスコアを格納する辞書
    subject_scores = defaultdict(list)

    # 課題2.csvを読み込む
    csv_path = "課題2.csv"
    with open(csv_path, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            name = row["名前"]
            score = int(row["スコア"])
            subject = row["科目"]
            participant_scores[name].append((score, subject))
            subject_scores[subject].append(score)

    # === 参加者ごとの集計 ===
    print("【参加者ごとのスコア】")
    print(f"{'参加者':<12} {'平均':>8} {'最高点':>14} {'最低点':>14}")
    print("-" * 52)

    for name in sorted(participant_scores.keys()):
        records = participant_scores[name]
        scores = [s for s, _ in records]
        average = sum(scores) / len(scores)
        max_record = max(records, key=lambda x: x[0])
        min_record = min(records, key=lambda x: x[0])
        max_score, max_subject = max_record
        min_score, min_subject = min_record
        print(f"{name:<12} {average:>8.2f} {max_score:>4}({max_subject}) {min_score:>4}({min_subject})")

    # === 科目ごとの集計 ===
    print()
    print("【科目ごとのスコア】")
    print(f"{'科目':<8} {'平均':>8} {'最高点':>8} {'最低点':>8}")
    print("-" * 36)

    for subject in sorted(subject_scores.keys()):
        scores = subject_scores[subject]
        average = sum(scores) / len(scores)
        max_score = max(scores)
        min_score = min(scores)
        print(f"{subject:<8} {average:>8.2f} {max_score:>8} {min_score:>8}")


if __name__ == "__main__":
    main()
