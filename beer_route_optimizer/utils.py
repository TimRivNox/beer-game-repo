"""
Utility functions: Haversine distance, nearest-neighbor routing, venue assignment.
"""

import math

ROAD_CORRECTION_FACTOR = 1.3
AVG_SPEED_KMH = 50.0


def haversine(lat1, lon1, lat2, lon2):
    """Calculate road-corrected distance in km between two points."""
    r = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(math.radians(lat1))
        * math.cos(math.radians(lat2))
        * math.sin(dlon / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return r * c * ROAD_CORRECTION_FACTOR


def driving_time(distance_km):
    """Estimate driving time in hours at average speed."""
    return distance_km / AVG_SPEED_KMH


def route_distance(depot, stops):
    """Calculate total distance for a route: depot -> stops[0] -> ... -> stops[-1] -> depot."""
    if not stops:
        return 0.0
    dist = haversine(depot["lat"], depot["lon"], stops[0]["lat"], stops[0]["lon"])
    for i in range(len(stops) - 1):
        dist += haversine(stops[i]["lat"], stops[i]["lon"], stops[i + 1]["lat"], stops[i + 1]["lon"])
    dist += haversine(stops[-1]["lat"], stops[-1]["lon"], depot["lat"], depot["lon"])
    return dist


def nearest_neighbor_route(depot, stops):
    """Order stops using nearest-neighbor heuristic starting from depot.
    Returns a new list of stops in visit order.
    """
    if not stops:
        return []
    remaining = list(stops)
    ordered = []
    current_lat, current_lon = depot["lat"], depot["lon"]
    while remaining:
        nearest_idx = min(
            range(len(remaining)),
            key=lambda i: haversine(current_lat, current_lon, remaining[i]["lat"], remaining[i]["lon"]),
        )
        nearest = remaining.pop(nearest_idx)
        ordered.append(nearest)
        current_lat, current_lon = nearest["lat"], nearest["lon"]
    return ordered


def assign_venues_to_nearest(venues, warehouses):
    """Assign each venue to its nearest warehouse.
    Returns dict: warehouse_id -> list of venue dicts.
    """
    assignments = {wh["id"]: [] for wh in warehouses}
    for venue in venues:
        nearest_wh = min(
            warehouses,
            key=lambda wh: haversine(venue["lat"], venue["lon"], wh["lat"], wh["lon"]),
        )
        assignments[nearest_wh["id"]].append(venue)
    return assignments


def build_routes_nearest_neighbor(assignments, warehouses, truck_capacity=24):
    """Build routes using nearest-neighbor for each warehouse's assigned venues.
    Returns dict: warehouse_id -> list of routes, where each route is
    {"stops": [...], "pallets": int, "distance": float, "time": float}.
    """
    wh_lookup = {wh["id"]: wh for wh in warehouses}
    all_routes = {}
    for wh_id, venues in assignments.items():
        depot = wh_lookup[wh_id]
        ordered = nearest_neighbor_route(depot, venues)
        routes = []
        current_route = []
        current_pallets = 0
        for venue in ordered:
            if current_pallets + venue["demand"] > truck_capacity and current_route:
                dist = route_distance(depot, current_route)
                routes.append({
                    "stops": current_route,
                    "pallets": current_pallets,
                    "distance": dist,
                    "time": driving_time(dist),
                })
                current_route = []
                current_pallets = 0
            current_route.append(venue)
            current_pallets += venue["demand"]
        if current_route:
            dist = route_distance(depot, current_route)
            routes.append({
                "stops": current_route,
                "pallets": current_pallets,
                "distance": dist,
                "time": driving_time(dist),
            })
        all_routes[wh_id] = routes
    return all_routes
