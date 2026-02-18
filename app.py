import streamlit as st
import pandas as pd
from collections import defaultdict

st.set_page_config(page_title="バンド割り当てアプリ", layout="wide")

st.title("固定ジェネレーター")

# -------------------------
# 枠の定義（固定10枠）
# -------------------------
days = ["月", "火", "水", "木", "金"]
slots = ["前枠", "後枠"]
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
    members_input = st.text_input("メンバー（カンマ区切り）例: 22ぷる,22めい,22かっくん,22いっせい,22しおり,22れみ")
    
    ng_slots = st.multiselect(
        "参加できない枠（複数選択可）",
        time_slots
    )

    submitted = st.form_submit_button("登録")

    if submitted:
        if band_name and members_input:
            members = [m.strip() for m in members_input.split(",") if m.strip()]
            st.session_state.bands[band_name] = {
                "members": members,
                "ng_slots": ng_slots
            }
            st.success(f"{band_name} を登録しました！")
        else:
            st.error("バンド名とメンバーを入力してください。")

# -------------------------
# 登録済みバンド表示 + 削除機能
# -------------------------
st.header("📋 登録済みバンド")

if st.session_state.bands:

    for band_name, data in list(st.session_state.bands.items()):
        col1, col2, col3, col4 = st.columns([2, 4, 3, 1])

        with col1:
            st.write(f"**{band_name}**")

        with col2:
            st.write(", ".join(data["members"]))

        with col3:
            if data["ng_slots"]:
                st.write("❌ " + ", ".join(data["ng_slots"]))
            else:
                st.write("制限なし")

        with col4:
            if st.button("🗑", key=f"delete_{band_name}"):
                del st.session_state.bands[band_name]
                st.rerun()

else:
    st.info("まだバンドが登録されていません。")

# -------------------------
# 割り当て処理
# -------------------------
st.header("🚀 自動割り当て")

if st.button("割り当て実行"):

    bands = st.session_state.bands.copy()

    slot_members = {slot: set() for slot in time_slots}
    slot_assignments = defaultdict(list)

    # 制約が強い順に並べる
    sorted_bands = sorted(
        bands.items(),
        key=lambda x: (len(x[1]["members"]), len(x[1]["ng_slots"])),
        reverse=True
    )

    unassigned = []

    for band_name, data in sorted_bands:
        members = data["members"]
        ng = data["ng_slots"]
        placed = False

        for slot in time_slots:

            # 参加不可枠チェック
            if slot in ng:
                continue

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

    if unassigned:
        st.warning("⚠ 割り当て不可:")
        st.write(", ".join(unassigned))
    else:
        st.success("✅ すべてのバンドを割り当てました！")
