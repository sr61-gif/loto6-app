import itertools
import io
import numpy as np
import pandas as pd
import requests
import streamlit as st

st.set_page_config(page_title="ロト6項目別予測アプリ", layout="wide")

st.title("🎯 自分専用ロト6予測アプリ（項目別チョイス版）")
st.write("各アプローチから気になる数字をピックアップして組み合わせてみましょう！")

# Googleスプレッドシートの公開CSVリンク
sheet_id = "1YHr7GDC4SwgGPSZrJzk5gm5bgdjaW4BmGxGCm8w-UUg"
csv_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv"


@st.cache_data
def load_data():
  try:
    df = pd.read_csv(csv_url)
    return df
  except Exception as e:
    st.error(f"データの読み込みに失敗しました: {e}")
    return None


df = load_data()

if df is not None and not df.empty:
  # 大阪抽選除外リスト
  osaka_rounds = [
      336,
      353,
      372,
      404,
      424,
      455,
      466,
      475,
      497,
      505,
      526,
      537,
      557,
      558,
      573,
      574,
      615,
      616,
      634,
      635,
      660,
      661,
      676,
      677,
      716,
      717,
      736,
      737,
      764,
      765,
      780,
      781,
      816,
      817,
      839,
      840,
      865,
      866,
      881,
      882,
      921,
      922,
      944,
      945,
      968,
      969,
      984,
      985,
      1024,
      1025,
      1049,
      1050,
      1071,
      1072,
      1089,
      1090,
      1127,
      1128,
      1152,
      1153,
      1186,
      1187,
      1194,
      1195,
      1228,
      1229,
      1249,
      1250,
      1297,
      1298,
      1329,
      1330,
      1351,
      1352,
      1399,
      1400,
      1419,
      1420,
      1421,
      1422,
      1449,
      1450,
      1523,
      1524,
      1636,
      1637,
      1705,
      1706,
      1721,
      1722,
      1768,
      1769,
      1808,
      1809,
      1842,
      1843,
      1867,
      1868,
      1916,
      1937,
      1938,
      1970,
      1971,
      2012,
      2013,
      2040,
      2041,
      2081,
      2082,
      2117,
      2118,
      2143,
      2144,
  ]

  df_filtered = df[~df["開催回"].isin(osaka_rounds)]
  df_sorted = df_filtered.sort_values(
      by="開催回", ascending=False
  ).reset_index(drop=True)
  df_recent50 = df_sorted.head(50)

  number_cols = ["第1数字", "第2数字", "第3数字", "第4数字", "第5数字", "第6数字"]
  draw_matrix = df_recent50[number_cols].values
  last_draw = list(draw_matrix[0])
  prev_draw = list(draw_matrix[1])

  st.sidebar.title("最新データ情報")
  st.sidebar.markdown(
      f"**📌 前回:** 第{int(df_recent50.iloc[0]['開催回'])}回\n`{last_draw}`"
  )
  st.sidebar.markdown(
      f"**📌 前々回:** 第{int(df_recent50.iloc[1]['開催回'])}回\n`{prev_draw}`"
  )

  # 基本集計（ギャップ＆出現回数）
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

  # タブで項目ごとに切り替え
  tab1, tab2, tab3, tab4 = st.tabs([
      "🔥 総合トレンド",
      "🔄 引っ張り連動",
      "⚖️ バランス型（合計＆偶奇）",
      "🚀 ご無沙汰（穴狙い）",
  ])

  # --- 1. 総合トレンド ---
  with tab1:
    st.subheader("🔥 総合トレンド（出現数＆ギャップ評価）")
    st.caption("直近30回の出現頻度とハマリ度を総合的に計算した候補です。")
    scores_trend = {
        n: (latest_gap[n] * 1.5) + (counts_30[n] * 2.0) for n in range(1, 44)
    }
    top_trend = sorted(scores_trend, key=scores_trend.get, reverse=True)[:15]
    st.write(f"**注目上位15数字:** `{top_trend}`")

    if st.button("総合トレンドの予測を生成", key="btn_trend"):
      combos = []
      for combo in itertools.combinations(top_trend, 6):
        score = sum(scores_trend[n] for n in combo)
        combos.append((score, sorted(combo)))
      combos.sort(key=lambda x: x[0], reverse=True)

      for idx, (_, c) in enumerate(combos[:3], 1):
        st.success(f"買い目 {idx}: {c}")

  # --- 2. 引っ張り連動 ---
  with tab2:
    st.subheader("🔄 引っ張り連動（前回・前々回の数字を活用）")
    st.caption(
        "前回・前々回からそれぞれ数字が引かれる前提で絞り込みます。"
    )

    scores_base = {
        n: (latest_gap[n] * 1.5) + (counts_30[n] * 2.0) for n in range(1, 44)
    }
    top_cand = sorted(scores_base, key=scores_base.get, reverse=True)

    def gen_pull_combos(last_target, prev_target):
      res = []
      for combo in itertools.combinations(top_cand, 6):
        c_list = list(combo)
        if sum(1 for x in c_list if x in last_draw) != last_target:
          continue
        if sum(1 for x in c_list if x in prev_draw) != prev_target:
          continue
        s = sum(scores_base[n] for n in c_list)
        res.append((s, sorted(c_list)))
      res.sort(key=lambda x: x[0], reverse=True)
      return [item[1] for item in res[:2]]

    if st.button("引っ張り連動の予測を生成", key="btn_pull"):
      st.markdown("##### 🔹 パターンA：前回から1個 ＋ 前々回から1個")
      for i, c in enumerate(gen_pull_combos(1, 1), 1):
        st.info(f"買い目 {i}: {c}")

      st.markdown("##### 🔹 パターンB：前回から0個 ＋ 前々回から1個")
      for i, c in enumerate(gen_pull_combos(0, 1), 1):
        st.info(f"買い目 {i}: {c}")

      st.markdown("##### 🔹 パターンC：前回から1個 ＋ 前々回から0個")
      for i, c in enumerate(gen_pull_combos(1, 0), 1):
        st.info(f"買い目 {i}: {c}")

  # --- 3. バランス型 ---
  with tab3:
    st.subheader("⚖️ バランス厳選（合計値 100〜150 / 偶奇 2:4〜4:2）")
    st.caption(
        "極端な組み合わせを排除し、過去に最も当せん頻度が高い黄金バランスに絞り込みます。"
    )

    if st.button("バランス重視の予測を生成", key="btn_bal"):
      scores_bal = {
          n: (latest_gap[n] * 1.2) + (counts_30[n] * 2.0) for n in range(1, 44)
      }
      top_bal = sorted(scores_bal, key=scores_bal.get, reverse=True)[:18]

      valid_bal = []
      for combo in itertools.combinations(top_bal, 6):
        c_sum = sum(combo)
        evens = sum(1 for x in combo if x % 2 == 0)

        # 合計値 100〜150 かつ 偶数が2〜4個の範囲
        if 100 <= c_sum <= 150 and 2 <= evens <= 4:
          s = sum(scores_bal[n] for n in combo)
          valid_bal.append((s, sorted(combo), c_sum, evens))

      valid_bal.sort(key=lambda x: x[0], reverse=True)

      for idx, (_, c, c_sum, evens) in enumerate(valid_bal[:3], 1):
        st.success(
            f"買い目 {idx}: {c} （合計: {c_sum} / 偶数: {evens}個・奇数:"
            f" {6-evens}個）"
        )

  # --- 4. ご無沙汰（穴狙い） ---
  with tab4:
    st.subheader("🚀 ご無沙汰数字（長期間出ていないハマリ数字）")
    st.caption("最近出ていないギャップの大きい数字を中心にした穴狙いです。")

    # ギャップ（はまり度）順にソート
    gap_sorted = sorted(latest_gap.items(), key=lambda x: x[1], reverse=True)
    top_holes = [n for n, g in gap_sorted[:12]]
    st.write(f"**ハマリ数字トップ12:** `{top_holes}`")

    if st.button("ご無沙汰・穴狙いの予測を生成", key="btn_hole"):
      scores_hole = {n: latest_gap[n] for n in range(1, 44)}
      combos_hole = []
      for combo in itertools.combinations(top_holes, 6):
        s = sum(scores_hole[n] for n in combo)
        combos_hole.append((s, sorted(combo)))
      combos_hole.sort(key=lambda x: x[0], reverse=True)

      for idx, (_, c) in enumerate(combos_hole[:3], 1):
        st.warning(f"穴狙い買い目 {idx}: {c}")

else:
  st.warning(
      "データを読み込めませんでした。スプレッドシートの共有設定やURLを確認してください。"
  )
