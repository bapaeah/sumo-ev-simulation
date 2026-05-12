#!/usr/bin/env python3
"""
SUMO EV Simulation: Marathalli to ETV Route
Simulates 5 electric vehicles with different battery capacities
Tracks State of Charge (SOC) and Velocity in real-time
"""

import os
import sys
import csv
from datetime import datetime
from pathlib import Path

# Add SUMO tools to path
if 'SUMO_HOME' in os.environ:
    tools = os.path.join(os.environ['SUMO_HOME'], 'tools')
    sys.path.append(tools)
else:
    print("Please set SUMO_HOME environment variable")
    sys.exit(1)

import traci

# Configuration
SUMO_CONFIG = os.path.join(os.path.dirname(__file__), '..', 'config', 'simulation.sumocfg')
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), '..', 'output')
SIMULATION_TIME = 600  # 10 minutes

# EV Specifications
EV_SPECS = {
    'ev_01': {'capacity': 40, 'initial_soc': 80},
    'ev_02': {'capacity': 60, 'initial_soc': 85},
    'ev_03': {'capacity': 75, 'initial_soc': 90},
    'ev_04': {'capacity': 50, 'initial_soc': 70},
    'ev_05': {'capacity': 55, 'initial_soc': 75}
}

# Consumption rate (kWh per km)
CONSUMPTION_RATE = 0.15


