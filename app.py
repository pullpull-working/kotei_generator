import streamlit as st
import pandas as pd
import re
from ortools.sat.python import cp_model
import json
import os

DATA_FILE = "bands.json"

def save_data():
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(st.session_state.bands, f, ensure_ascii=False, indent=2)

st.set_page_config(page_title="バンド割り当てアプリ", layout="wide")

st.title("バンド固定ジェネレータ")

# -------------------------
# 枠の定義（固定10枠）
# -------------------------
days = ["月", "火", "水", "木", "金"]
slots = ["前枠", "後枠"]
time_slots = [f"{d}_{s}" for d in days for s in slots]

# -------------------------
# セッション状態初期化（永続化対応）
# -------------------------
if "bands" not in st.session_state:
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            st.session_state.bands = json.load(f)
    else:
        st.session_state.bands = {}

# -------------------------
# バンド登録フォーム
# -------------------------
st.header("📌 バンド登録")

with st.form("band_form"):
    band_name = st.text_input("バンド名")
    members_input = st.text_input("メンバー 例: 22れみ,22しおり、22ぷる､22めい，22かっくん、22いっせい")

    ng_slots = st.multiselect(
        "参加できない枠（複数選択可）",
        time_slots
    )

    submitted = st.form_submit_button("登録")

    if submitted:
        if band_name and members_input:
            members = [m.strip() for m in re.split(r"[、,，､]", members_input) if m.strip()]
            st.session_state.bands[band_name] = {
                "members": members,
                "ng_slots": ng_slots
            }
            st.success(f"{band_name} を登録しました！")
            save_data()  # ←追加
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
                save_data()  # ←追加
                st.rerun()
else:
    st.info("まだバンドが登録されていません。")

# -------------------------
# OR-Tools 割り当て処理
# -------------------------
st.header("🚀 自動割り当て")

if st.button("割り当て実行"):

    bands = st.session_state.bands
    band_names = list(bands.keys())

    model = cp_model.CpModel()

    # 変数: x[(band, slot)] = 1ならその枠に配置
    x = {}
    for b in band_names:
        for s in time_slots:
            x[(b, s)] = model.NewBoolVar(f"x_{b}_{s}")

    # -------------------------
    # 制約1: 各バンドは高々1枠
    # -------------------------
    for b in band_names:
        model.Add(sum(x[(b, s)] for s in time_slots) <= 1)

    # -------------------------
    # 制約2: メンバー被り禁止
    # 同じ枠に同じメンバーが含まれるバンドは同時配置不可
    # -------------------------
    for s in time_slots:
        for i in range(len(band_names)):
            for j in range(i + 1, len(band_names)):
                b1 = band_names[i]
                b2 = band_names[j]

                if set(bands[b1]["members"]) & set(bands[b2]["members"]):
                    model.Add(x[(b1, s)] + x[(b2, s)] <= 1)

    # -------------------------
    # 制約3: 参加不可枠
    # -------------------------
    for b in band_names:
        for s in bands[b]["ng_slots"]:
            model.Add(x[(b, s)] == 0)

    # -------------------------
    # 目的関数: 配置バンド数を最大化
    # -------------------------
    model.Maximize(
        sum(x[(b, s)] for b in band_names for s in time_slots)
    )

    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = 10

    status = solver.Solve(model)

    slot_assignments = {s: [] for s in time_slots}
    unassigned = []

    if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):

        for b in band_names:
            assigned = False
            for s in time_slots:
                if solver.Value(x[(b, s)]) == 1:
                    slot_assignments[s].append(b)
                    assigned = True
            if not assigned:
                unassigned.append(b)

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