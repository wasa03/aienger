"""
CSVからデータを読み込み、所属ごとの参加者数と割合を円グラフで表示するスクリプト

使い方:
  pip install matplotlib
  python pie_chart.py
"""

import csv
from collections import Counter, defaultdict
import matplotlib
matplotlib.use('Agg')  # GUI不要で画像保存のみ
import matplotlib.pyplot as plt

# CSVファイルを読み込み
with open('課題3.csv', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    rows = list(reader)

# 所属ごとに参加者数を集計
counts = Counter(row['所属'] for row in rows)
total = len(rows)
# 割合が多い順にソート（降順）
sorted_items = sorted(counts.items(), key=lambda x: x[1], reverse=True)
labels = [item[0] for item in sorted_items]
sizes = [item[1] for item in sorted_items]
percentages = [count / total * 100 for count in sizes]

# 凡例ラベル（参加者数と割合を表示）
legend_labels = [f'{label}: {size}人 ({pct:.1f}%)' for label, size, pct in zip(labels, sizes, percentages)]

# 日本語フォントの設定
plt.rcParams['font.family'] = ['Hiragino Sans', 'Hiragino Kaku Gothic ProN', 'DejaVu Sans', 'sans-serif']

# 統一カラーパレット
PALETTE = {
    'primary': '#2E86AB',    # メイン（青系）
    'secondary': '#4AB39A',  # サブ（ティール系）
    'tertiary': '#5BC48B',   # 補助（緑系）
    'accent': '#E07A5F',    # 強調（オレンジ系）
}
# 円グラフ用の色（4所属）
PIE_COLORS = ['#2E86AB', '#3D9AA2', '#4AB39A', '#5BC48B']

# 図のサイズを設定
fig, ax = plt.subplots(figsize=(10, 8))

# 円グラフを作成
colors = PIE_COLORS[:len(labels)]
wedges, texts, autotexts = ax.pie(
    sizes,
    labels=labels,
    autopct=lambda pct: f'{pct:.1f}%',
    startangle=90,
    counterclock=False,  # 時計回りに配置
    colors=colors,
    explode=[0.02] * len(labels),  # 各セクションを少し離す
    shadow=False
)

ax.set_title('所属別参加者数', fontsize=16, fontweight='bold')

# 凡例を追加（参加者数も表示）
ax.legend(
    legend_labels,
    loc='center left',
    bbox_to_anchor=(1, 0.5),
    fontsize=10
)

plt.tight_layout()
plt.savefig('所属別参加者数.png', dpi=150, bbox_inches='tight')
plt.close()

# ===== 棒グラフを作成（所属ごとの平均・最高・最低スコア） =====
dept_scores = defaultdict(list)
for row in rows:
    dept_scores[row['所属']].append(int(row['スコア']))

# 所属ごとに平均・最高・最低を計算（円グラフと同じ順序でソート）
dept_names = labels
dept_avg = [sum(dept_scores[d]) / len(dept_scores[d]) for d in dept_names]
dept_max = [max(dept_scores[d]) for d in dept_names]
dept_min = [min(dept_scores[d]) for d in dept_names]

fig2, ax2 = plt.subplots(figsize=(10, 6))
x = range(len(dept_names))
width = 0.5

# 棒グラフ：平均スコアのみ
bars = ax2.bar(x, dept_avg, width, label='平均スコア', color=PALETTE['primary'])

# 最高点・最低点は点で表示
ax2.scatter(x, dept_max, marker='^', s=80, color=PALETTE['accent'], zorder=5, label='最高点', edgecolors='#C25B45', linewidths=1.5)
ax2.scatter(x, dept_min, marker='v', s=80, color=PALETTE['secondary'], zorder=5, label='最低点', edgecolors='#3A8F7A', linewidths=1.5)

# 数値を表示
for i, (avg, mx, mn) in enumerate(zip(dept_avg, dept_max, dept_min)):
    # 平均点：棒グラフの下部に白色で表示
    ax2.annotate(f'{avg:.1f}', xy=(i, 10), xytext=(0, 0), textcoords='offset points',
                 ha='center', va='center', fontsize=9, fontweight='bold', color='white',
                 bbox=dict(boxstyle='round,pad=0.2', facecolor=PALETTE['primary'], edgecolor='none'))
    # 最高点：三角マーカーの真上に表示
    ax2.annotate(f'{mx}', xy=(i, mx), xytext=(0, 8), textcoords='offset points',
                 ha='center', va='bottom', fontsize=9, color='#C25B45')
    # 最低点：三角マーカーの真下に表示
    ax2.annotate(f'{mn}', xy=(i, mn), xytext=(0, -8), textcoords='offset points',
                 ha='center', va='top', fontsize=9, color='#2D6A7A')

ax2.set_xlabel('所属', fontsize=12)
ax2.set_ylabel('スコア', fontsize=12)
ax2.set_title('所属別スコア', fontsize=14, fontweight='bold')
ax2.set_xticks(x)
ax2.set_xticklabels(dept_names)
ax2.legend(loc='upper right')
# 余白を追加して数値がはみ出さないように
ax2.set_xlim(-0.7, len(dept_names) - 1 + 0.7)
ax2.set_ylim(0, 118)
plt.tight_layout(pad=1.5)
plt.savefig('所属別スコア.png', dpi=150, bbox_inches='tight', pad_inches=0.3)
plt.close()

# ===== ヒストグラムを作成（全参加者のスコア分布） =====
all_scores = [int(row['スコア']) for row in rows]
# ビン数：スコア範囲70-100、5点刻みで分布が把握しやすい
bins = range(70, 101, 5)  # 70-74, 75-79, 80-84, 85-89, 90-94, 95-99, 100

fig3, ax3 = plt.subplots(figsize=(10, 6))
n, bins_out, patches = ax3.hist(all_scores, bins=bins, color=PALETTE['primary'], edgecolor='white', linewidth=1.2)

# 平均スコアの基準線
avg_all = sum(all_scores) / len(all_scores)
ax3.axvline(x=avg_all, color=PALETTE['accent'], linestyle='--', linewidth=2, label=f'平均: {avg_all:.1f}点')

ax3.set_title('スコア分布', fontsize=14, fontweight='bold')
ax3.set_xlabel('スコア', fontsize=12)
ax3.set_ylabel('人数', fontsize=12)
ax3.legend(loc='upper right')
ax3.set_xlim(65, 105)
plt.tight_layout()
plt.savefig('スコア分布.png', dpi=150, bbox_inches='tight')
plt.close()

# コンソールにも集計結果を表示
print('\n=== 所属ごとの参加者数と割合 ===')
for label, size in zip(labels, sizes):
    pct = size / total * 100
    print(f'  {label}: {size}人 ({pct:.1f}%)')
print(f'\n合計: {total}人')
