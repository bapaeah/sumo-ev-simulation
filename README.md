# SUMO EV Simulation: Marathalli to ETV Route

This project simulates 5 electric vehicles (EVs) with different battery capacities traveling from Marathalli to ETV with traffic and pedestrians.

## Project Structure

```
sumo-ev-simulation/
├── network/
│   ├── marathalli_etv.nod.xml       # Node (junction) definitions
│   ├── marathalli_etv.edg.xml       # Edge (road) definitions
│   ├── marathalli_etv.net.xml       # Generated network file
│   ├── generate_network.netcfg      # netconvert configuration
│   └── generate_network.sh          # Network generation script
├── routes/
│   └── ev_routes.rou.xml            # Vehicle routes and flows
├── config/
│   └── simulation.sumocfg           # SUMO simulation configuration
├── scripts/
│   └── run_simulation.py            # Main simulation script
├── output/
│   ├── *.csv                        # CSV data files (generated)
│   └── screenshots/                 # Simulation screenshots (generated)
├── requirements.txt
├── .gitignore
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

### Prerequisites

1. **Install SUMO** (Ubuntu/Debian):
   ```bash
   sudo apt-get install sumo sumo-tools sumo-doc
   ```

   **macOS**:
   ```bash
   brew install sumo
   ```

2. **Install Python dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

## Setup & Running

### Step 1: Generate Network

First, generate the SUMO network file from node/edge definitions:

```bash
# Set SUMO_HOME environment variable
export SUMO_HOME=/usr/share/sumo  # Ubuntu/Debian
# OR
export SUMO_HOME=/usr/local/opt/sumo/share/sumo  # macOS

# Generate the network
cd network
chmod +x generate_network.sh
./generate_network.sh

# Return to root directory
cd ..
```

### Step 2: Run Simulation

```bash
python scripts/run_simulation.py
```

The simulation will:
- ✅ Run for 10 minutes (600 seconds)
- ✅ Display real-time vehicle data every 10 seconds in console
- ✅ Track velocity and state of charge for all 5 EVs
- ✅ Generate CSV files with detailed data
- ✅ Capture screenshots of the simulation every 30 seconds
- ✅ Include background traffic (600+ vehicles/hour)
- ✅ Include pedestrians on sidewalks

## Output

The simulation generates the following files in the `output/` directory:

### CSV Data Files

1. **ev_state_of_charge.csv** - State of charge (%) over time for each EV
2. **ev_velocity.csv** - Velocity (km/h) over time for each EV
3. **ev_position.csv** - X,Y coordinates for each EV at each timestep
4. **ev_energy_consumption.csv** - Distance traveled and energy consumed per EV

### Screenshots

All screenshots are saved in `output/screenshots/` directory with format:
```
simulation_t0000_00-00-00.png  (at 0 seconds)
simulation_t0030_00-00-30.png  (at 30 seconds)
simulation_t0060_00-01-00.png  (at 60 seconds)
... (every 30 seconds until end)
```

## Simulation Parameters

- **Duration**: 600 seconds (10 minutes)
- **Route**: Marathalli → Whitefield → Silk Board → ETV (round trip)
- **Traffic**: Enabled with realistic congestion (600-1500 vehicles/hour)
- **Pedestrians**: 37 pedestrians walking on sidewalks
- **Screenshot Interval**: Every 30 seconds
- **Update Interval**: 1 second
- **Energy Consumption**: 0.15 kWh/km

## Real-time Console Output

During simulation, you'll see output like:

```
============================================================================================================================
Timestamp: 60s (00:01:00)
============================================================================================================================
Vehicle ID   Speed(km/h)     SOC(%)       Battery(kWh)       Distance(km)    Status         
────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
ev_01        42.50           78.45        31.38              1.82            HEALTHY        
ev_02        38.60           84.20        50.52              1.55            HEALTHY        
ev_03        45.20           89.10        66.83              1.92            HEALTHY        
ev_04        41.30           68.90        34.45              1.75            WARNING        
ev_05        39.80           73.50        40.43              1.68            WARNING        
```

## Vehicle Status Indicators

- **HEALTHY**: SOC > 50%
- **WARNING**: 20% < SOC ≤ 50%
- **CRITICAL**: SOC ≤ 20%

## Data Analysis

After the simulation completes, analyze the generated CSV files:

```python
import pandas as pd

# Read SOC data
soc_df = pd.read_csv('output/ev_state_of_charge.csv')
print(soc_df.head())

# Read velocity data
vel_df = pd.read_csv('output/ev_velocity.csv')
print(vel_df.head())

# Plot SOC vs Time
import matplotlib.pyplot as plt
plt.figure(figsize=(12, 6))
for col in ['ev_01', 'ev_02', 'ev_03', 'ev_04', 'ev_05']:
    plt.plot(soc_df['Timestamp(s)'], soc_df[col], label=col)
plt.xlabel('Time (seconds)')
plt.ylabel('State of Charge (%)')
plt.title('EV State of Charge Over Time')
plt.legend()
plt.grid(True)
plt.show()
```

## Troubleshooting

### SUMO_HOME not set
```bash
export SUMO_HOME=/usr/share/sumo  # Ubuntu/Debian
# OR
export SUMO_HOME=/usr/local/opt/sumo/share/sumo  # macOS
```

### Network file not found
```bash
cd network
./generate_network.sh
cd ..
```

### GUI issues with screenshots
Make sure you have a display server running. On headless systems:
```bash
export DISPLAY=:0  # For X11 systems
```

## Dependencies

- **SUMO 1.16+** - Traffic simulation
- **Python 3.8+**
- **traci** - SUMO TraCI Python binding
- **pandas** - Data analysis
- **numpy** - Numerical computing
- **Pillow** - Image processing

## License

MIT License - Feel free to use and modify for your needs.

## Contact

For questions or issues, please create an issue in the repository.
