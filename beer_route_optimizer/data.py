"""
All hardcoded data for the Beer Route Optimizer.
Breweries, candidate warehouses, venues, and color palette.
"""

# Color palette
COLORS = {
    "navy": "#1B3A5C",
    "orange": "#E8923C",
    "teal": "#2B9E8F",
    "cream": "#FAF7F2",
    "purple": "#7B68EE",
    "red": "#E85B5B",
    "yellow": "#E8B84D",
    "green": "#4AA872",
}

# Warehouse assignment colors (used for venue coloring and route lines)
WAREHOUSE_COLORS = ["#E8923C", "#2B9E8F", "#7B68EE"]

# --- Breweries (fixed production sources) ---
BREWERIES = [
    {
        "id": "brewery_puurs",
        "name": "Duvel Moortgat (Puurs-Sint-Amands)",
        "lat": 51.07,
        "lon": 4.29,
        "products": "Duvel, Vedett, Maredsous",
        "volume": "high",
    },
    {
        "id": "brewery_achouffe",
        "name": "Brasserie d'Achouffe (Houffalize)",
        "lat": 50.13,
        "lon": 5.72,
        "products": "Chouffe",
        "volume": "medium",
    },
    {
        "id": "brewery_liefmans",
        "name": "Liefmans (Oudenaarde)",
        "lat": 50.85,
        "lon": 3.61,
        "products": "Liefmans fruit beers",
        "volume": "low",
    },
    {
        "id": "brewery_dekoninck",
        "name": "De Koninck (Antwerp)",
        "lat": 51.21,
        "lon": 4.42,
        "products": "Bolleke / De Koninck",
        "volume": "medium",
    },
]

# --- Candidate Warehouses (user picks 3) ---
WAREHOUSES = [
    {
        "id": "wh_mechelen",
        "name": "Mechelen",
        "lat": 51.03,
        "lon": 4.48,
        "weekly_cost": 2800,
        "capacity": 180,
    },
    {
        "id": "wh_ghent",
        "name": "Ghent",
        "lat": 51.05,
        "lon": 3.72,
        "weekly_cost": 3200,
        "capacity": 200,
    },
    {
        "id": "wh_leuven",
        "name": "Leuven",
        "lat": 50.88,
        "lon": 4.70,
        "weekly_cost": 2600,
        "capacity": 160,
    },
    {
        "id": "wh_brussels",
        "name": "Brussels",
        "lat": 50.85,
        "lon": 4.35,
        "weekly_cost": 3800,
        "capacity": 220,
    },
    {
        "id": "wh_hasselt",
        "name": "Hasselt",
        "lat": 50.93,
        "lon": 5.34,
        "weekly_cost": 2400,
        "capacity": 140,
    },
    {
        "id": "wh_kortrijk",
        "name": "Kortrijk",
        "lat": 50.83,
        "lon": 3.26,
        "weekly_cost": 2900,
        "capacity": 150,
    },
    {
        "id": "wh_turnhout",
        "name": "Turnhout",
        "lat": 51.32,
        "lon": 4.95,
        "weekly_cost": 2200,
        "capacity": 120,
    },
    {
        "id": "wh_sintniklaas",
        "name": "Sint-Niklaas",
        "lat": 51.16,
        "lon": 4.14,
        "weekly_cost": 2500,
        "capacity": 160,
    },
]

