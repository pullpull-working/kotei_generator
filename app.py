import streamlit as st
import pandas as pd
from collections import defaultdict

st.set_page_config(page_title="バンド割り当てアプリ", layout="wide")

st.title("🎸 バンド時間割 自動割り当てアプリ")

# -------------------------
# 枠の定義（固定10枠）
# -------------------------
days = ["月", "火", "水", "木", "金"]
slots = ["前半", "後半"]
time_slots = [f"{d}_{s}" for d in days for s in slots]

# -------------------------
# セッション状態初期化
# -------------------------
if "bands" not in st.session_state:
    st.session_state.bands = {}

# -------------------------
# バンド登録フォーム
# -------------------------
st.header("📌 バンド登録")

with st.form("band_form"):
    band_name = st.text_input("バンド名")
    members_input = st.text_input("メンバー（カンマ区切り）例: 田中,佐藤,鈴木")
    submitted = st.form_submit_button("登録")

    if submitted:
        if band_name and members_input:
            members = [m.strip() for m in members_input.split(",") if m.strip()]
            st.session_state.bands[band_name] = members
            st.success(f"{band_name} を登録しました！")
        else:
            st.error("バンド名とメンバーを入力してください。")

# -------------------------
# 登録済みバンド表示
# -------------------------
st.header("📋 登録済みバンド")

if st.session_state.bands:
    df_bands = pd.DataFrame(
        [(name, ", ".join(members)) for name, members in st.session_state.bands.items()],
        columns=["バンド名", "メンバー"]
    )
    st.dataframe(df_bands, use_container_width=True)
else:
    st.info("まだバンドが登録されていません。")

# -------------------------
# 割り当て処理
# -------------------------
st.header("🚀 自動割り当て")

if st.button("割り当て実行"):

    bands = st.session_state.bands.copy()

    # 枠ごとのメンバー使用状況
    slot_members = {slot: set() for slot in time_slots}
    slot_assignments = defaultdict(list)

    # メンバー数が多い順にソート（制約強いもの優先）
    sorted_bands = sorted(bands.items(), key=lambda x: len(x[1]), reverse=True)

    unassigned = []

    for band_name, members in sorted_bands:
        placed = False

        for slot in time_slots:
            # メンバー被りチェック
            if not set(members) & slot_members[slot]:
                slot_assignments[slot].append(band_name)
                slot_members[slot].update(members)
                placed = True
                break

        if not placed:
            unassigned.append(band_name)

    # -------------------------
    # 結果表示
    # -------------------------
    st.subheader("📅 割り当て結果")

    result_data = []
    for day in days:
        row = {}
        for s in slots:
            slot_key = f"{day}_{s}"
            row[s] = ", ".join(slot_assignments[slot_key])
        result_data.append(row)

    df_result = pd.DataFrame(result_data, index=days)
    st.dataframe(df_result, use_container_width=True)

    # 未割り当て表示
    if unassigned:
        st.warning("⚠ 割り当て不可:")
        st.write(", ".join(unassigned))
    else:
        st.success("✅ すべてのバンドを割り当てました！")
