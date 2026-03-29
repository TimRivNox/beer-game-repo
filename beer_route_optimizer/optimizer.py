"""
Automated optimizer: brute-force warehouse selection, Clarke-Wright savings,
2-opt improvement, and border venue reassignment.
"""

import math
from itertools import combinations

from beer_route_optimizer.utils import haversine, driving_time, route_distance
from beer_route_optimizer.scoring import (
    calc_warehouse_cost,
    calc_routes_stats,
    calc_total_cost,
    FUEL_COST_PER_KM,
    TRUCK_CAPACITY,
)

MAX_ROUTE_HOURS = 4.0


def _precompute_distances(points):
    """Precompute pairwise distance matrix for a list of dicts with lat/lon.
    Returns a dict keyed by (index_a, index_b) -> distance_km.
    """
    n = len(points)
    dist = {}
    for i in range(n):
        for j in range(i + 1, n):
            d = haversine(points[i]["lat"], points[i]["lon"], points[j]["lat"], points[j]["lon"])
            dist[(i, j)] = d
            dist[(j, i)] = d
        dist[(i, i)] = 0.0
    return dist


def _clarke_wright(depot_idx, stop_indices, demands, dist_matrix):
    """Clarke-Wright savings algorithm.
    Returns list of routes, each route = list of stop indices in visit order.
    """
    if not stop_indices:
        return []

    # Start: each stop is its own shuttle route
    routes = [[s] for s in stop_indices]
    route_of = {}  # stop_idx -> route_index
    for ri, route in enumerate(routes):
        route_of[route[0]] = ri

    # Compute savings
    savings = []
    for i in range(len(stop_indices)):
        for j in range(i + 1, len(stop_indices)):
            si, sj = stop_indices[i], stop_indices[j]
            s = dist_matrix[(depot_idx, si)] + dist_matrix[(depot_idx, sj)] - dist_matrix[(si, sj)]
            savings.append((s, si, sj))
    savings.sort(reverse=True, key=lambda x: x[0])

    def route_demand(route):
        return sum(demands[s] for s in route)

    def route_time(route):
        d = dist_matrix[(depot_idx, route[0])]
        for k in range(len(route) - 1):
            d += dist_matrix[(route[k], route[k + 1])]
        d += dist_matrix[(route[-1], depot_idx)]
        return driving_time(d)

    for s_val, si, sj in savings:
        if s_val <= 0:
            break
        ri = route_of.get(si)
        rj = route_of.get(sj)
        if ri is None or rj is None or ri == rj:
            continue
        route_i = routes[ri]
        route_j = routes[rj]
        if route_i is None or route_j is None:
            continue

        # Can only merge if si is at end of route_i and sj is at start of route_j, or vice versa
        can_merge = False
        merged = None
        if route_i[-1] == si and route_j[0] == sj:
            merged = route_i + route_j
            can_merge = True
        elif route_j[-1] == sj and route_i[0] == si:
            merged = route_j + route_i
            can_merge = True
        elif route_i[-1] == si and route_j[-1] == sj:
            merged = route_i + list(reversed(route_j))
            can_merge = True
        elif route_i[0] == si and route_j[0] == sj:
            merged = list(reversed(route_i)) + route_j
            can_merge = True

        if not can_merge or merged is None:
            continue

        # Check constraints
        if route_demand(merged) > TRUCK_CAPACITY:
            continue
        if route_time(merged) > MAX_ROUTE_HOURS:
            continue

        # Merge: replace route_i with merged, nullify route_j
        routes[ri] = merged
        routes[rj] = None
        for s in merged:
            route_of[s] = ri

    return [r for r in routes if r is not None]


