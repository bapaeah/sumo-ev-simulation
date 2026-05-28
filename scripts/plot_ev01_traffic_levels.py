#!/usr/bin/env python3
"""
Generates dedicated comparative plots for EV1 (ev_01) under three different traffic levels.
For each traffic level (Low, Medium, Heavy), it creates a dedicated 4-panel stacked plot comparing:
  1. Surrounding Traffic Volume (All Traffic active vehicle count) - Context
  2. Velocity Profile (Speed in km/h) - Actual vs. Optimised
  3. State of Charge (SOC %) - Actual vs. Optimised
  4. Cumulative Energy Consumption (kWh) - Actual vs. Optimised
Over a 1-minute (60-second) window.
"""

import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# Directories
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_DIR = os.path.join(BASE_DIR, 'output')

# Output Plot Paths
PLOT_LOW_PATH = os.path.join(OUTPUT_DIR, 'ev01_low_traffic_comparison.png')
PLOT_MED_PATH = os.path.join(OUTPUT_DIR, 'ev01_medium_traffic_comparison.png')
PLOT_HEAVY_PATH = os.path.join(OUTPUT_DIR, 'ev01_heavy_traffic_comparison.png')

# Colors
COLOR_DEFAULT = '#E74C3C'  # Crimson Red (Actual)
COLOR_MARL = '#27AE60'     # Eco-Driving Emerald Green (Optimised)
COLOR_TRAFFIC = '#2C3E50'  # Dark Slate Blue for Surrounding Traffic

def load_and_clean_csv(file_path):
    df = pd.read_csv(file_path)
    df = df.replace('N/A', np.nan)
    for col in df.columns:
        if col not in ['Time(Time)', 'Time(HH:MM:SS)', 'VehicleID']:
            df[col] = pd.to_numeric(df[col], errors='coerce')
    return df

def extract_window_data(df, start_t, end_t, col_name):
    # Filter by Timestamp(s)
    sub = df[(df['Timestamp(s)'] >= start_t) & (df['Timestamp(s)'] <= end_t)].copy()
    sub = sub.sort_values(by='Timestamp(s)').reset_index(drop=True)
    # Ensure we get the specific column and timestamp
    return sub['Timestamp(s)'], sub[col_name] if col_name in sub.columns else pd.Series(dtype=float)

def plot_traffic_level_comparison(title, start_t, end_t, save_path, data_dict):
    """
    Generates a premium 4-panel stacked plot for a single traffic state.
    """
    time_sec = np.arange(1, 61)  # 1 to 60 seconds
    
    # Enable premium styling
    plt.rcParams.update({
        'font.size': 14,
        'axes.labelsize': 18,
        'xtick.labelsize': 16,
        'ytick.labelsize': 16,
        'legend.fontsize': 11
    })
    
    fig, (ax_traffic, ax_speed, ax_soc, ax_energy) = plt.subplots(4, 1, figsize=(10, 12), sharex=True, dpi=150)
    
    # 1. SURROUNDING TRAFFIC VOL (Context)
    ax_traffic.plot(time_sec, data_dict['traffic'][:60], color=COLOR_TRAFFIC, linewidth=2.5)
    ax_traffic.set_ylabel("Traffic Count", fontsize=18, fontweight='bold')
    ax_traffic.grid(True, linestyle='--', alpha=0.5)
    ax_traffic.tick_params(axis='both', which='major', labelsize=16)
    # Put tight bounds with some padding
    min_t = data_dict['traffic'].min()
    max_t = data_dict['traffic'].max()
    ax_traffic.set_ylim(max(0, min_t - 10), max_t + 10)
    
    # 2. SPEED SUBPLOT (Legend kept here!)
    ax_speed.plot(time_sec, data_dict['vel_def'][:60], color=COLOR_DEFAULT, linewidth=2.5, label='Actual (Default)')
    ax_speed.plot(time_sec, data_dict['vel_marl'][:60], color=COLOR_MARL, linewidth=2.5, label='Optimised (MARL)')
    ax_speed.set_ylabel("Speed (km/h)", fontsize=18, fontweight='bold')
    ax_speed.grid(True, linestyle='--', alpha=0.5)
    ax_speed.legend(loc='upper right', framealpha=0.9, fontsize=11)
    ax_speed.tick_params(axis='both', which='major', labelsize=16)
    ax_speed.set_ylim(-2, 75)
    
    # 3. STATE OF CHARGE (SOC) SUBPLOT
    ax_soc.plot(time_sec, data_dict['soc_def'][:60], color=COLOR_DEFAULT, linewidth=2.5)
    ax_soc.plot(time_sec, data_dict['soc_marl'][:60], color=COLOR_MARL, linewidth=2.5)
    ax_soc.set_ylabel("SoC (%)", fontsize=18, fontweight='bold')
    ax_soc.grid(True, linestyle='--', alpha=0.5)
    ax_soc.tick_params(axis='both', which='major', labelsize=16)
    
    # Zoom tightly to SOC range to eliminate whitespace
    min_soc = min(data_dict['soc_def'].min(), data_dict['soc_marl'].min())
    max_soc = max(data_dict['soc_def'].max(), data_dict['soc_marl'].max())
    ax_soc.set_ylim(min_soc - 0.05, max_soc + 0.05)
    
    # 4. ENERGY SUBPLOT
    ax_energy.plot(time_sec, data_dict['energy_def'][:60], color=COLOR_DEFAULT, linewidth=2.5)
    ax_energy.plot(time_sec, data_dict['energy_marl'][:60], color=COLOR_MARL, linewidth=2.5)
    ax_energy.set_ylabel("Energy Consumed (kWh)", fontsize=18, fontweight='bold')
    ax_energy.set_xlabel("Time (seconds)", fontsize=18, fontweight='bold')
    ax_energy.grid(True, linestyle='--', alpha=0.5)
    ax_energy.tick_params(axis='both', which='major', labelsize=16)
    
    # Zoom tightly to Energy consumption
    min_energy = min(data_dict['energy_def'].min(), data_dict['energy_marl'].min())
    max_energy = max(data_dict['energy_def'].max(), data_dict['energy_marl'].max())
    ax_energy.set_ylim(min_energy - 0.01, max_energy + 0.01)
    
    plt.tight_layout(pad=1.2)
    plt.savefig(save_path, bbox_inches='tight')
    plt.close()
    print(f"[SUCCESS] Saved comparative plot for {title} to: {save_path}")

