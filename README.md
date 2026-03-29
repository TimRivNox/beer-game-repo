# Beer Route Optimizer

Interactive logistics planning demo built with Streamlit. Play as a logistics manager for Duvel Moortgat's Belgian distribution network — place warehouses, plan delivery routes, then see how an automated optimizer compares to your decisions.

## Quick Start

```bash
pip install -r requirements.txt
streamlit run beer_route_optimizer/app.py
```

## How It Works

### Phase 1: Place Your Warehouses
Choose 3 warehouse locations from 8 Belgian cities. Balance operating costs, capacity, and geographic coverage for 40 venues across Flanders and Brussels.

### Phase 2: Plan Your Routes
Assign venues to warehouses and review delivery routes. Reassign venues to balance capacity and minimize driving distance.

### Phase 3: Results & Optimizer Comparison
Compare your plan against an automated optimizer that uses:
- Brute-force evaluation of all 56 warehouse combinations
- Clarke-Wright savings algorithm for route construction
- 2-opt local search for route improvement
- Border venue reassignment for fine-tuning

## Tech Stack

- **Streamlit** — Interactive web UI
- **Folium** + **streamlit-folium** — Interactive maps
- **Python** — All optimization algorithms implemented from scratch

## File Structure

```
beer_route_optimizer/
├── app.py            # Main Streamlit app (3-phase game flow)
├── data.py           # Hardcoded venue, brewery, and warehouse data
├── optimizer.py      # Clarke-Wright, 2-opt, brute-force optimizer
├── map_builder.py    # Folium map construction
├── scoring.py        # Cost calculations
└── utils.py          # Haversine distance, routing helpers
```

Built by [Rivnox](https://rivnox.ai)
