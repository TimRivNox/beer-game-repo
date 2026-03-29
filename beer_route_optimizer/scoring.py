"""
Cost calculations: warehouse cost, fuel cost, route stats, capacity checks.
"""

from beer_route_optimizer.utils import route_distance, driving_time

FUEL_COST_PER_KM = 0.45
TRUCK_CAPACITY = 24


def calc_warehouse_cost(warehouses):
    """Sum of weekly operating costs for selected warehouses."""
    return sum(wh["weekly_cost"] for wh in warehouses)


def calc_routes_stats(routes_dict, warehouses):
    """Calculate aggregate stats across all warehouse routes.
    routes_dict: {warehouse_id: [{"stops": [...], "pallets": int, "distance": float, "time": float}, ...]}
    Returns dict with totals.
    """
    total_distance = 0.0
    total_time = 0.0
    total_trucks = 0
    for wh_id, routes in routes_dict.items():
        for route in routes:
            total_distance += route["distance"]
            total_time += route["time"]
            total_trucks += 1
    fuel_cost = total_distance * FUEL_COST_PER_KM
    return {
        "total_distance": total_distance,
        "total_time": total_time,
        "total_trucks": total_trucks,
        "fuel_cost": fuel_cost,
    }


def calc_total_cost(warehouse_cost, fuel_cost):
    """Total weekly cost."""
    return warehouse_cost + fuel_cost


def check_capacity(assignments, warehouses):
    """Check if any warehouse is over capacity.
    Returns list of error strings (empty = all OK).
    """
    wh_lookup = {wh["id"]: wh for wh in warehouses}
    errors = []
    for wh_id, venues in assignments.items():
        wh = wh_lookup[wh_id]
        total_demand = sum(v["demand"] for v in venues)
        if total_demand > wh["capacity"]:
            errors.append(
                f"{wh['name']}: {total_demand} pallets assigned, capacity is {wh['capacity']} "
                f"(over by {total_demand - wh['capacity']})"
            )
    return errors


def get_full_cost_breakdown(selected_warehouses, routes_dict):
    """Convenience: compute full cost breakdown from warehouses and routes."""
    warehouse_cost = calc_warehouse_cost(selected_warehouses)
    stats = calc_routes_stats(routes_dict, selected_warehouses)
    total = calc_total_cost(warehouse_cost, stats["fuel_cost"])
    return {
        "warehouse_cost": warehouse_cost,
        "fuel_cost": stats["fuel_cost"],
        "total_distance": stats["total_distance"],
        "total_time": stats["total_time"],
        "total_trucks": stats["total_trucks"],
        "total_cost": total,
    }