def _two_opt(route, depot_idx, dist_matrix, max_passes=5):
    """2-opt improvement on a single route. Returns improved route."""
    if len(route) < 3:
        return route

    def total_dist(r):
        d = dist_matrix[(depot_idx, r[0])]
        for k in range(len(r) - 1):
            d += dist_matrix[(r[k], r[k + 1])]
        d += dist_matrix[(r[-1], depot_idx)]
        return d

    best = list(route)
    improved = True
    passes = 0
    while improved and passes < max_passes:
        improved = False
        passes += 1
        for i in range(len(best) - 1):
            for j in range(i + 2, len(best)):
                new_route = best[:i + 1] + list(reversed(best[i + 1:j + 1])) + best[j + 1:]
                if total_dist(new_route) < total_dist(best) - 0.01:
                    best = new_route
                    improved = True
    return best


def _build_optimized_routes(depot_idx, stop_indices, demands, dist_matrix, points):
    """Run Clarke-Wright + 2-opt for one warehouse's venues."""
    routes_indices = _clarke_wright(depot_idx, stop_indices, demands, dist_matrix)

    # Apply 2-opt to each route
    optimized = []
    for route_idx_list in routes_indices:
        improved = _two_opt(route_idx_list, depot_idx, dist_matrix)
        # Convert to venue dicts with stats
        stops = [points[idx] for idx in improved]
        pallets = sum(demands[idx] for idx in improved)
        dist = dist_matrix[(depot_idx, improved[0])]
        for k in range(len(improved) - 1):
            dist += dist_matrix[(improved[k], improved[k + 1])]
        dist += dist_matrix[(improved[-1], depot_idx)]
        optimized.append({
            "stops": stops,
            "pallets": pallets,
            "distance": dist,
            "time": driving_time(dist),
        })
    return optimized


def optimize(venues, candidate_warehouses):
    """Run the full optimizer. Returns dict with best solution.

    Steps:
    1. Brute-force best 3 warehouses from 8 candidates
    2. Clarke-Wright savings routing per warehouse
    3. 2-opt improvement
    4. Border venue reassignment
    """
    # Build a combined point list: warehouses first, then venues
    wh_count = len(candidate_warehouses)
    points = list(candidate_warehouses) + list(venues)
    demands = {i: 0 for i in range(wh_count)}
    for i, v in enumerate(venues):
        demands[wh_count + i] = v["demand"]

    # Precompute all pairwise distances
    dist_matrix = _precompute_distances(points)

    # Venue indices in the points array
    venue_indices = list(range(wh_count, len(points)))

    best_combo = None
    best_cost = float("inf")
    best_assignments = None

    total_demand = sum(v["demand"] for v in venues)

    # Try all C(8,3) = 56 combinations
    for combo in combinations(range(wh_count), 3):
        selected = [candidate_warehouses[i] for i in combo]

        # Check total capacity
        total_cap = sum(selected[k]["capacity"] for k in range(3))
        if total_cap < total_demand:
            continue

        # Assign venues to nearest warehouse in this combo
        assignments = {ci: [] for ci in combo}
        for vi in venue_indices:
            nearest = min(combo, key=lambda ci: dist_matrix[(ci, vi)])
            assignments[nearest].append(vi)

        # Check individual warehouse capacity
        feasible = True
        for ci in combo:
            assigned_demand = sum(demands[vi] for vi in assignments[ci])
            if assigned_demand > candidate_warehouses[ci]["capacity"]:
                feasible = False
                break
        if not feasible:
            continue

        # Full cost: warehouse cost + CW-routed fuel cost (fast enough for 56 combos)
        wh_cost = sum(candidate_warehouses[ci]["weekly_cost"] for ci in combo)
        delivery_dist = 0.0
        for ci in combo:
            if assignments[ci]:
                routes = _clarke_wright(ci, assignments[ci], demands, dist_matrix)
                for route in routes:
                    d = dist_matrix[(ci, route[0])]
                    for k in range(len(route) - 1):
                        d += dist_matrix[(route[k], route[k + 1])]
                    d += dist_matrix[(route[-1], ci)]
                    delivery_dist += d
        fuel = delivery_dist * FUEL_COST_PER_KM
        total_cost = wh_cost + fuel

        if total_cost < best_cost:
            best_cost = total_cost
            best_combo = combo
            best_assignments = assignments

    if best_combo is None:
        raise ValueError("No feasible warehouse combination found")

    # Build optimized routes for the best combo
    selected_warehouses = [candidate_warehouses[ci] for ci in best_combo]
    routes_dict = {}
    assignments_dict = {}

    for ci in best_combo:
        wh = candidate_warehouses[ci]
        stop_idxs = best_assignments[ci]
        routes = _build_optimized_routes(ci, stop_idxs, demands, dist_matrix, points)
        routes_dict[wh["id"]] = routes
        assignments_dict[wh["id"]] = [points[vi] for vi in stop_idxs]

    # Border venue reassignment: try swapping venues near the boundary
    wh_ids = [candidate_warehouses[ci]["id"] for ci in best_combo]
    _try_border_reassignment(
        best_combo, assignments_dict, routes_dict, demands, dist_matrix, points,
        candidate_warehouses, wh_count,
    )

    # Final cost calculation
    from beer_route_optimizer.scoring import get_full_cost_breakdown
    cost_breakdown = get_full_cost_breakdown(selected_warehouses, routes_dict)

    return {
        "warehouses": selected_warehouses,
        "assignments": assignments_dict,
        "routes": routes_dict,
        "stats": cost_breakdown,
    }


