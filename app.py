import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

from inventory import search_part, issue_part, restock_part, add_new_part
from recommendation import generate_recommendations, apply_recommendations
from data_handler import load_parts, load_usage_log, load_restock_log
from scoring import calculate_scores


st.set_page_config(page_title="Warehouse System", layout="wide")
st.title("📦 Intelligent Warehouse Management System")


# ── session defaults ──────────────────────────────────────────────────────────
if "active_tab" not in st.session_state:
    st.session_state["active_tab"] = 0

if "message" not in st.session_state:
    st.session_state["message"] = None


# ── global message banner ─────────────────────────────────────────────────────
if st.session_state["message"]:
    msg_type = st.session_state.get("message_type", "info")
    if msg_type == "success":
        st.success(st.session_state["message"])
    elif msg_type == "error":
        st.error(st.session_state["message"])
    else:
        st.info(st.session_state["message"])
    st.session_state["message"] = None


# ── navigation ────────────────────────────────────────────────────────────────
tabs = ["Dashboard", "Search & Issue", "Add / Restock", "Recommendations", "Analytics"]

selected_tab = st.radio(
    "Navigation",
    tabs,
    index=st.session_state["active_tab"],
    horizontal=True,
)
st.session_state["active_tab"] = tabs.index(selected_tab)


# ══════════════════════════════════════════════════════════════════════════════
# DASHBOARD
# ══════════════════════════════════════════════════════════════════════════════
if selected_tab == "Dashboard":
    df = load_parts()

    st.subheader("⚠️ Low Stock Alerts")
    if df.empty:
        st.info("No parts in the system yet.")
    else:
        low_stock = df[pd.to_numeric(df["count"], errors="coerce") <
                       pd.to_numeric(df["threshold"], errors="coerce")]
        if low_stock.empty:
            st.success("All stock levels are sufficient")
        else:
            st.dataframe(low_stock)

    st.subheader("🔝 Top Used Parts")
    if df.empty:
        st.info("No parts in the system yet.")
    else:
        top_parts = df.sort_values(by="frequency", ascending=False).head(5)
        st.dataframe(top_parts)


# ══════════════════════════════════════════════════════════════════════════════
# SEARCH & ISSUE
# ══════════════════════════════════════════════════════════════════════════════
elif selected_tab == "Search & Issue":
    st.subheader("🔍 Search & Issue Part")

    df = load_parts()

    if df.empty:
        st.info("No parts in the system yet. Add parts first.")
    else:
        df["display"] = df["part_id"] + " - " + df["name"]
        selected = st.selectbox("Select Part", df["display"].tolist())

        if selected:
            part_id = selected.split(" - ")[0]
            result  = search_part(part_id)

            if result is not None:
                st.success("Part Found")
                st.write(result)

                qty = st.number_input("Enter Quantity to Issue", min_value=1)

                if st.button("Issue Part"):
                    msg = issue_part(part_id, qty)
                    st.session_state["message"]      = msg
                    st.session_state["message_type"] = "success"
                    st.session_state["active_tab"]   = 1
                    st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# ADD / RESTOCK
