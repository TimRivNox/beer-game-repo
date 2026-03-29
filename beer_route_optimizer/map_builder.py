"""
Folium map builders for each phase of the Beer Route Optimizer.
"""

import folium
from beer_route_optimizer.data import COLORS, WAREHOUSE_COLORS

BELGIUM_CENTER = [50.85, 4.35]
DEFAULT_ZOOM = 8


def create_base_map():
    """Create a base Folium map centered on Belgium."""
    return folium.Map(
        location=BELGIUM_CENTER,
        zoom_start=DEFAULT_ZOOM,
        tiles="CartoDB positron",
    )


def add_breweries(m, breweries):
    """Add brewery markers to the map."""
    for b in breweries:
        folium.Marker(
            location=[b["lat"], b["lon"]],
            popup=folium.Popup(
                f"<b>{b['name']}</b><br>{b['products']}<br>Volume: {b['volume']}",
                max_width=250,
            ),
            tooltip=b["name"],
            icon=folium.Icon(color="darkblue", icon="industry", prefix="fa"),
        ).add_to(m)


def add_warehouses(m, warehouses, selected_ids=None, warehouse_colors=None):
    """Add warehouse markers. Selected ones are colored, others are gray."""
    if selected_ids is None:
        selected_ids = []
    if warehouse_colors is None:
        warehouse_colors = {}

    for wh in warehouses:
        is_selected = wh["id"] in selected_ids
        color_hex = warehouse_colors.get(wh["id"], "#888888")

        if is_selected:
            icon = folium.Icon(color="orange", icon="warehouse", prefix="fa")
        else:
            icon = folium.Icon(color="gray", icon="box", prefix="fa")

        folium.Marker(
            location=[wh["lat"], wh["lon"]],
            popup=folium.Popup(
                f"<b>{wh['name']}</b><br>"
                f"Cost: \u20ac{wh['weekly_cost']:,}/week<br>"
                f"Capacity: {wh['capacity']} pallets",
                max_width=200,
            ),
            tooltip=f"{wh['name']} ({'Selected' if is_selected else 'Available'})",
            icon=icon,
        ).add_to(m)


def _urgency_color(venue):
    """Get color based on stock urgency."""
    if venue["stock"] < 2:
        return COLORS["red"]
    elif venue["stock"] < 4:
        return COLORS["yellow"]
    return COLORS["green"]


def add_venues(m, venues, color_mode="urgency", assignments=None, warehouse_colors=None):
    """Add venue CircleMarkers to the map.
    color_mode: "urgency" (by stock level) or "warehouse" (by assignment).
    """
    if warehouse_colors is None:
        warehouse_colors = {}

    # Build venue-to-warehouse color lookup
    venue_wh_color = {}
    if color_mode == "warehouse" and assignments:
        for wh_id, venue_list in assignments.items():
            c = warehouse_colors.get(wh_id, "#888888")
            for v in venue_list:
                venue_wh_color[v["id"]] = c

    for venue in venues:
        if color_mode == "urgency":
            color = _urgency_color(venue)
        else:
            color = venue_wh_color.get(venue["id"], "#888888")

        radius = max(5, venue["demand"] * 1.2 + 2)
        urgency_text = "URGENT" if venue["stock"] < 2 else ("Low" if venue["stock"] < 4 else "OK")

        folium.CircleMarker(
            location=[venue["lat"], venue["lon"]],
            radius=radius,
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.7,
            popup=folium.Popup(
                f"<b>{venue['name']}</b><br>"
                f"City: {venue['city']}<br>"
                f"Demand: {venue['demand']} pallets<br>"
                f"Stock: {venue['stock']} pallets ({urgency_text})",
                max_width=220,
            ),
            tooltip=f"{venue['name']} ({venue['demand']}p)",
        ).add_to(m)


def add_routes(m, routes_dict, warehouse_colors=None):
    """Draw route polylines for each warehouse."""
    if warehouse_colors is None:
        warehouse_colors = {}

    for wh_id, routes in routes_dict.items():
        color = warehouse_colors.get(wh_id, "#888888")
        for route in routes:
            if not route["stops"]:
                continue
            # Build coordinates: we don't have the depot in stops, but the line
            # goes through the stops in order
            coords = [[s["lat"], s["lon"]] for s in route["stops"]]
            folium.PolyLine(
                locations=coords,
                color=color,
                weight=3,
                opacity=0.7,
            ).add_to(m)


def add_routes_with_depot(m, routes_dict, warehouses, warehouse_colors=None):
    """Draw route polylines including depot (warehouse) at start and end."""
    if warehouse_colors is None:
        warehouse_colors = {}

    wh_lookup = {wh["id"]: wh for wh in warehouses}

    for wh_id, routes in routes_dict.items():
        color = warehouse_colors.get(wh_id, "#888888")
        depot = wh_lookup[wh_id]
        for route in routes:
            if not route["stops"]:
                continue
            coords = [[depot["lat"], depot["lon"]]]
            coords += [[s["lat"], s["lon"]] for s in route["stops"]]
            coords.append([depot["lat"], depot["lon"]])
            folium.PolyLine(
                locations=coords,
                color=color,
                weight=3,
                opacity=0.7,
                dash_array="5 5" if len(routes) > 2 else None,
            ).add_to(m)


def build_phase1_map(breweries, venues, candidate_warehouses):
    """Phase 1: Show venues (urgency colors), breweries, and all candidate warehouses."""
    m = create_base_map()
    add_breweries(m, breweries)
    add_warehouses(m, candidate_warehouses, selected_ids=[])
    add_venues(m, venues, color_mode="urgency")
    return m


def build_phase2_map(breweries, venues, selected_warehouses, assignments, candidate_warehouses):
    """Phase 2: Venues colored by warehouse, selected warehouses highlighted."""
    m = create_base_map()
    add_breweries(m, breweries)

    selected_ids = [wh["id"] for wh in selected_warehouses]
    wh_colors = _make_warehouse_colors(selected_warehouses)

    add_warehouses(m, candidate_warehouses, selected_ids=selected_ids, warehouse_colors=wh_colors)
    add_venues(m, venues, color_mode="warehouse", assignments=assignments, warehouse_colors=wh_colors)
    return m


def build_phase2_map_with_routes(breweries, venues, selected_warehouses, assignments,
                                  routes_dict, candidate_warehouses):
    """Phase 2 with route lines drawn."""
    m = build_phase2_map(breweries, venues, selected_warehouses, assignments, candidate_warehouses)
    wh_colors = _make_warehouse_colors(selected_warehouses)
    add_routes_with_depot(m, routes_dict, selected_warehouses, warehouse_colors=wh_colors)
    return m


def build_phase3_map(breweries, venues, selected_warehouses, assignments, routes_dict,
                     candidate_warehouses):
    """Phase 3: Full view with routes."""
    m = create_base_map()
    add_breweries(m, breweries)

    selected_ids = [wh["id"] for wh in selected_warehouses]
    wh_colors = _make_warehouse_colors(selected_warehouses)

    add_warehouses(m, candidate_warehouses, selected_ids=selected_ids, warehouse_colors=wh_colors)
    add_venues(m, venues, color_mode="warehouse", assignments=assignments, warehouse_colors=wh_colors)
    add_routes_with_depot(m, routes_dict, selected_warehouses, warehouse_colors=wh_colors)
    return m


def _make_warehouse_colors(selected_warehouses):
    """Map warehouse IDs to their display colors."""
    colors = {}
    for i, wh in enumerate(selected_warehouses):
        colors[wh["id"]] = WAREHOUSE_COLORS[i % len(WAREHOUSE_COLORS)]
    return colors