def generate_comparisons():
    print("[INFO] Loading CSV data for EV1 comparison plots...")
    
    # File Paths
    def_soc_file = os.path.join(OUTPUT_DIR, 'default_ev_state_of_charge.csv')
    def_vel_file = os.path.join(OUTPUT_DIR, 'default_ev_velocity.csv')
    def_energy_file = os.path.join(OUTPUT_DIR, 'default_ev_energy_consumption.csv')
    
    marl_soc_file = os.path.join(OUTPUT_DIR, 'marl_ev_state_of_charge.csv')
    marl_vel_file = os.path.join(OUTPUT_DIR, 'marl_ev_velocity.csv')
    marl_energy_file = os.path.join(OUTPUT_DIR, 'marl_ev_energy_consumption.csv')
    
    traffic_file = os.path.join(OUTPUT_DIR, 'traffic_info.csv')
    
    files = [def_soc_file, def_vel_file, def_energy_file, marl_soc_file, marl_vel_file, marl_energy_file, traffic_file]
    if not all(os.path.exists(f) for f in files):
        print("[ERROR] CSV files missing. Please run run_marl_simulation.py first.")
        return

    # Load & Pivot Data
    df_def_soc = load_and_clean_csv(def_soc_file)
    df_def_vel = load_and_clean_csv(def_vel_file)
    df_def_energy_raw = load_and_clean_csv(def_energy_file)
    df_def_energy = df_def_energy_raw.pivot(index='Timestamp(s)', columns='VehicleID', values='Energy_Consumed(kWh)').reset_index()
    
    df_marl_soc = load_and_clean_csv(marl_soc_file)
    df_marl_vel = load_and_clean_csv(marl_vel_file)
    df_marl_energy_raw = load_and_clean_csv(marl_energy_file)
    df_marl_energy = df_marl_energy_raw.pivot(index='Timestamp(s)', columns='VehicleID', values='Energy_Consumed(kWh)').reset_index()
    
    df_traffic = load_and_clean_csv(traffic_file)
    
    # Define Windows
    windows = {
        'Low Traffic': (109, 168),
        'Medium Traffic': (655, 714),
        'Heavy Traffic': (1084, 1143)
    }
    
    paths = {
        'Low Traffic': PLOT_LOW_PATH,
        'Medium Traffic': PLOT_MED_PATH,
        'Heavy Traffic': PLOT_HEAVY_PATH
    }
    
    for level, (start_t, end_t) in windows.items():
        # Slicing EV1 and Traffic Data
        _, vel_def = extract_window_data(df_def_vel, start_t, end_t, 'ev_01')
        _, vel_marl = extract_window_data(df_marl_vel, start_t, end_t, 'ev_01')
        
        _, soc_def = extract_window_data(df_def_soc, start_t, end_t, 'ev_01')
        _, soc_marl = extract_window_data(df_marl_soc, start_t, end_t, 'ev_01')
        
        _, energy_def = extract_window_data(df_def_energy, start_t, end_t, 'ev_01')
        _, energy_marl = extract_window_data(df_marl_energy, start_t, end_t, 'ev_01')
        
        _, traffic = extract_window_data(df_traffic, start_t, end_t, 'Total_Vehicles')
        
        data_dict = {
            'vel_def': vel_def,
            'vel_marl': vel_marl,
            'soc_def': soc_def,
            'soc_marl': soc_marl,
            'energy_def': energy_def,
            'energy_marl': energy_marl,
            'traffic': traffic
        }
        
        plot_traffic_level_comparison(level, start_t, end_t, paths[level], data_dict)

if __name__ == '__main__':
    generate_comparisons()
