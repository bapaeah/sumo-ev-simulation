#!/usr/bin/env python3
"""
Plots traffic information over time from output/traffic_info.csv.
Generates a high-quality 3-panel visualization showing vehicle count density,
traffic speed profiles, and pedestrian activity.
"""

import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# Directories
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_DIR = os.path.join(BASE_DIR, 'output')
CSV_PATH = os.path.join(OUTPUT_DIR, 'traffic_info.csv')
PLOT_PATH = os.path.join(OUTPUT_DIR, 'traffic_info_plots.png')

# Color palette
COLOR_TOTAL_VEH = '#2C3E50'      # Dark Blue-Gray
COLOR_BG_VEH = '#2980B9'         # Blue
COLOR_EV_VEH = '#E74C3C'         # Red
COLOR_BG_SPEED = '#16A085'       # Dark Teal
COLOR_PEDESTRIANS = '#8E44AD'    # Purple

def load_and_clean_csv(file_path):
    df = pd.read_csv(file_path)
    # Convert numerical columns to float
    for col in df.columns:
        if col not in ['Time(Time)', 'Time(HH:MM:SS)']:
            df[col] = pd.to_numeric(df[col], errors='coerce')
    return df

def generate_traffic_plots():
    print(f"[INFO] Loading traffic info from: {CSV_PATH}...")
    if not os.path.exists(CSV_PATH):
        print(f"[ERROR] Traffic info CSV missing. Please run simulation first.")
        return
        
    df = load_and_clean_csv(CSV_PATH)
    
    # Convert Timestamp(s) to Minutes for X-axis
    time_min = df['Timestamp(s)'] / 60.0
    
    # Create 3-panel plot (3 rows, 1 col)
    fig, (ax_veh, ax_speed, ax_ped) = plt.subplots(3, 1, figsize=(12, 14), sharex=True, dpi=150)
    
    # --- PANEL 1: Vehicle Counts (Density) ---
    ax_veh.plot(time_min, df['Total_Vehicles'], label="Total Vehicles in Network", color=COLOR_TOTAL_VEH, linewidth=2.2)
    ax_veh.plot(time_min, df['Background_Traffic_Count'], label="Background Traffic", color=COLOR_BG_VEH, linewidth=1.8, alpha=0.85)
    ax_veh.plot(time_min, df['EV_Count'], label="Active Electric Vehicles (EVs)", color=COLOR_EV_VEH, linewidth=2.0)
    
    ax_veh.set_title("Network Vehicle Counts (Traffic Density)", fontsize=13, fontweight='bold', pad=8)
    ax_veh.set_ylabel("Vehicle Count", fontsize=11, fontweight='bold')
    ax_veh.grid(True, linestyle='--', alpha=0.5)
    ax_veh.legend(loc='upper left', frameon=True, facecolor='white', framealpha=0.9)
    
    # Highlight peak congestion
    peak_veh = df['Total_Vehicles'].max()
    peak_time_min = time_min[df['Total_Vehicles'].idxmax()]
    ax_veh.annotate(f'Peak Congestion: {peak_veh} vehicles', 
                    xy=(peak_time_min, peak_veh), 
                    xytext=(peak_time_min - 6, peak_veh - 50),
                    arrowprops=dict(facecolor='black', shrink=0.08, width=1.5, headwidth=6),
                    fontweight='bold', fontsize=9)
    
    # --- PANEL 2: Average Background Speed Profile (Flow) ---
    ax_speed.plot(time_min, df['Avg_Background_Speed(km/h)'], label="Average Background Traffic Speed", color=COLOR_BG_SPEED, linewidth=2.0)
    
    # Calculate overall average background speed
    mean_speed = df['Avg_Background_Speed(km/h)'].mean()
    ax_speed.axhline(mean_speed, color=COLOR_BG_SPEED, linestyle='--', linewidth=1.5, alpha=0.7, 
                     label=f"Overall Avg Speed: {mean_speed:.2f} km/h")
    
    ax_speed.set_title("Background Traffic Speed Profile (Flow & Congestion)", fontsize=13, fontweight='bold', pad=8)
    ax_speed.set_ylabel("Speed (km/h)", fontsize=11, fontweight='bold')
    ax_speed.set_ylim(0, 60)
    ax_speed.grid(True, linestyle='--', alpha=0.5)
    ax_speed.legend(loc='lower left', frameon=True, facecolor='white', framealpha=0.9)
    
    # --- PANEL 3: Active Pedestrians (Activity) ---
    ax_ped.plot(time_min, df['Active_Pedestrians'], label="Active Walking Pedestrians", color=COLOR_PEDESTRIANS, linewidth=2.0)
    ax_ped.set_title("Pedestrian Crossing Activity over Time", fontsize=13, fontweight='bold', pad=8)
    ax_ped.set_ylabel("Pedestrian Count", fontsize=11, fontweight='bold')
    ax_ped.set_xlabel("Time (minutes)", fontsize=11, fontweight='bold')
    ax_ped.set_ylim(-0.5, max(5, df['Active_Pedestrians'].max() + 1))
    ax_ped.grid(True, linestyle='--', alpha=0.5)
    ax_ped.legend(loc='upper right', frameon=True, facecolor='white', framealpha=0.9)
    
    # Title of the overall figure
    fig.suptitle("Bengaluru Traffic & Pedestrian Environment Analysis\n35-Minute Real-Time Simulation Cycle (Marathalli to ETV Round-Trip Route)", 
                 fontsize=16, fontweight='bold', y=0.96)
    
    plt.tight_layout(rect=[0, 0.02, 1, 0.93])
    
    # Save plot
    plt.savefig(PLOT_PATH, bbox_inches='tight')
    plt.close()
    print(f"[SUCCESS] Saved traffic info plot to: {PLOT_PATH}")

if __name__ == '__main__':
    generate_traffic_plots()