class EVSimulation:
    def __init__(self):
        self.output_dir = OUTPUT_DIR
        self.create_output_directory()
        self.initialize_csv_files()
        self.ev_data = {ev_id: {'soc': specs['initial_soc'], 'energy_consumed': 0.0, 
                                 'distance': 0.0, 'capacity': specs['capacity']}
                       for ev_id, specs in EV_SPECS.items()}
        self.timestep = 0
        
    def create_output_directory(self):
        """Create output directory if it doesn't exist"""
        Path(self.output_dir).mkdir(parents=True, exist_ok=True)
        print(f"[INFO] Output directory: {self.output_dir}")
        
    def initialize_csv_files(self):
        """Initialize CSV files for data logging"""
        # State of Charge CSV
        soc_file = os.path.join(self.output_dir, 'ev_state_of_charge.csv')
        with open(soc_file, 'w', newline='') as f:
            writer = csv.writer(f)
            header = ['Timestamp(s)', 'Time(HH:MM:SS)'] + list(EV_SPECS.keys())
            writer.writerow(header)
            
        # Velocity CSV
        vel_file = os.path.join(self.output_dir, 'ev_velocity.csv')
        with open(vel_file, 'w', newline='') as f:
            writer = csv.writer(f)
            header = ['Timestamp(s)', 'Time(HH:MM:SS)'] + list(EV_SPECS.keys())
            writer.writerow(header)
            
        # Position CSV
        pos_file = os.path.join(self.output_dir, 'ev_position.csv')
        with open(pos_file, 'w', newline='') as f:
            writer = csv.writer(f)
            header = ['Timestamp(s)', 'Time(HH:MM:SS)', 'VehicleID', 'X_Position', 'Y_Position']
            writer.writerow(header)
            
        # Energy consumption CSV
        energy_file = os.path.join(self.output_dir, 'ev_energy_consumption.csv')
        with open(energy_file, 'w', newline='') as f:
            writer = csv.writer(f)
            header = ['Timestamp(s)', 'Time(HH:MM:SS)', 'VehicleID', 'Speed(km/h)', 'Distance(km)', 'Energy_Consumed(kWh)']
            writer.writerow(header)
    
    def format_time(self, seconds):
        """Convert seconds to HH:MM:SS format"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    
    def update_soc(self, vehicle_id, speed, dt=1.0):
        """Update State of Charge based on speed and distance traveled"""
        # Distance in km (speed is in m/s, dt is in seconds)
        distance = (speed * dt) / 1000.0
        # Energy consumed in kWh
        energy_consumed = distance * CONSUMPTION_RATE
        
        self.ev_data[vehicle_id]['distance'] += distance
        self.ev_data[vehicle_id]['energy_consumed'] += energy_consumed
        
        # Calculate remaining energy
        initial_energy = self.ev_data[vehicle_id]['capacity'] * (EV_SPECS[vehicle_id]['initial_soc'] / 100)
        remaining_energy = initial_energy - self.ev_data[vehicle_id]['energy_consumed']
        
        # Calculate SOC percentage
        soc = (remaining_energy / self.ev_data[vehicle_id]['capacity']) * 100
        soc = max(0, min(100, soc))  # Clamp between 0 and 100
        self.ev_data[vehicle_id]['soc'] = soc
        
        return soc, distance, energy_consumed
    
    def log_soc_and_velocity(self, vehicles):
        """Log State of Charge and Velocity to CSV"""
        soc_file = os.path.join(self.output_dir, 'ev_state_of_charge.csv')
        vel_file = os.path.join(self.output_dir, 'ev_velocity.csv')
        
        time_formatted = self.format_time(self.timestep)
        
        # Prepare SOC data
        soc_row = [self.timestep, time_formatted]
        vel_row = [self.timestep, time_formatted]
        
        for ev_id in EV_SPECS.keys():
            if ev_id in vehicles:
                soc = self.ev_data[ev_id]['soc']
                speed = vehicles[ev_id]['speed']
                soc_row.append(f"{soc:.2f}")
                vel_row.append(f"{speed:.2f}")
            else:
                soc_row.append("N/A")
                vel_row.append("N/A")
        
        # Append to CSV files
        with open(soc_file, 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(soc_row)
        
        with open(vel_file, 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(vel_row)
    
    def log_position(self, vehicles):
        """Log vehicle positions to CSV"""
        pos_file = os.path.join(self.output_dir, 'ev_position.csv')
        time_formatted = self.format_time(self.timestep)
        
        with open(pos_file, 'a', newline='') as f:
            writer = csv.writer(f)
            for ev_id, data in vehicles.items():
                writer.writerow([self.timestep, time_formatted, ev_id, f"{data['x']:.2f}", f"{data['y']:.2f}"])
    
    def log_energy_consumption(self, vehicles):
        """Log energy consumption details to CSV"""
        energy_file = os.path.join(self.output_dir, 'ev_energy_consumption.csv')
        time_formatted = self.format_time(self.timestep)
        
        with open(energy_file, 'a', newline='') as f:
            writer = csv.writer(f)
            for ev_id, data in vehicles.items():
                speed_kmh = data['speed'] * 3.6  # Convert m/s to km/h
                writer.writerow([
                    self.timestep,
                    time_formatted,
                    ev_id,
                    f"{speed_kmh:.2f}",
                    f"{self.ev_data[ev_id]['distance']:.2f}",
                    f"{self.ev_data[ev_id]['energy_consumed']:.2f}"
                ])
    
    def print_console_output(self, vehicles):
        """Print real-time console output"""
        time_formatted = self.format_time(self.timestep)
        
        print(f"\n{'='*120}")
        print(f"Timestamp: {self.timestep}s ({time_formatted})")
        print(f"{'='*120}")
        print(f"{'Vehicle ID':<12} {'Speed(km/h)':<15} {'SOC(%)':<12} {'Battery(kWh)':<18} {'Distance(km)':<15} {'Status':<15}")
        print(f"{'-'*120}")
        
        for ev_id, data in vehicles.items():
            speed_kmh = data['speed'] * 3.6
            soc = self.ev_data[ev_id]['soc']
            remaining_energy = (soc / 100) * self.ev_data[ev_id]['capacity']
            distance = self.ev_data[ev_id]['distance']
            
            # Status based on SOC
            if soc > 50:
                status = "HEALTHY"
            elif soc > 20:
                status = "WARNING"
            else:
                status = "CRITICAL"
            
            print(f"{ev_id:<12} {speed_kmh:<15.2f} {soc:<12.2f} {remaining_energy:<18.2f} {distance:<15.2f} {status:<15}")
    
    def run_simulation(self):
        """Run the SUMO simulation"""
        print("\n" + "="*120)
        print(" SUMO EV SIMULATION: Marathalli to ETV Route")
        print("="*120)
        print(f"Start Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Simulation Duration: {SIMULATION_TIME} seconds (10 minutes)")
        print(f"Output Directory: {self.output_dir}")
        print("="*120 + "\n")
        
        try:
            # Start SUMO simulation
            sumo_cmd = ['sumo', '-c', SUMO_CONFIG, '--step-length', '1.0', 
                       '--no-step-log', '--xml-validation', 'never']
            
            traci.start(sumo_cmd)
            print("[INFO] SUMO simulation started successfully\n")
            
            # Simulation loop
            while traci.simulation.getTime() < SIMULATION_TIME:
                self.timestep = int(traci.simulation.getTime())
                
                # Get active vehicles
                vehicle_ids = traci.vehicle.getIDList()
                vehicles = {}
                
                for vehicle_id in vehicle_ids:
                    if vehicle_id in EV_SPECS:
                        try:
                            speed = traci.vehicle.getSpeed(vehicle_id)
                            x, y = traci.vehicle.getPosition(vehicle_id)
                            
                            # Update SOC
                            soc, distance, energy = self.update_soc(vehicle_id, speed, dt=1.0)
                            
                            vehicles[vehicle_id] = {
                                'speed': speed,
                                'x': x,
                                'y': y
                            }
                        except traci.TraCIException:
                            continue
                
                # Log data every second
                if vehicles:
                    self.log_soc_and_velocity(vehicles)
                    self.log_position(vehicles)
                    self.log_energy_consumption(vehicles)
                    
                    # Print console output every 10 seconds
                    if self.timestep % 10 == 0:
                        self.print_console_output(vehicles)
                
                # Perform step
                traci.simulationStep()
            
            # Final output
            self.print_console_output(vehicles)
            print("\n" + "="*120)
            print("[SUCCESS] Simulation completed successfully!")
            print("="*120 + "\n")
            
            # Summary
            print("\nFINAL SUMMARY:")
            print("-" * 120)
            for ev_id, specs in EV_SPECS.items():
                soc = self.ev_data[ev_id]['soc']
                energy_consumed = self.ev_data[ev_id]['energy_consumed']
                distance = self.ev_data[ev_id]['distance']
                remaining_energy = (soc / 100) * specs['capacity']
                print(f"{ev_id}: Distance: {distance:.2f}km | Energy Consumed: {energy_consumed:.2f}kWh | Final SOC: {soc:.2f}% | Remaining Energy: {remaining_energy:.2f}kWh")
            
            print("\nOutput Files Generated:")
            for file in os.listdir(self.output_dir):
                if file.endswith('.csv'):
                    file_path = os.path.join(self.output_dir, file)
                    print(f"  - {file} ({os.path.getsize(file_path)} bytes)")
            
            print("\n" + "="*120 + "\n")
            
        except Exception as e:
            print(f"[ERROR] Simulation failed: {e}")
            import traceback
            traceback.print_exc()
        finally:
            traci.close()


def main():
    # Check if config file exists
    if not os.path.exists(SUMO_CONFIG):
        print(f"[ERROR] Configuration file not found: {SUMO_CONFIG}")
        sys.exit(1)
    
    # Run simulation
    sim = EVSimulation()
    sim.run_simulation()


if __name__ == '__main__':
    main()