def _try_border_reassignment(combo, assignments_dict, routes_dict, demands, dist_matrix, points,
                              candidate_warehouses, wh_count):
    """Try reassigning border venues (within 20% distance of 2nd-nearest warehouse)."""
    threshold = 0.20

    for ci in combo:
        wh = candidate_warehouses[ci]
        wh_id = wh["id"]
        other_combos = [c for c in combo if c != ci]

        venues_to_try = []
        for venue in list(assignments_dict[wh_id]):
            vi = next(i for i, p in enumerate(points) if p is venue or (p.get("id") == venue.get("id") and i >= wh_count))
            d_current = dist_matrix[(ci, vi)]
            for oci in other_combos:
                d_other = dist_matrix[(oci, vi)]
                if d_other < d_current * (1 + threshold):
                    venues_to_try.append((venue, vi, ci, oci))

    for venue, vi, from_ci, to_ci in venues_to_try:
        from_wh_id = candidate_warehouses[from_ci]["id"]
        to_wh_id = candidate_warehouses[to_ci]["id"]

        if venue not in assignments_dict[from_wh_id]:
            continue

        # Check capacity
        to_demand = sum(v["demand"] for v in assignments_dict[to_wh_id]) + venue["demand"]
        if to_demand > candidate_warehouses[to_ci]["capacity"]:
            continue

        # Try the swap: compute cost before and after
        old_from_routes = routes_dict[from_wh_id]
        old_to_routes = routes_dict[to_wh_id]
        old_from_dist = sum(r["distance"] for r in old_from_routes)
        old_to_dist = sum(r["distance"] for r in old_to_routes)

        # Move venue
        new_from_venues = [v for v in assignments_dict[from_wh_id] if v is not venue]
        new_to_venues = assignments_dict[to_wh_id] + [venue]

        # Rebuild routes for affected warehouses
        from_stop_idxs = [next(i for i, p in enumerate(points) if p is v) for v in new_from_venues]
        to_stop_idxs = [next(i for i, p in enumerate(points) if p is v) for v in new_to_venues]

        new_from_routes = _build_optimized_routes(from_ci, from_stop_idxs, demands, dist_matrix, points)
        new_to_routes = _build_optimized_routes(to_ci, to_stop_idxs, demands, dist_matrix, points)

        new_from_dist = sum(r["distance"] for r in new_from_routes)
        new_to_dist = sum(r["distance"] for r in new_to_routes)

        if (new_from_dist + new_to_dist) < (old_from_dist + old_to_dist) - 0.5:
            assignments_dict[from_wh_id] = new_from_venues
            assignments_dict[to_wh_id] = new_to_venues
            routes_dict[from_wh_id] = new_from_routes
            routes_dict[to_wh_id] = new_to_routes