# --- 40 Venues across Flanders and Brussels ---
# Total demand: ~252 pallets
# Stock levels: 0 to demand * 0.4 (most running low)
# Border venues marked for optimizer testing
VENUES = [
    # Antwerp area (5 venues)
    {"id": 1, "name": "Café Den Hopsack", "city": "Antwerp", "lat": 51.22, "lon": 4.40, "demand": 8, "stock": 1},
    {"id": 2, "name": "Grand Café Bolleke", "city": "Antwerp", "lat": 51.21, "lon": 4.43, "demand": 10, "stock": 3},
    {"id": 3, "name": "Brasserie 't Pakhuis", "city": "Antwerp", "lat": 51.20, "lon": 4.41, "demand": 7, "stock": 0},
    {"id": 4, "name": "Estaminet De Gouden Aap", "city": "Antwerp", "lat": 51.23, "lon": 4.39, "demand": 5, "stock": 2},
    {"id": 5, "name": "Bar De Vagant", "city": "Antwerp", "lat": 51.22, "lon": 4.42, "demand": 6, "stock": 1},

    # Brussels area (5 venues)
    {"id": 6, "name": "Le Cirio", "city": "Brussels", "lat": 50.85, "lon": 4.35, "demand": 10, "stock": 2},
    {"id": 7, "name": "À la Mort Subite", "city": "Brussels", "lat": 50.85, "lon": 4.36, "demand": 8, "stock": 1},
    {"id": 8, "name": "Café Métropole", "city": "Brussels", "lat": 50.86, "lon": 4.35, "demand": 6, "stock": 0},
    {"id": 9, "name": "Le Greenwich", "city": "Brussels", "lat": 50.85, "lon": 4.34, "demand": 7, "stock": 3},
    {"id": 10, "name": "Moeder Lambic Original", "city": "Brussels", "lat": 50.83, "lon": 4.34, "demand": 5, "stock": 1},

    # Ghent area (4 venues)
    {"id": 11, "name": "Het Waterhuis aan de Bierkant", "city": "Ghent", "lat": 51.05, "lon": 3.72, "demand": 8, "stock": 2},
    {"id": 12, "name": "Café De Trollekelder", "city": "Ghent", "lat": 51.06, "lon": 3.73, "demand": 6, "stock": 1},
    {"id": 13, "name": "Dreupelkot", "city": "Ghent", "lat": 51.05, "lon": 3.73, "demand": 4, "stock": 0},
    {"id": 14, "name": "Gruut Stadsbrouwerij", "city": "Ghent", "lat": 51.04, "lon": 3.72, "demand": 7, "stock": 2},

    # Bruges area (3 venues)
    {"id": 15, "name": "Café 't Brugs Beertje", "city": "Bruges", "lat": 51.21, "lon": 3.23, "demand": 7, "stock": 1},
    {"id": 16, "name": "De Garre", "city": "Bruges", "lat": 51.21, "lon": 3.22, "demand": 5, "stock": 0},
    {"id": 17, "name": "Cambrinus", "city": "Bruges", "lat": 51.20, "lon": 3.23, "demand": 8, "stock": 2},

    # Leuven area (3 venues)
    {"id": 18, "name": "Café Den Biull", "city": "Leuven", "lat": 50.88, "lon": 4.70, "demand": 6, "stock": 1},
    {"id": 19, "name": "De Blauwe Kater", "city": "Leuven", "lat": 50.88, "lon": 4.71, "demand": 8, "stock": 2},
    {"id": 20, "name": "Domus Brouwerij", "city": "Leuven", "lat": 50.87, "lon": 4.70, "demand": 5, "stock": 0},

    # Mechelen area (2 venues)
    {"id": 21, "name": "Het Anker Brouwerij", "city": "Mechelen", "lat": 51.03, "lon": 4.48, "demand": 7, "stock": 2},
    {"id": 22, "name": "Café De Vansen", "city": "Mechelen", "lat": 51.02, "lon": 4.49, "demand": 5, "stock": 1},

    # Hasselt area (2 venues)
    {"id": 23, "name": "Café Dôme", "city": "Hasselt", "lat": 50.93, "lon": 5.34, "demand": 6, "stock": 1},
    {"id": 24, "name": "De Gouverneur", "city": "Hasselt", "lat": 50.93, "lon": 5.33, "demand": 5, "stock": 0},

    # Kortrijk area (2 venues)
    {"id": 25, "name": "Bar Le Fût", "city": "Kortrijk", "lat": 50.83, "lon": 3.27, "demand": 6, "stock": 2},
    {"id": 26, "name": "Den Trap", "city": "Kortrijk", "lat": 50.82, "lon": 3.26, "demand": 6, "stock": 1},

    # Ostend (2 venues)
    {"id": 27, "name": "Botteltje", "city": "Ostend", "lat": 51.22, "lon": 2.92, "demand": 7, "stock": 1},
    {"id": 28, "name": "Café De Burbure", "city": "Ostend", "lat": 51.23, "lon": 2.91, "demand": 5, "stock": 0},

    # Turnhout (1 venue)
    {"id": 29, "name": "De Zwaan", "city": "Turnhout", "lat": 51.32, "lon": 4.95, "demand": 5, "stock": 2},

    # Sint-Niklaas (1 venue)
    {"id": 30, "name": "Café Den Hoek", "city": "Sint-Niklaas", "lat": 51.16, "lon": 4.15, "demand": 6, "stock": 1},

    # Lier - BORDER venue (between Mechelen and Antwerp coverage)
    {"id": 31, "name": "Den Bansen", "city": "Lier", "lat": 51.13, "lon": 4.57, "demand": 5, "stock": 1, "border": True},

    # Dendermonde (1 venue)
    {"id": 32, "name": "Café 't Veer", "city": "Dendermonde", "lat": 51.03, "lon": 4.10, "demand": 6, "stock": 2},

    # Aalst - BORDER venue (between Ghent and Brussels)
    {"id": 33, "name": "De Carillon", "city": "Aalst", "lat": 50.94, "lon": 4.04, "demand": 7, "stock": 1, "border": True},

    # Roeselare (1 venue)
    {"id": 34, "name": "Café De Vrede", "city": "Roeselare", "lat": 50.95, "lon": 3.12, "demand": 5, "stock": 0},

    # Smaller towns
    {"id": 35, "name": "In De Verzekering Tegen De Grote Dorst", "city": "Eizeringen", "lat": 50.77, "lon": 4.15, "demand": 5, "stock": 1},

    # Vilvoorde - BORDER venue (between Brussels and Mechelen)
    {"id": 36, "name": "Het Hof Van Rembrandt", "city": "Vilvoorde", "lat": 50.93, "lon": 4.43, "demand": 6, "stock": 0, "border": True},

    # Tienen (1 venue)
    {"id": 37, "name": "Den Stillen Gansen", "city": "Tienen", "lat": 50.81, "lon": 4.94, "demand": 6, "stock": 1},

    # Aarschot - BORDER venue (between Leuven and Hasselt)
    {"id": 38, "name": "Café Sint-Rochus", "city": "Aarschot", "lat": 50.99, "lon": 4.83, "demand": 5, "stock": 2, "border": True},

    # Waregem (1 venue)
    {"id": 39, "name": "Estaminet 't Oud Stadhuis", "city": "Waregem", "lat": 50.88, "lon": 3.42, "demand": 6, "stock": 1},

    # Genk (1 venue)
    {"id": 40, "name": "Café Bij Jansen", "city": "Genk", "lat": 50.97, "lon": 5.50, "demand": 5, "stock": 0},
]

# Verify total demand
_total_demand = sum(v["demand"] for v in VENUES)
assert 240 <= _total_demand <= 260, f"Total demand {_total_demand} outside target range 240-260"
assert len(VENUES) == 40, f"Expected 40 venues, got {len(VENUES)}"
