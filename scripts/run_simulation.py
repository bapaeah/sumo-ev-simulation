#!/usr/bin/env python3
"""
SUMO EV Simulation: Marathalli to ETV Route
Simulates 5 electric vehicles with different battery capacities
Tracks State of Charge (SOC) and Velocity in real-time
Captures colored screenshots with vehicle positions and status
"""

import os
import sys
import csv
import subprocess
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import FancyBboxPatch, Circle, Polygon
import numpy as np
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
SCREENSHOT_DIR = os.path.join(OUTPUT_DIR, 'screenshots')
SIMULATION_TIME = 2100  # 35 minutes
SCREENSHOT_INTERVAL = 30  # Take screenshot every 30 seconds

# EV Specifications
EV_SPECS = {
    'ev_01': {'capacity': 40, 'initial_soc': 80, 'color': '#FF6B6B'},    # Red
    'ev_02': {'capacity': 60, 'initial_soc': 85, 'color': '#4ECDC4'},    # Teal
    'ev_03': {'capacity': 75, 'initial_soc': 90, 'color': '#45B7D1'},    # Blue
    'ev_04': {'capacity': 50, 'initial_soc': 70, 'color': '#FFA07A'},    # Light Salmon
    'ev_05': {'capacity': 55, 'initial_soc': 75, 'color': '#98D8C8'}     # Mint
}

# Consumption rate (kWh per km)
CONSUMPTION_RATE = 0.15

# Network bounds
NETWORK_X_MIN, NETWORK_X_MAX = 0, 12000
NETWORK_Y_MIN, NETWORK_Y_MAX = 0, 5000