# ══════════════════════════════════════════════════════════════════════════════
elif selected_tab == "Add / Restock":
    st.subheader("📥 Add / Restock Part")

    option = st.radio("Choose Action", ["Add New Part", "Restock Part"])

    # ── Add New Part ──────────────────────────────────────────────────────────
    if option == "Add New Part":
        part_id   = st.text_input("Part ID (e.g. ENG003)")
        name      = st.text_input("Part Name")
        count     = st.number_input("Initial Stock Count", min_value=0, step=1)
        threshold = st.number_input("Low Stock Threshold", min_value=0, step=1)
        location  = st.text_input("Location (e.g. R1-S1-B1)")

        movement_type_options = ["None (classify later)", "Fast", "Slow", "Rare"]
        movement_type_sel     = st.selectbox("Movement Type", movement_type_options)
        st.caption("Select 'None' if unknown — the system will classify it automatically once log data is available.")
        movement_type = "" if movement_type_sel == "None (classify later)" else movement_type_sel

        if st.button("Add Part"):
            if not part_id.strip():
                st.error("Please enter a Part ID.")
            else:
                msg = add_new_part(
                    part_id.strip().upper(),
                    name,
                    count,
                    threshold,
                    movement_type,
                    location,
                )
                st.session_state["message"]      = msg
                st.session_state["message_type"] = "success" if "successfully" in msg else "error"
                st.session_state["active_tab"]   = 2
                st.rerun()

    # ── Restock Part ──────────────────────────────────────────────────────────
    else:
        df = load_parts()

        if df.empty:
            st.info("No parts in the system yet. Add parts first.")
        else:
            df["display"] = df["part_id"] + " - " + df["name"]
            selected      = st.selectbox("Select Part to Restock", df["display"].tolist())

            if selected:
                part_id = selected.split(" - ")[0]
                qty     = st.number_input("Quantity", min_value=1)

                if st.button("Restock"):
                    msg = restock_part(part_id, qty)
                    st.session_state["message"]      = msg
                    st.session_state["message_type"] = "success"
                    st.session_state["active_tab"]   = 2
                    st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# RECOMMENDATIONS
# ══════════════════════════════════════════════════════════════════════════════
elif selected_tab == "Recommendations":
    st.subheader("🔍 Rearrangement Suggestions")

    if st.button("Recommend Arrangement"):
        recommendations, current_ranks = generate_recommendations()
        st.session_state["current_ranks"]   = current_ranks
        st.session_state["recommendations"] = recommendations

    if "recommendations" in st.session_state:
        recommendations = st.session_state["recommendations"]

        if not recommendations:
            st.info("✅ No rearrangement needed — all parts are already optimally placed")
            del st.session_state["recommendations"]
            del st.session_state["current_ranks"]
        else:
            df_rec = pd.DataFrame(recommendations)
            df_rec.index = range(1, len(df_rec) + 1)
            st.dataframe(
                df_rec[[
                    "part_id",
                    "name",
                    "current_location",
                    "old_rank",
                    "new_rank",
                    "direction"
                ]],
                use_container_width=True
            )

    if "recommendations" in st.session_state and st.session_state.get("recommendations"):
        if st.button("Apply Changes"):
            msg = apply_recommendations(st.session_state["current_ranks"])
            st.session_state["message"]      = msg
            st.session_state["message_type"] = "success"
            st.session_state["active_tab"]   = 3
            del st.session_state["recommendations"]
            del st.session_state["current_ranks"]
            st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# ANALYTICS
