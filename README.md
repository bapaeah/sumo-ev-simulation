# SUMO EV Simulation: Marathalli to ETV Route

This project simulates 5 electric vehicles (EVs) with different battery capacities traveling from Marathalli to ETV with traffic and pedestrians.

## Project Structure

```
sumo-ev-simulation/
├── network/
│   ├── marathalli_etv.net.xml
│   └── marathalli_etv.edg.xml
├── routes/
│   └── ev_routes.rou.xml
├── config/
│   └── simulation.sumocfg
├── scripts/
│   └── run_simulation.py
├── output/
│   └── (CSV files generated after simulation)
└── README.md
```

## EV Specifications

| EV ID | Battery Capacity (kWh) | Initial SOC (%) | Vehicle Type |
|-------|------------------------|-----------------|----------|
| ev_01 | 40                     | 80              | Small    |
| ev_02 | 60                     | 85              | Medium   |
| ev_03 | 75                     | 90              | Large    |
| ev_04 | 50                     | 70              | Medium   |
| ev_05 | 55                     | 75              | Medium   |

## Installation

```bash
# Install SUMO (Ubuntu/Debian)
sudo apt-get install sumo sumo-tools sumo-doc

# For macOS
brew install sumo

# Install Python dependencies
pip install -r requirements.txt
```

## Running the Simulation

```bash
python scripts/run_simulation.py
```

## Output

The simulation generates the following CSV files in the `output/` directory:

- `ev_state_of_charge.csv` - State of charge over time for each EV
- `ev_velocity.csv` - Velocity data for each EV
- `ev_position.csv` - Position (x, y coordinates) for each EV
- `simulation_summary.csv` - Overall simulation statistics

## Simulation Parameters

- **Duration**: 600 seconds (10 minutes)
- **Route**: Marathalli to ETV
- **Traffic**: Enabled with realistic congestion
- **Pedestrians**: Enabled on sidewalks
- **Update Interval**: 1 second

## Real-time Console Output

During simulation, you'll see real-time output showing:
- Timestamp
- Vehicle ID
- Speed (km/h)
- State of Charge (%)
- Position coordinates
- Energy consumption (kWh)