class EVSimulation:
    def __init__(self):
        self.output_dir = OUTPUT_DIR
        self.screenshot_dir = SCREENSHOT_DIR
        self.create_output_directory()
        self.initialize_csv_files()
        self.ev_data = {ev_id: {'soc': specs['initial_soc'], 'energy_consumed': 0.0, 
                                 'distance': 0.0, 'capacity': specs['capacity']}
                       for ev_id, specs in EV_SPECS.items()}
        self.timestep = 0
        self.screenshot_count = 0
        self.vehicle_positions = {}  # Store vehicle positions for visualization
        self.max_vehicles = 0
        self.max_pedestrians = 0
        self.traffic_speed_samples = []
        
    def create_output_directory(self):
        """Create output directory if it doesn't exist"""
        Path(self.output_dir).mkdir(parents=True, exist_ok=True)
        Path(self.screenshot_dir).mkdir(parents=True, exist_ok=True)
        print(f"[INFO] Output directory: {self.output_dir}")
        print(f"[INFO] Screenshot directory: {self.screenshot_dir}")
        
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
            
        # Traffic Info CSV
        traffic_file = os.path.join(self.output_dir, 'traffic_info.csv')
        with open(traffic_file, 'w', newline='') as f:
            writer = csv.writer(f)
            header = ['Timestamp(s)', 'Time(HH:MM:SS)', 'Total_Vehicles', 'EV_Count', 'Background_Traffic_Count', 'Avg_Background_Speed(km/h)', 'Active_Pedestrians']
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
                speed_kmh = vehicles[ev_id]['speed'] * 3.6
                soc_row.append(f"{soc:.2f}")
                vel_row.append(f"{speed_kmh:.2f}")
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
                
    def log_traffic_info(self, total_vehicles, ev_count, bg_count, avg_bg_speed, active_pedestrians):
        """Log general traffic and pedestrian metrics to CSV"""
        traffic_file = os.path.join(self.output_dir, 'traffic_info.csv')
        time_formatted = self.format_time(self.timestep)
        
        with open(traffic_file, 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                self.timestep,
                time_formatted,
                total_vehicles,
                ev_count,
                bg_count,
                f"{avg_bg_speed:.2f}",
                active_pedestrians
            ])
    
    def draw_car_symbol(self, ax, x, y, angle, color, label):
        """Draw a car symbol at position (x, y) with given angle and color"""
        # Car body dimensions
        car_length = 150
        car_width = 80
        
        # Convert angle to radians (SUMO uses degrees)
        angle_rad = np.radians(angle)
        
        # Rotate the patch using an Affine transform
        import matplotlib.transforms as mtransforms
        t = mtransforms.Affine2D().rotate_deg_around(x, y, angle) + ax.transData
        
        # Car body (rectangle)
        car_body = FancyBboxPatch(
            (x - car_length/2, y - car_width/2),
            car_length,
            car_width,
            boxstyle="round,pad=15",
            facecolor=color,
            edgecolor='black',
            linewidth=2,
            alpha=0.8,
            transform=t
        )
        ax.add_patch(car_body)
        
        # Draw direction arrow
        arrow_length = 200
        arrow_x = x + arrow_length * np.cos(angle_rad)
        arrow_y = y + arrow_length * np.sin(angle_rad)
        ax.arrow(x, y, arrow_x - x, arrow_y - y, 
                head_width=40, head_length=50, fc='darkgray', ec='black', alpha=0.5)
        
        # Add label
        ax.text(x, y - car_width/2 - 100, label, 
               ha='center', va='top', fontsize=9, fontweight='bold',
               bbox=dict(boxstyle='round', facecolor=color, alpha=0.7))
    
    def capture_colored_screenshot(self, vehicles):
        """Capture colored screenshot with vehicle positions and status"""
        try:
            time_formatted = self.format_time(self.timestep)
            filename = f"simulation_t{self.timestep:04d}_{time_formatted.replace(':', '-')}.png"
            filepath = os.path.join(self.screenshot_dir, filename)
            
            # Create figure with high DPI for better quality
            fig, ax = plt.subplots(figsize=(16, 7), dpi=100)
            
            # Set network bounds
            ax.set_xlim(NETWORK_X_MIN - 500, NETWORK_X_MAX + 500)
            ax.set_ylim(NETWORK_Y_MIN - 500, NETWORK_Y_MAX + 500)
            ax.set_aspect('equal')
            
            # Draw road network
            self.draw_road_network(ax)
            
            # Draw vehicles
            for ev_id, data in vehicles.items():
                if ev_id in EV_SPECS:
                    speed_kmh = data['speed'] * 3.6
                    soc = self.ev_data[ev_id]['soc']
                    remaining_energy = (soc / 100) * EV_SPECS[ev_id]['capacity']
                    
                    # Get vehicle angle
                    angle = data.get('angle', 0)
                    
                    # Draw car
                    self.draw_car_symbol(
                        ax, data['x'], data['y'], angle,
                        EV_SPECS[ev_id]['color'],
                        f"{ev_id}\n{soc:.1f}%\n{speed_kmh:.1f}km/h"
                    )
            
            # Add title and info
            title = f"SUMO EV Simulation - Marathalli to ETV Route\nTimestamp: {self.timestep}s ({time_formatted})"
            ax.set_title(title, fontsize=16, fontweight='bold', pad=20)
            
            # Add grid
            ax.grid(True, alpha=0.3, linestyle='--')
            
            # Add legend
            legend_text = "EV Status Legend:\n"
            legend_text += "🟢 HEALTHY (SOC > 50%)\n"
            legend_text += "🟡 WARNING (20% < SOC ≤ 50%)\n"
            legend_text += "🔴 CRITICAL (SOC ≤ 20%)"
            
            ax.text(0.02, 0.98, legend_text, transform=ax.transAxes,
                   fontsize=10, verticalalignment='top',
                   bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))
            
            # Add axis labels
            ax.set_xlabel('X Coordinate (meters)', fontsize=12)
            ax.set_ylabel('Y Coordinate (meters)', fontsize=12)
            
            # Add vehicle info box
            info_text = "Current Vehicles:\n"
            for ev_id, data in vehicles.items():
                if ev_id in EV_SPECS:
                    soc = self.ev_data[ev_id]['soc']
                    speed_kmh = data['speed'] * 3.6
                    info_text += f"{ev_id}: {soc:.1f}% SOC, {speed_kmh:.1f} km/h\n"
            
            ax.text(0.98, 0.98, info_text, transform=ax.transAxes,
                   fontsize=9, verticalalignment='top', horizontalalignment='right',
                   bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.8))
            
            # Tight layout and save
            plt.tight_layout()
            plt.savefig(filepath, dpi=100, bbox_inches='tight')
            plt.close(fig)
            
            self.screenshot_count += 1
            print(f"  [SCREENSHOT] Captured: {filename}")
            
        except Exception as e:
            print(f"  [WARNING] Could not capture screenshot: {e}")
    
    def draw_road_network(self, ax):
        """Draw the road network on the plot"""
        # Define road edges
        roads = [
            # Main route
            {'start': (0, 0), 'end': (5000, 1500), 'name': 'Marathalli→Whitefield', 'color': '#E8E8E8'},
            {'start': (5000, 1500), 'end': (8500, 3200), 'name': 'Whitefield→Silk Board', 'color': '#E8E8E8'},
            {'start': (8500, 3200), 'end': (11000, 4500), 'name': 'Silk Board→ETV', 'color': '#E8E8E8'},
            # Return route
            {'start': (11000, 4500), 'end': (8500, 3200), 'name': 'ETV→Silk Board', 'color': '#F0F0F0'},
            {'start': (8500, 3200), 'end': (5000, 1500), 'name': 'Silk Board→Whitefield', 'color': '#F0F0F0'},
            {'start': (5000, 1500), 'end': (0, 0), 'name': 'Whitefield→Marathalli', 'color': '#F0F0F0'},
        ]
        
        # Draw roads
        for road in roads:
            x_coords = [road['start'][0], road['end'][0]]
            y_coords = [road['start'][1], road['end'][1]]
            ax.plot(x_coords, y_coords, color='#666666', linewidth=3, zorder=1)
            ax.fill_between(x_coords, y_coords, color=road['color'], alpha=0.5, zorder=0)
        
        # Draw junctions as circles
        junctions = [
            {'pos': (0, 0), 'name': 'Marathalli'},
            {'pos': (5000, 1500), 'name': 'Whitefield'},
            {'pos': (8500, 3200), 'name': 'Silk Board'},
            {'pos': (11000, 4500), 'name': 'ETV'},
        ]
        
        for junction in junctions:
            circle = Circle(junction['pos'], 150, color='#FFD700', ec='black', linewidth=2, zorder=3)
            ax.add_patch(circle)
            ax.text(junction['pos'][0], junction['pos'][1], junction['name'],
                   ha='center', va='center', fontsize=8, fontweight='bold')
    
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
        print(f"Screenshot Interval: Every {SCREENSHOT_INTERVAL} seconds")
        print(f"Output Directory: {self.output_dir}")
        print("="*120 + "\n")
        
        try:
            # Start SUMO simulation (headless for screenshot capture)
            sumo_cmd = ['sumo', '-c', SUMO_CONFIG, '--step-length', '1.0', 
                       '--no-step-log', '--xml-validation', 'never']
            
            traci.start(sumo_cmd)
            print("[INFO] SUMO simulation started successfully\n")
            
            # Simulation loop
            vehicles = {}
            while traci.simulation.getTime() < SIMULATION_TIME:
                self.timestep = int(traci.simulation.getTime())
                
                # Get active vehicles
                vehicle_ids = traci.vehicle.getIDList()
                total_vehicles = len(vehicle_ids)
                self.max_vehicles = max(self.max_vehicles, total_vehicles)
                
                # Get active pedestrians
                try:
                    person_ids = traci.person.getIDList()
                    active_pedestrians = len(person_ids)
                except traci.TraCIException:
                    active_pedestrians = 0
                self.max_pedestrians = max(self.max_pedestrians, active_pedestrians)
                
                vehicles = {}
                bg_speeds = []
                bg_count = 0
                ev_count = 0
                
                for vehicle_id in vehicle_ids:
                    if vehicle_id in EV_SPECS:
                        ev_count += 1
                        try:
                            speed = traci.vehicle.getSpeed(vehicle_id)
                            x, y = traci.vehicle.getPosition(vehicle_id)
                            angle = traci.vehicle.getAngle(vehicle_id)
                            
                            # Update SOC
                            soc, distance, energy = self.update_soc(vehicle_id, speed, dt=1.0)
                            
                            vehicles[vehicle_id] = {
                                'speed': speed,
                                'x': x,
                                'y': y,
                                'angle': angle
                            }
                        except traci.TraCIException:
                            continue
                    else:
                        bg_count += 1
                        try:
                            bg_speed = traci.vehicle.getSpeed(vehicle_id)
                            bg_speeds.append(bg_speed)
                        except traci.TraCIException:
                            continue
                
                avg_bg_speed_kmh = (sum(bg_speeds) / len(bg_speeds)) * 3.6 if bg_speeds else 0.0
                if bg_speeds:
                    self.traffic_speed_samples.append(avg_bg_speed_kmh)
                
                # Log traffic info every second
                self.log_traffic_info(total_vehicles, ev_count, bg_count, avg_bg_speed_kmh, active_pedestrians)
                
                # Log EV data every second
                if vehicles:
                    self.log_soc_and_velocity(vehicles)
                    self.log_position(vehicles)
                    self.log_energy_consumption(vehicles)
                    
                    # Print console output every 10 seconds
                    if self.timestep % 10 == 0:
                        self.print_console_output(vehicles)
                    
                    # Capture colored screenshot at specified interval
                    if self.timestep % SCREENSHOT_INTERVAL == 0 and self.timestep > 0:
                        self.capture_colored_screenshot(vehicles)
                
                # Perform step
                traci.simulationStep()
            
            # Final output and screenshot
            if vehicles:
                self.print_console_output(vehicles)
                self.capture_colored_screenshot(vehicles)
            
            print("\n" + "="*120)
            print("[SUCCESS] Simulation completed successfully!")
            print("="*120 + "\n")
            
            # Summary
            print("\nFINAL EV SUMMARY:")
            print("-" * 120)
            for ev_id, specs in EV_SPECS.items():
                soc = self.ev_data[ev_id]['soc']
                energy_consumed = self.ev_data[ev_id]['energy_consumed']
                distance = self.ev_data[ev_id]['distance']
                remaining_energy = (soc / 100) * specs['capacity']
                print(f"{ev_id}: Distance: {distance:.2f}km | Energy Consumed: {energy_consumed:.2f}kWh | Final SOC: {soc:.2f}% | Remaining Energy: {remaining_energy:.2f}kWh")
            
            print("\nTRAFFIC & PEDESTRIAN SUMMARY:")
            print("-" * 120)
            avg_traffic_speed_overall = sum(self.traffic_speed_samples) / len(self.traffic_speed_samples) if self.traffic_speed_samples else 0.0
            print(f"Peak Congestion (Max Active Vehicles): {self.max_vehicles}")
            print(f"Peak Pedestrian Count: {self.max_pedestrians}")
            print(f"Overall Average Background Traffic Speed: {avg_traffic_speed_overall:.2f} km/h")
            
            print("\nOutput Files Generated:")
            for file in sorted(os.listdir(self.output_dir)):
                if file.endswith('.csv'):
                    file_path = os.path.join(self.output_dir, file)
                    print(f"  - {file} ({os.path.getsize(file_path)} bytes)")
            
            print(f"\nScreenshots Captured: {self.screenshot_count}")
            screenshot_files = [f for f in os.listdir(self.screenshot_dir) if f.endswith('.png')]
            print(f"Screenshot Files: {len(screenshot_files)}")
            if screenshot_files:
                print("  Sample screenshots:")
                for screenshot in sorted(screenshot_files)[:5]:
                    print(f"    - {screenshot}")
                if len(screenshot_files) > 5:
                    print(f"    ... and {len(screenshot_files) - 5} more")
            
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
