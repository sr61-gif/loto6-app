import streamlit as st
import pandas as pd
import numpy as np
import itertools

st.title("🎯 自分専用ロト6予測アプリ")
st.write("直近50回のトレンド分析 ＆ 前回・前々回連動予測")

# 1. loto6.csvの読み込み
try:
    df = pd.read_csv('loto6.csv', encoding='shift_jis')
except:
    try:
        df = pd.read_csv('/loto6.csv', encoding='shift_jis')
    except:
        df = pd.read_csv('loto6.csv', encoding='utf-8')

# 大阪抽選除外リスト
osaka_rounds = [
    336, 353, 372, 404, 424, 455, 466, 475, 497, 505, 526, 537, 557, 558, 573, 574, 
    615, 616, 634, 635, 660, 661, 676, 677, 716, 717, 736, 737, 764, 765, 780, 781, 
    816, 817, 839, 840, 865, 866, 881, 882, 921, 922, 944, 945, 968, 969, 984, 985, 
    1024, 1025, 1049, 1050, 1071, 1072, 1089, 1090, 1127, 1128, 1152, 1153, 1186, 1187, 
    1194, 1195, 1228, 1229, 1249, 1250, 1297, 1298, 1329, 1330, 1351, 1352, 1399, 1400, 
    1419, 1420, 1421, 1422, 1449, 1450, 1523, 1524, 1636, 1637, 1705, 1706, 1721, 1722, 
    1768, 1769, 1808, 1809, 1842, 1843, 1867, 1868, 1916, 1937, 1938, 1970, 1971, 
    2012, 2013, 2040, 2041, 2081, 2082, 2117, 2118, 2143, 2144
]

df_filtered = df[~df['開催回'].isin(osaka_rounds)]
df_sorted = df_filtered.sort_values(by='開催回', ascending=False).reset_index(drop=True)
df_recent50 = df_sorted.head(50)

number_cols = ['第1数字', '第2数字', '第3数字', '第4数字', '第5数字', '第6数字']
draw_matrix = df_recent50[number_cols].values
last_draw = list(draw_matrix[0])
prev_draw = list(draw_matrix[1])

st.sidebar.markdown(f"**📌 前回:** 第{df_recent50.iloc[0]['開催回']}回 ({last_draw})")
st.sidebar.markdown(f"**📌 前々回:** 第{df_recent50.iloc[1]['開催回']}回 ({prev_draw})")

# スコアリング
latest_gap = {}
for num in range(1, 44):
    gap = 0
    for row in draw_matrix:
        if num in row:
            break
        gap += 1
    latest_gap[num] = gap

recent_30 = draw_matrix[:30].flatten()
counts_30 = {num: np.sum(recent_30 == num) for num in range(1, 44)}
scores = {num: (latest_gap[num] * 1.5) + (counts_30[num] * 2.0) for num in range(1, 44)}
top_candidates = sorted(scores, key=scores.get, reverse=True)

def generate_robust_combos(last_target, prev_target):
    valid_combos = []
    for combo in itertools.combinations(top_candidates, 6):
        combo_list = list(combo)
        if sum(1 for x in combo_list if x in last_draw) != last_target:
            continue
        if sum(1 for x in combo_list if x in prev_draw) != prev_target:
            continue
        total_score = sum(scores[n] for n in combo_list)
        valid_combos.append((total_score, sorted(combo_list)))
    valid_combos.sort(key=lambda x: x[0], reverse=True)
    return [item[1] for item in valid_combos[:3]]

if st.button("🚀 予測を実行する"):
    with st.spinner("分析中..."):
        combos_a = generate_robust_combos(1, 1)
        combos_b = generate_robust_combos(0, 1)
        combos_c = generate_robust_combos(1, 0)

    st.subheader("✨ パターン1：前回 1個 ＋ 前々回 1個")
    for i, c in enumerate(combos_a, 1):
        st.success(f"買い目 {i}: {c}")

    st.subheader("✨ パターン2（条件C）：前回 0個 ＋ 前々回 1個")
    for i, c in enumerate(combos_b, 1):
        st.success(f"買い目 {i}: {c}")

    st.subheader("✨ パターン3：前回 1個 ＋ 前々回 0個")
    for i, c in enumerate(combos_c, 1):
        st.success(f"買い目 {i}: {c}")