"""
Beer Route Optimizer — Interactive Planning Demo
Main Streamlit application with 3-phase game flow.
"""

import math
import time

import streamlit as st
from streamlit_folium import st_folium

from beer_route_optimizer.data import (
    BREWERIES, WAREHOUSES, VENUES, COLORS, WAREHOUSE_COLORS,
)
from beer_route_optimizer.utils import (
    assign_venues_to_nearest,
    build_routes_nearest_neighbor,
    haversine,
)
from beer_route_optimizer.scoring import (
    get_full_cost_breakdown,
    check_capacity,
    calc_warehouse_cost,
)
from beer_route_optimizer.optimizer import optimize
from beer_route_optimizer.map_builder import (
    build_phase1_map,
    build_phase2_map_with_routes,
    build_phase3_map,
    _make_warehouse_colors,
)

# --- Page config (must be first Streamlit call) ---
st.set_page_config(
    page_title="\U0001f37a Duvel Route Planner",
    page_icon="\U0001f37a",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- Custom CSS ---
st.markdown("""
<style>
    /* Global */
    .stApp {
        background-color: #FAFAFA;
    }
    /* Sidebar */
    section[data-testid="stSidebar"] {
        background-color: #FAF7F2;
    }
    section[data-testid="stSidebar"] h1,
    section[data-testid="stSidebar"] h2,
    section[data-testid="stSidebar"] h3 {
        color: #1B3A5C;
    }
    /* Phase indicator */
    .phase-indicator {
        display: flex;
        justify-content: center;
        gap: 8px;
        margin-bottom: 1rem;
        align-items: center;
    }
    .phase-step {
        display: flex;
        align-items: center;
        gap: 6px;
        padding: 8px 16px;
        border-radius: 20px;
        font-size: 0.9rem;
        font-weight: 500;
    }
    .phase-active {
        background-color: #E8923C;
        color: white;
    }
    .phase-done {
        background-color: #2B9E8F;
        color: white;
    }
    .phase-upcoming {
        background-color: #E0E0E0;
        color: #888;
    }
    .phase-arrow {
        color: #CCC;
        font-size: 1.2rem;
    }
    /* Reveal box */
    .reveal-box {
        background: linear-gradient(135deg, #1B3A5C 0%, #2B4A6C 100%);
        color: white;
        padding: 2rem;
        border-radius: 12px;
        margin-top: 1.5rem;
    }
    .reveal-box h3 {
        color: #E8923C !important;
        margin-top: 0;
    }
    .reveal-box a {
        color: #E8923C;
        font-weight: bold;
    }
    /* Metric cards */
    div[data-testid="stMetric"] {
        background-color: white;
        padding: 12px;
        border-radius: 8px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.08);
    }
    /* Legend styling */
    .legend-item {
        display: inline-flex;
        align-items: center;
        gap: 4px;
        margin-right: 16px;
        font-size: 0.85rem;
    }
    .legend-dot {
        width: 12px;
        height: 12px;
        border-radius: 50%;
        display: inline-block;
    }
</style>
""", unsafe_allow_html=True)


# --- Session state initialization ---
_defaults = {
    "phase": 1,
    "selected_warehouse_ids": [],
    "assignments": {},
    "user_routes": {},
    "user_cost": None,
    "optimizer_result": None,
    "show_optimizer": False,
}
for _key, _val in _defaults.items():
    if _key not in st.session_state:
        st.session_state[_key] = _val


# --- Helper functions ---
@st.cache_data
def get_venues():
    return list(VENUES)

@st.cache_data
def get_warehouses():
    return list(WAREHOUSES)

@st.cache_data
def get_breweries():
    return list(BREWERIES)

@st.cache_data
def get_total_demand():
    return sum(v["demand"] for v in VENUES)


def get_selected_warehouses():
    """Get warehouse dicts for selected IDs."""
    return [wh for wh in WAREHOUSES if wh["id"] in st.session_state.selected_warehouse_ids]


def render_phase_indicator(current_phase):
    """Render the 3-step phase progress indicator."""
    labels = ["1. Place Warehouses", "2. Plan Routes", "3. Results"]
    parts = []
    for i, label in enumerate(labels):
        phase_num = i + 1
        if phase_num < current_phase:
            cls = "phase-done"
            icon = "\u2705"
        elif phase_num == current_phase:
            cls = "phase-active"
            icon = "\u25B6"
        else:
            cls = "phase-upcoming"
            icon = "\u25CB"
        parts.append(f'<span class="phase-step {cls}">{icon} {label}</span>')
        if i < 2:
            parts.append('<span class="phase-arrow">\u2192</span>')
    st.markdown(f'<div class="phase-indicator">{"".join(parts)}</div>', unsafe_allow_html=True)


def render_legend_urgency():
    """Render urgency color legend."""
    st.markdown(
        '<div>'
        f'<span class="legend-item"><span class="legend-dot" style="background:{COLORS["red"]}"></span> Urgent (stock &lt; 2)</span>'
        f'<span class="legend-item"><span class="legend-dot" style="background:{COLORS["yellow"]}"></span> Low (stock &lt; 4)</span>'
        f'<span class="legend-item"><span class="legend-dot" style="background:{COLORS["green"]}"></span> OK (stock \u2265 4)</span>'
        '</div>',
        unsafe_allow_html=True,
    )


# --- Sidebar ---
with st.sidebar:
    st.markdown(f"### \U0001f37a Duvel Route Planner")
    st.caption("Interactive logistics planning demo")
    st.divider()

    if st.button("\U0001f504 Start over"):
        for key in _defaults:
            st.session_state[key] = _defaults[key]
        st.rerun()


# --- Phase indicator ---
render_phase_indicator(st.session_state.phase)


# ============================================================
# PHASE 1: Warehouse Placement
# ============================================================
if st.session_state.phase == 1:
    st.markdown("## \U0001f3ed Place your warehouses")
    st.markdown(
        f"Choose **3 warehouse locations** from 8 candidates to serve {len(VENUES)} venues "
        f"with a total weekly demand of **{get_total_demand()} pallets**."
    )

    # Sidebar controls
    with st.sidebar:
        st.markdown("#### Select 3 warehouses")
        wh_options = {wh["name"]: wh["id"] for wh in WAREHOUSES}
        selected_names = st.multiselect(
            "Warehouse locations",
            options=list(wh_options.keys()),
            default=[
                name for name, wid in wh_options.items()
                if wid in st.session_state.selected_warehouse_ids
            ],
            max_selections=3,
        )
        st.session_state.selected_warehouse_ids = [wh_options[n] for n in selected_names]

        # Show selected warehouse stats
        if selected_names:
            selected_whs = get_selected_warehouses()
            total_cap = sum(wh["capacity"] for wh in selected_whs)
            total_cost = sum(wh["weekly_cost"] for wh in selected_whs)

            st.markdown("---")
            st.markdown("**Selected warehouses:**")
            for wh in selected_whs:
                st.markdown(f"- **{wh['name']}**: \u20ac{wh['weekly_cost']:,}/wk, {wh['capacity']} pallets")

            st.metric("Total capacity", f"{total_cap} pallets")
            st.metric("Total warehouse cost", f"\u20ac{total_cost:,}/week")

            if total_cap < get_total_demand():
                st.error(
                    f"\u26a0\ufe0f Capacity shortfall: {total_cap} < {get_total_demand()} pallets needed. "
                    f"You're short by {get_total_demand() - total_cap} pallets."
                )

        # Confirm button
        st.markdown("---")
        can_confirm = len(st.session_state.selected_warehouse_ids) == 3
        if can_confirm:
            selected_whs = get_selected_warehouses()
            total_cap = sum(wh["capacity"] for wh in selected_whs)
            can_confirm = total_cap >= get_total_demand()

        if st.button("\u2705 Confirm warehouses", disabled=not can_confirm):
            selected_whs = get_selected_warehouses()
            assignments = assign_venues_to_nearest(VENUES, selected_whs)
            st.session_state.assignments = assignments
            st.session_state.phase = 2
            st.rerun()

        if not can_confirm and len(st.session_state.selected_warehouse_ids) == 3:
            st.warning("Total capacity must meet or exceed total demand.")
        elif len(st.session_state.selected_warehouse_ids) < 3:
            st.info(f"Select {3 - len(st.session_state.selected_warehouse_ids)} more warehouse(s).")

    # Main content: map
    col1, col2 = st.columns([3, 1])
    with col1:
        m = build_phase1_map(BREWERIES, VENUES, WAREHOUSES)
        st_folium(m, width=900, height=550, returned_objects=[], key="phase1_map")
    with col2:
        render_legend_urgency()
        st.markdown("---")
        st.markdown("**Candidate warehouses:**")
        for wh in WAREHOUSES:
            marker = "\u2705" if wh["id"] in st.session_state.selected_warehouse_ids else "\u25CB"
            st.markdown(
                f"{marker} **{wh['name']}** — \u20ac{wh['weekly_cost']:,}/wk, "
                f"{wh['capacity']}p"
            )


# ============================================================
# PHASE 2: Route Planning
# ============================================================
elif st.session_state.phase == 2:
    st.markdown("## \U0001f69a Plan your routes")
    st.markdown("Assign venues to warehouses and review routes. Reassign venues if needed.")

    selected_whs = get_selected_warehouses()
    wh_colors = _make_warehouse_colors(selected_whs)
    wh_lookup = {wh["id"]: wh for wh in selected_whs}
    wh_name_to_id = {wh["name"]: wh["id"] for wh in selected_whs}
    wh_id_to_name = {wh["id"]: wh["name"] for wh in selected_whs}

    # Build venue assignment data for the editor — deduplicate to avoid key conflicts
    assignments = st.session_state.assignments
    venue_rows = []
    seen_ids = set()
    for wh_id, venue_list in assignments.items():
        for v in venue_list:
            if v["id"] not in seen_ids:
                seen_ids.add(v["id"])
                venue_rows.append({
                    "Venue": v["name"],
                    "City": v["city"],
                    "Demand": v["demand"],
                    "Stock": v["stock"],
                    "Warehouse": wh_id_to_name[wh_id],
                    "_venue_id": v["id"],
                })
    # Add any venues missing from assignments (safety net)
    for v in VENUES:
        if v["id"] not in seen_ids:
            first_wh = selected_whs[0]
            venue_rows.append({
                "Venue": v["name"],
                "City": v["city"],
                "Demand": v["demand"],
                "Stock": v["stock"],
                "Warehouse": wh_id_to_name[first_wh["id"]],
                "_venue_id": v["id"],
            })
    venue_rows.sort(key=lambda r: r["Venue"])

    # Sidebar controls
    with st.sidebar:
        st.markdown("#### Warehouse assignments")

        for wh in selected_whs:
            wh_id = wh["id"]
            color = wh_colors[wh_id]
            assigned = assignments.get(wh_id, [])
            total_assigned = sum(v["demand"] for v in assigned)
            n_routes = max(1, math.ceil(total_assigned / 24)) if assigned else 0

            with st.expander(f"\U0001f4e6 {wh['name']} ({total_assigned}/{wh['capacity']}p)", expanded=True):
                st.progress(min(total_assigned / wh["capacity"], 1.0))
                if total_assigned > wh["capacity"]:
                    st.error(f"Over capacity by {total_assigned - wh['capacity']} pallets!")
                st.markdown(f"**Venues:** {len(assigned)} | **Routes needed:** {n_routes}")
                for v in sorted(assigned, key=lambda x: x["name"]):
                    urgency = "\U0001f534" if v["stock"] < 2 else ""
                    st.markdown(f"- {urgency} {v['name']} ({v['demand']}p)")

        # Capacity check
        errors = check_capacity(assignments, selected_whs)
        st.markdown("---")
        if errors:
            st.error("Cannot confirm: some warehouses are over capacity.")
            for e in errors:
                st.warning(e)
            can_confirm = False
        else:
            can_confirm = True

        if st.button("\u2705 Confirm routes", disabled=not can_confirm):
            routes = build_routes_nearest_neighbor(assignments, selected_whs)
            st.session_state.user_routes = routes
            st.session_state.user_cost = get_full_cost_breakdown(selected_whs, routes)
            st.session_state.phase = 3
            st.rerun()

    # Main content
    col_map, col_edit = st.columns([3, 2])

    with col_edit:
        st.markdown("#### Reassign venues")
        st.caption("Change the Warehouse column to reassign a venue.")

        import pandas as pd
        df = pd.DataFrame(venue_rows)
        display_df = df[["Venue", "City", "Demand", "Stock", "Warehouse"]].copy()

        edited = st.data_editor(
            display_df,
            column_config={
                "Warehouse": st.column_config.SelectboxColumn(
                    "Warehouse",
                    options=list(wh_name_to_id.keys()),
                    required=True,
                ),
                "Demand": st.column_config.NumberColumn("Demand", format="%d pallets"),
                "Stock": st.column_config.NumberColumn("Stock", format="%d pallets"),
            },
            hide_index=True,
            use_container_width=True,
            key="venue_editor",
        )

        # Sync edits back to assignments (deduplicate by venue ID)
        if edited is not None:
            new_assignments = {wh["id"]: [] for wh in selected_whs}
            venue_lookup = {v["name"]: v for v in VENUES}
            assigned_ids = set()
            for _, row in edited.iterrows():
                venue = venue_lookup.get(row["Venue"])
                wh_id = wh_name_to_id.get(row["Warehouse"])
                if venue and wh_id and venue["id"] not in assigned_ids:
                    assigned_ids.add(venue["id"])
                    new_assignments[wh_id].append(venue)
            st.session_state.assignments = new_assignments
            assignments = new_assignments

    with col_map:
        routes_preview = build_routes_nearest_neighbor(assignments, selected_whs)
        m = build_phase2_map_with_routes(
            BREWERIES, VENUES, selected_whs, assignments, routes_preview, WAREHOUSES,
        )
        st_folium(m, width=700, height=550, returned_objects=[], key="phase2_map")


# ============================================================
# PHASE 3: Results & Optimizer Comparison
# ============================================================
elif st.session_state.phase == 3:
    st.markdown("## \U0001f4ca Results & Optimizer Comparison")

    selected_whs = get_selected_warehouses()
    user_cost = st.session_state.user_cost

    # --- User Results ---
    st.markdown("### \U0001f4cb Your plan")
    cols = st.columns(6)
    cols[0].metric("Warehouse cost", f"\u20ac{user_cost['warehouse_cost']:,.0f}/wk")
    cols[1].metric("Fuel cost", f"\u20ac{user_cost['fuel_cost']:,.0f}/wk")
    cols[2].metric("Total distance", f"{user_cost['total_distance']:,.0f} km")
    cols[3].metric("Driving time", f"{user_cost['total_time']:,.1f} hrs")
    cols[4].metric("Truck routes", f"{user_cost['total_trucks']}")
    cols[5].metric("\u2b50 Total cost", f"\u20ac{user_cost['total_cost']:,.0f}/wk")

    # Count urgent venues
    urgent_count = sum(1 for v in VENUES if v["stock"] < 2)
    st.markdown(f"\u26a0\ufe0f **{urgent_count}** venues are running critically low (stock < 2 pallets)")

    st.divider()

    # --- Optimizer ---
    st.markdown("### \U0001f916 Run the optimizer")
    st.markdown(
        "The optimizer evaluates all 56 warehouse combinations, "
        "uses Clarke-Wright savings routing, 2-opt improvement, "
        "and border venue reassignment."
    )

    run_col, result_col = st.columns([1, 2])

    with run_col:
        if st.button("\U0001f680 Run optimizer", type="primary", use_container_width=True):
            progress = st.progress(0, text="Initializing...")
            for i in range(20):
                time.sleep(0.05)
                progress.progress(i * 5, text="Evaluating warehouse combinations...")
            for i in range(20, 40):
                time.sleep(0.03)
                progress.progress(i * 2.5, text="Building optimized routes...")

            opt_result = optimize(VENUES, WAREHOUSES)

            for i in range(40, 50):
                time.sleep(0.02)
                progress.progress(80 + i - 40, text="Applying 2-opt improvements...")
            progress.progress(100, text="Done!")
            time.sleep(0.3)

            st.session_state.optimizer_result = opt_result
            st.session_state.show_optimizer = True
            st.rerun()

    # --- Show optimizer results ---
    if st.session_state.show_optimizer and st.session_state.optimizer_result:
        opt = st.session_state.optimizer_result
        opt_cost = opt["stats"]

        st.markdown("### \u2728 Optimized plan")
        st.markdown(
            f"**Optimizer chose:** {', '.join(w['name'] for w in opt['warehouses'])}"
        )

        cols = st.columns(6)
        d_wh = opt_cost["warehouse_cost"] - user_cost["warehouse_cost"]
        d_fuel = opt_cost["fuel_cost"] - user_cost["fuel_cost"]
        d_dist = opt_cost["total_distance"] - user_cost["total_distance"]
        d_time = opt_cost["total_time"] - user_cost["total_time"]
        d_trucks = opt_cost["total_trucks"] - user_cost["total_trucks"]
        d_total = opt_cost["total_cost"] - user_cost["total_cost"]

        cols[0].metric("Warehouse cost", f"\u20ac{opt_cost['warehouse_cost']:,.0f}/wk",
                       delta=f"\u20ac{d_wh:+,.0f}", delta_color="inverse")
        cols[1].metric("Fuel cost", f"\u20ac{opt_cost['fuel_cost']:,.0f}/wk",
                       delta=f"\u20ac{d_fuel:+,.0f}", delta_color="inverse")
        cols[2].metric("Total distance", f"{opt_cost['total_distance']:,.0f} km",
                       delta=f"{d_dist:+,.0f} km", delta_color="inverse")
        cols[3].metric("Driving time", f"{opt_cost['total_time']:,.1f} hrs",
                       delta=f"{d_time:+,.1f} hrs", delta_color="inverse")
        cols[4].metric("Truck routes", f"{opt_cost['total_trucks']}",
                       delta=f"{d_trucks:+d}", delta_color="inverse")
        cols[5].metric("\u2b50 Total cost", f"\u20ac{opt_cost['total_cost']:,.0f}/wk",
                       delta=f"\u20ac{d_total:+,.0f}", delta_color="inverse")

        weekly_savings = user_cost["total_cost"] - opt_cost["total_cost"]
        yearly_savings = weekly_savings * 52
        pct_savings = (weekly_savings / user_cost["total_cost"]) * 100

        if weekly_savings > 0:
            st.success(
                f"\U0001f4b0 **Savings: \u20ac{weekly_savings:,.0f}/week "
                f"(\u20ac{yearly_savings:,.0f}/year) \u2014 {pct_savings:.0f}% reduction**"
            )

        # Maps comparison
        st.divider()
        tab_user, tab_opt = st.tabs(["\U0001f4cb Your plan", "\u2728 Optimized plan"])

        with tab_user:
            m_user = build_phase3_map(
                BREWERIES, VENUES, selected_whs, st.session_state.assignments,
                st.session_state.user_routes, WAREHOUSES,
            )
            st_folium(m_user, width=900, height=500, returned_objects=[], key="phase3_user_map")

        with tab_opt:
            m_opt = build_phase3_map(
                BREWERIES, VENUES, opt["warehouses"], opt["assignments"],
                opt["routes"], WAREHOUSES,
            )
            st_folium(m_opt, width=900, height=500, returned_objects=[], key="phase3_opt_map")

        # Reveal message
        st.markdown(f"""
<div class="reveal-box">
    <h3>"Your logistics intuition is good \u2014 but math is better."</h3>
    <p>Even in this simplified scenario with {len(VENUES)} venues and 3 warehouses,
    the optimizer found a plan that saves <b>\u20ac{weekly_savings:,.0f}/week</b> \u2014
    that's <b>\u20ac{yearly_savings:,.0f}/year</b>.</p>
    <p>In reality, breweries manage hundreds of venues across multiple regions, with daily-changing
    demand, vehicle fleets, time windows, driver schedules, and seasonal peaks. The savings gap
    grows exponentially with complexity.</p>
    <p><b>This is what Rivnox builds.</b> Custom planning & forecasting tools that turn complex
    logistics decisions into automated, data-driven solutions \u2014 in weeks, not months.</p>
    <p>\U0001f517 <a href="https://rivnox.ai" target="_blank"><b>rivnox.ai</b></a></p>
</div>
""", unsafe_allow_html=True)


# --- Footer ---
st.sidebar.divider()
st.sidebar.caption("Built by [Rivnox](https://rivnox.ai) \u2022 Logistics Planning Demo")
