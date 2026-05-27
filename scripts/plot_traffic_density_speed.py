#!/usr/bin/env python3
"""
Generates a premium, publication-grade traffic comparison plot.
Plots a 1-minute (60-second) window comparing:
  1. Traffic Volume (All Traffic / Total Vehicles count)
  2. Average Traffic Speed (km/h)
Across three conditions: Low Traffic, Medium Traffic, and Heavy Traffic.
"""

import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# Directories
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_DIR = os.path.join(BASE_DIR, 'output')
CSV_PATH = os.path.join(OUTPUT_DIR, 'traffic_info.csv')
PLOT_PATH = os.path.join(OUTPUT_DIR, 'traffic_density_speed_comparison.png')

# Premium color scheme
COLOR_LOW = '#2ECC71'    # Emerald Green for Low Traffic
COLOR_MED = '#F39C12'    # Vibrant Orange for Medium Traffic
COLOR_HEAVY = '#E74C3C'  # Crimson Red for Heavy Traffic

def load_and_clean_data(file_path):
    df = pd.read_csv(file_path)
    for col in df.columns:
        if col not in ['Time(Time)', 'Time(HH:MM:SS)']:
            df[col] = pd.to_numeric(df[col], errors='coerce')
    return df

def generate_density_speed_plot():
    print(f"[INFO] Loading traffic data from {CSV_PATH}...")
    if not os.path.exists(CSV_PATH):
        print("[ERROR] Traffic info CSV missing. Please run run_marl_simulation.py first.")
        return
        
    df = load_and_clean_data(CSV_PATH)
    
    # Representative stable 1-minute windows (60 seconds) determined from the simulation log:
    # 1. Low Traffic: index 109 to 168 (mean total active vehicles: ~64)
    # 2. Medium Traffic: index 655 to 714 (mean total active vehicles: ~290)
    # 3. Heavy Traffic: index 1084 to 1143 (mean total active vehicles: ~347)
    idx_low, idx_med, idx_heavy = 109, 655, 1084
    
    df_low = df.iloc[idx_low:idx_low+60].reset_index(drop=True)
    df_med = df.iloc[idx_med:idx_med+60].reset_index(drop=True)
    df_heavy = df.iloc[idx_heavy:idx_heavy+60].reset_index(drop=True)
    
    time_sec = np.arange(1, 61)  # 1 to 60 seconds
    
    # Initialize the plot with premium aesthetics
    plt.rcParams.update({
        'font.size': 14,
        'axes.labelsize': 16,
        'xtick.labelsize': 14,
        'ytick.labelsize': 14,
        'legend.fontsize': 13,
        'figure.titlesize': 18
    })
    
    fig, (ax_vol, ax_speed) = plt.subplots(1, 2, figsize=(18, 8), dpi=150)
    
    # ----------------------------------------------------
    # PANEL 1: Traffic Volume Density (Total Active Vehicles)
    # ----------------------------------------------------
    ax_vol.plot(time_sec, df_low['Total_Vehicles'], color=COLOR_LOW, linewidth=3.0, label=f"Low Traffic (Mean: {df_low['Total_Vehicles'].mean():.1f} vehicles)")
    ax_vol.plot(time_sec, df_med['Total_Vehicles'], color=COLOR_MED, linewidth=3.0, label=f"Medium Traffic (Mean: {df_med['Total_Vehicles'].mean():.1f} vehicles)")
    ax_vol.plot(time_sec, df_heavy['Total_Vehicles'], color=COLOR_HEAVY, linewidth=3.0, label=f"Heavy Traffic (Mean: {df_heavy['Total_Vehicles'].mean():.1f} vehicles)")
    
    ax_vol.set_title("Traffic Volume Comparison (All Traffic)", fontsize=16, fontweight='bold', pad=12)
    ax_vol.set_xlabel("Time (seconds)", fontsize=15, fontweight='bold')
    ax_vol.set_ylabel("Total Active Vehicles", fontsize=15, fontweight='bold')
    ax_vol.set_xlim(1, 60)
    ax_vol.set_ylim(0, 400)
    ax_vol.grid(True, linestyle='--', alpha=0.5, color='#BDC3C7')
    ax_vol.legend(loc='center right', framealpha=0.95, edgecolor='#BDC3C7')
    
    # ----------------------------------------------------
    # PANEL 2: Average Traffic Speed (km/h)
    # ----------------------------------------------------
    ax_speed.plot(time_sec, df_low['Avg_Background_Speed(km/h)'], color=COLOR_LOW, linewidth=3.0, label=f"Low Traffic (Mean: {df_low['Avg_Background_Speed(km/h)'].mean():.2f} km/h)")
    ax_speed.plot(time_sec, df_med['Avg_Background_Speed(km/h)'], color=COLOR_MED, linewidth=3.0, label=f"Medium Traffic (Mean: {df_med['Avg_Background_Speed(km/h)'].mean():.2f} km/h)")
    ax_speed.plot(time_sec, df_heavy['Avg_Background_Speed(km/h)'], color=COLOR_HEAVY, linewidth=3.0, label=f"Heavy Traffic (Mean: {df_heavy['Avg_Background_Speed(km/h)'].mean():.2f} km/h)")
    
    ax_speed.set_title("Average Background Speed Comparison", fontsize=16, fontweight='bold', pad=12)
    ax_speed.set_xlabel("Time (seconds)", fontsize=15, fontweight='bold')
    ax_speed.set_ylabel("Speed (km/h)", fontsize=15, fontweight='bold')
    ax_speed.set_xlim(1, 60)
    ax_speed.set_ylim(35, 55)
    ax_speed.grid(True, linestyle='--', alpha=0.5, color='#BDC3C7')
    ax_speed.legend(loc='lower left', framealpha=0.95, edgecolor='#BDC3C7')
    
    # Add visual annotation showing inverse relation
    ax_speed.annotate('Higher Density → Lower Average Speed', 
                      xy=(45, 42.1), xytext=(20, 37.5),
                      arrowprops=dict(facecolor='black', shrink=0.08, width=1.5, headwidth=6),
                      fontweight='bold', fontsize=12, bbox=dict(boxstyle='round,pad=0.5', fc='#ECF0F1', alpha=0.9, ec='#BDC3C7'))

    plt.suptitle("SUMO Traffic Profile Analysis: 1-Minute Window Comparison\nTraffic Volume vs. Speed under Dynamic Congestion Regimes", 
                 fontsize=18, fontweight='bold', y=0.97)
    
    plt.tight_layout(rect=[0, 0.02, 1, 0.93])
    
    # Save the figure
    plt.savefig(PLOT_PATH, bbox_inches='tight')
    plt.close()
    print(f"[SUCCESS] Saved traffic comparison plot successfully to: {PLOT_PATH}")

if __name__ == '__main__':
    generate_density_speed_plot()