# ══════════════════════════════════════════════════════════════════════════════
elif selected_tab == "Analytics":
    st.subheader("📊 Usage & Stock Analysis")

    parts_df   = load_parts()
    usage_df   = load_usage_log()
    restock_df = load_restock_log()

    # Normalise dates
    if not usage_df.empty:
        usage_df["date"]  = pd.to_datetime(usage_df["date"])
        usage_df["month"] = usage_df["date"].dt.to_period("M").astype(str)

    if not restock_df.empty:
        restock_df["date"]  = pd.to_datetime(restock_df["date"])
        restock_df["month"] = restock_df["date"].dt.to_period("M").astype(str)

    a1, a2, a3, a4 = st.tabs([
        "📈 Monthly Usage",
        "📦 Restock / Purchases",
        "🗺️ Warehouse Map",
        "❤️ Stock Health",
    ])

    # ═════════════════════════════════════════════════════════════════════════
    # TAB 1 — Monthly Usage Trend
    # ═════════════════════════════════════════════════════════════════════════
    with a1:
        if usage_df.empty:
            st.info("📭 No usage data yet. Issue some parts to see the trend.")
        else:
            monthly = (
                usage_df.groupby(["month", "part_id"])["quantity"]
                .sum()
                .reset_index()
            )
            monthly = monthly.merge(
                parts_df[["part_id", "name", "movement_type"]],
                on="part_id", how="left"
            )
            monthly["movement_type"] = monthly["movement_type"].fillna("")
            monthly["label"]         = monthly["part_id"] + " - " + monthly["name"]

            view_mode = st.radio("View by", ["Movement Group", "Custom Selection"], horizontal=True)

            if view_mode == "Movement Group":
                group    = st.selectbox("Select movement group", ["Fast", "Slow", "Rare"])
                filtered = monthly[monthly["movement_type"] == group]

                if filtered.empty:
                    st.info(f"📭 No usage data for '{group}' parts yet.")
                else:
                    fig = px.line(
                        filtered, x="month", y="quantity", color="label",
                        markers=True, title=f"{group} Moving Parts — Monthly Usage"
                    )
                    fig.update_layout(
                        plot_bgcolor="#1E1E1E", paper_bgcolor="#1E1E1E",
                        font=dict(color="white"), height=400, legend=dict(x=1, y=1)
                    )
                    st.plotly_chart(fig, use_container_width=True)

            else:
                top5 = (
                    monthly.groupby("part_id")["quantity"]
                    .sum().sort_values(ascending=False).head(5).index.tolist()
                )
                all_labels = monthly["label"].unique().tolist()
                default    = monthly[monthly["part_id"].isin(top5)]["label"].unique().tolist()
                selected   = st.multiselect("Select parts", all_labels, default=default)
                filtered   = monthly[monthly["label"].isin(selected)]

                if filtered.empty:
                    st.info("Select parts to display the trend.")
                else:
                    fig = px.line(
                        filtered, x="month", y="quantity", color="label",
                        markers=True, title="Custom Usage Trend"
                    )
                    fig.update_layout(
                        plot_bgcolor="#1E1E1E", paper_bgcolor="#1E1E1E",
                        font=dict(color="white"), height=400, legend=dict(x=1, y=1)
                    )
                    st.plotly_chart(fig, use_container_width=True)

            # Overall monthly bar
            st.markdown("---")
            overall = usage_df.groupby("month")["quantity"].sum().reset_index()
            fig2    = px.bar(overall, x="month", y="quantity", title="Total Monthly Usage")
            fig2.update_layout(
                plot_bgcolor="#1E1E1E", paper_bgcolor="#1E1E1E",
                font=dict(color="white"), height=300
            )
            st.plotly_chart(fig2, use_container_width=True)

    # ═════════════════════════════════════════════════════════════════════════
    # TAB 2 — Restock / Purchase Analytics
    # ═════════════════════════════════════════════════════════════════════════
    with a2:
        if restock_df.empty:
            st.info("📭 No restock or purchase data yet. Add or restock parts to see this chart.")
        else:
            restock_merged = restock_df.merge(
                parts_df[["part_id", "name"]], on="part_id", how="left"
            )
            restock_merged["label"] = restock_merged["part_id"] + " - " + restock_merged["name"].fillna("Unknown")

            # ── Summary metrics ───────────────────────────────────────────
            total_purchased = restock_merged[restock_merged["type"] == "New Part"]["quantity"].sum()
            total_restocked = restock_merged[restock_merged["type"] == "Restock"]["quantity"].sum()
            total_events    = len(restock_merged)

            m1, m2, m3 = st.columns(3)
            m1.metric("🆕 Units Added (New Parts)", int(total_purchased))
            m2.metric("🔄 Units Restocked",         int(total_restocked))
            m3.metric("📋 Total Events",            total_events)

            st.markdown("---")

            # ── Monthly totals bar (split by type) ───────────────────────
            monthly_restock = (
                restock_merged.groupby(["month", "type"])["quantity"]
                .sum().reset_index()
            )
            fig_r1 = px.bar(
                monthly_restock, x="month", y="quantity", color="type",
                barmode="group",
                title="Monthly Inbound Stock (New Parts vs Restocks)",
                color_discrete_map={"New Part": "#6366F1", "Restock": "#16A34A"}
            )
            fig_r1.update_layout(
                plot_bgcolor="#1E1E1E", paper_bgcolor="#1E1E1E",
                font=dict(color="white"), height=350, legend=dict(x=1, y=1)
            )
            st.plotly_chart(fig_r1, use_container_width=True)

            # ── Per-part restock breakdown ────────────────────────────────
            st.markdown("##### Restock / Purchase by Part")
            part_restock = (
                restock_merged.groupby(["label", "type"])["quantity"]
                .sum().reset_index()
            )
            fig_r2 = px.bar(
                part_restock, x="quantity", y="label", color="type",
                orientation="h", barmode="stack",
                title="Total Units Received per Part",
                color_discrete_map={"New Part": "#6366F1", "Restock": "#16A34A"}
            )
            fig_r2.update_layout(
                plot_bgcolor="#1E1E1E", paper_bgcolor="#1E1E1E",
                font=dict(color="white"), height=max(300, len(part_restock) * 28),
                legend=dict(x=1, y=1)
            )
            st.plotly_chart(fig_r2, use_container_width=True)

            # ── Raw log table ─────────────────────────────────────────────
            with st.expander("📋 View Raw Restock Log"):
                st.dataframe(
                    restock_merged[["date", "part_id", "name", "quantity", "type"]]
                    .sort_values("date", ascending=False)
                    .reset_index(drop=True),
                    use_container_width=True,
                )

    # ═════════════════════════════════════════════════════════════════════════
    # TAB 3 — Warehouse Location Map
    # ═════════════════════════════════════════════════════════════════════════
    with a3:
        st.markdown("##### Physical Warehouse Layout")

        st.markdown("""
<div style="
    display:flex;
    gap:20px;
    margin-bottom:15px;
    flex-wrap:wrap;
">

<div style="display:flex;align-items:center;gap:8px;">
    <div style="
        width:18px;
        height:18px;
        background:#16A34A;
        border-radius:4px;
    "></div>
    <span>Fast Moving</span>
</div>

<div style="display:flex;align-items:center;gap:8px;">
    <div style="
        width:18px;
        height:18px;
        background:#D97706;
        border-radius:4px;
    "></div>
    <span>Slow Moving</span>
</div>

<div style="display:flex;align-items:center;gap:8px;">
    <div style="
        width:18px;
        height:18px;
        background:#6B7280;
        border-radius:4px;
    "></div>
    <span>Rare Moving</span>
</div>

<div style="display:flex;align-items:center;gap:8px;">
    <div style="
        width:18px;
        height:18px;
        background:#CBD5E1;
        border-radius:4px;
    "></div>
    <span>Movement Type Not Classified</span>
</div>

</div>
""", unsafe_allow_html=True)

        if parts_df.empty:
            st.info("📭 No parts available.")
        else:

            df_map = parts_df.copy()

            # Clean location
            df_map["location"] = (
                df_map["location"]
                .astype(str)
                .str.upper()
                .str.strip()
            )

            # Sort by real warehouse location
            df_map = df_map.sort_values("location")

            # Color mapping
            color_map = {
                "Fast": "#16A34A",
                "Slow": "#D97706",
                "Rare": "#6B7280",
                "": "#1571E2"
            }

            # Create rows of 4 cards each
            cols_per_row = 4

            for i in range(0, len(df_map), cols_per_row):

                cols = st.columns(cols_per_row)

                chunk = df_map.iloc[i:i + cols_per_row]

                for col, (_, row) in zip(cols, chunk.iterrows()):

                    movement_type = str(
                        row.get("movement_type", "")
                    ).strip()

                    color = color_map.get(
                        movement_type,
                        "#CBD5E1"
                    )

                    col.markdown(
                        f'''
                        <div style="
                            background:{color};
                            padding:14px;
                            border-radius:10px;
                            border:1px solid #D1D5DB;
                            min-height:130px;
                            color:white;
                            margin-bottom:12px;
                        ">

                        <div style="
                            font-size:15px;
                            font-weight:700;
                            margin-bottom:8px;
                        ">
                            {row["location"]}
                        </div>

                        <div style="font-size:13px;">
                            <b>{row["part_id"]}</b>
                        </div>

                        <div style="
                            font-size:12px;
                            margin-top:4px;
                        ">
                            {row["name"]}
                        </div>

                        <hr style="margin:8px 0;">

                        <div style="font-size:12px;">
                            Stock: {row["count"]}
                        </div>

                        <div style="font-size:12px;">
                            Rank: {row["previous_rank"]}
                        </div>

                        <div style="font-size:12px;">
                            Type: {movement_type if movement_type else "Movement type not classified"}
                        </div>

                        </div>
                        ''',
                        unsafe_allow_html=True
                    )
    # ═════════════════════════════════════════════════════════════════════════
    # TAB 4 — Stock Health
    # ═════════════════════════════════════════════════════════════════════════
    with a4:
        st.markdown("##### Stock level vs threshold for every part")

        if parts_df.empty:
            st.info("📭 No parts in the system yet.")
        else:
            df_health = parts_df.copy()
            df_health["count"]     = pd.to_numeric(df_health["count"],     errors="coerce").fillna(0).astype(int)
            df_health["threshold"] = pd.to_numeric(df_health["threshold"], errors="coerce").fillna(0).astype(int)

            df_health["ratio"] = df_health.apply(
                lambda r: r["count"] / r["threshold"] if r["threshold"] > 0 else 1.0, axis=1
            )

            def health_label(ratio):
                if ratio < 1.0:   return "🔴 Critical"
                elif ratio < 1.5: return "🟡 Low"
                else:             return "🟢 Healthy"

            df_health["status"] = df_health["ratio"].apply(health_label)

            critical = (df_health["status"] == "🔴 Critical").sum()
            low      = (df_health["status"] == "🟡 Low").sum()
            healthy  = (df_health["status"] == "🟢 Healthy").sum()

            c1, c2, c3 = st.columns(3)
            c1.metric("🔴 Critical", critical, help="Stock below threshold")
            c2.metric("🟡 Low",      low,       help="Stock within 1.5× threshold")
            c3.metric("🟢 Healthy",  healthy,   help="Stock well above threshold")

            st.markdown("<br>", unsafe_allow_html=True)

            status_filter = st.selectbox(
                "Filter by status", ["All", "🔴 Critical", "🟡 Low", "🟢 Healthy"]
            )
            if status_filter != "All":
                df_health = df_health[df_health["status"] == status_filter]

            df_health = df_health.sort_values("ratio")

            for _, row in df_health.iterrows():
                ratio     = min(row["ratio"], 3.0)
                pct       = ratio / 3.0
                status    = row["status"]

                if "Critical" in status:
                    bar_color, bg_color = "#DC2626", "#FEF2F2"
                elif "Low" in status:
                    bar_color, bg_color = "#D97706", "#FFFBEB"
                else:
                    bar_color, bg_color = "#16A34A", "#F0FDF4"

                mtype = str(row.get("movement_type", "") or "–")

                st.markdown(
                    f"""<div style="background:{bg_color};border-radius:8px;
                                padding:12px 16px;margin-bottom:10px;
                                border:1px solid #E2E8F0;">
                        <div style="display:flex;justify-content:space-between;
                                    align-items:center;margin-bottom:6px;">
                            <span style="font-weight:600;font-size:14px;">
                                {row["part_id"]} — {row["name"]}</span>
                            <span style="font-size:13px;">{status} &nbsp;|&nbsp;
                                {row["count"]} / {row["threshold"]} &nbsp;|&nbsp;
                                <em>{mtype}</em></span>
                        </div>
                        <div style="background:#E2E8F0;border-radius:4px;height:10px;">
                            <div style="background:{bar_color};width:{pct*100:.1f}%;
                                        height:10px;border-radius:4px;"></div>
                        </div>
                    </div>""",
                    unsafe_allow_html=True,
                )