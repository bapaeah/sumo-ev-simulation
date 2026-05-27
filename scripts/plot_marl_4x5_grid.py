#!/usr/bin/env python3
"""
Generates a highly compact 2x5 grid comparison plot.
Rows:
  1. Velocity Profile (km/h) - Retained to normal scale [-2, 75]
  2. Cumulative Energy Consumption (kWh)
Columns:
  a, b, c, d, e (Column headers set as requested)
Optimized with independent y-axes, increased font sizes (tick/label), tight bounds, and a compact layout.
"""

import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# Directories
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_DIR = os.path.join(BASE_DIR, 'output')
PLOT_PATH = os.path.join(OUTPUT_DIR, 'marl_4x5_grid_comparison.png')  # Keep same name to avoid stale files

# Color palette
COLOR_DEFAULT = '#E74C3C'  # Aggressive Red (Actual)
COLOR_MARL = '#27AE60'     # Eco-Driving Emerald Green (Optimised)

EV_SPECS = {
    'ev_01': 'a',
    'ev_02': 'b',
    'ev_03': 'c',
    'ev_04': 'd',
    'ev_05': 'e'
}

def load_and_clean_csv(file_path):
    df = pd.read_csv(file_path)
    df = df.replace('N/A', np.nan)
    for col in df.columns:
        if col not in ['Time(Time)', 'Time(HH:MM:SS)', 'VehicleID']:
            df[col] = pd.to_numeric(df[col], errors='coerce')
    return df

def generate_grid_plot():
    print("[INFO] Loading comparative data files for compact 2x5 grid plot...")
    
    # Paths for default run
    def_soc_file = os.path.join(OUTPUT_DIR, 'default_ev_state_of_charge.csv')
    def_vel_file = os.path.join(OUTPUT_DIR, 'default_ev_velocity.csv')
    def_energy_file = os.path.join(OUTPUT_DIR, 'default_ev_energy_consumption.csv')
    
    # Paths for MARL run
    marl_soc_file = os.path.join(OUTPUT_DIR, 'marl_ev_state_of_charge.csv')
    marl_vel_file = os.path.join(OUTPUT_DIR, 'marl_ev_velocity.csv')
    marl_energy_file = os.path.join(OUTPUT_DIR, 'marl_ev_energy_consumption.csv')
    
    # Verify all files exist
    files = [def_soc_file, def_vel_file, def_energy_file, marl_soc_file, marl_vel_file, marl_energy_file]
    if not all(os.path.exists(f) for f in files):
        print("[ERROR] Comparative CSV files missing. Please run run_marl_simulation.py first.")
        return
        
    # Load and clean data
    df_def_soc = load_and_clean_csv(def_soc_file)
    df_def_vel = load_and_clean_csv(def_vel_file)
    df_def_energy_raw = load_and_clean_csv(def_energy_file)
    df_def_energy = df_def_energy_raw.pivot(index='Timestamp(s)', columns='VehicleID', values='Energy_Consumed(kWh)').reset_index()
    
    # MARL Load
    df_marl_soc = load_and_clean_csv(marl_soc_file)
    df_marl_vel = load_and_clean_csv(marl_vel_file)
    df_marl_energy_raw = load_and_clean_csv(marl_energy_file)
    df_marl_energy = df_marl_energy_raw.pivot(index='Timestamp(s)', columns='VehicleID', values='Energy_Consumed(kWh)').reset_index()
    
    # Create 2x5 subplot grid with independent y-axes (Rows: 0=Velocity, 1=Energy)
    fig, axes = plt.subplots(2, 5, figsize=(26, 9.5), sharex='col', sharey=False, dpi=150)
    
    # Global Matplotlib parameters tuning for large, readable fonts
    plt.rcParams.update({
        'font.size': 16,
        'axes.labelsize': 18,
        'xtick.labelsize': 16,
        'ytick.labelsize': 16,
        'legend.fontsize': 16
    })
    
    for col_idx, (ev_id, ev_name) in enumerate(EV_SPECS.items()):
        # ----------------------------------------------------
        # Extract & Clean Data for this specific EV
        # ----------------------------------------------------
        # DEFAULT Run (Actual)
        t_def_vel = df_def_vel['Timestamp(s)'] / 60.0
        vel_def = df_def_vel[ev_id].dropna()
        t_def_vel = t_def_vel.loc[vel_def.index]
        
        t_def_energy = df_def_energy['Timestamp(s)'] / 60.0
        energy_def = df_def_energy[ev_id].dropna() if ev_id in df_def_energy.columns else pd.Series(dtype=float)
        t_def_energy = t_def_energy.loc[energy_def.index]
        
        # MARL Run (Optimised)
        t_marl_vel = df_marl_vel['Timestamp(s)'] / 60.0
        vel_marl = df_marl_vel[ev_id].dropna()
        t_marl_vel = t_marl_vel.loc[vel_marl.index]
        
        t_marl_energy = df_marl_energy['Timestamp(s)'] / 60.0
        energy_marl = df_marl_energy[ev_id].dropna() if ev_id in df_marl_energy.columns else pd.Series(dtype=float)
        t_marl_energy = t_marl_energy.loc[energy_marl.index]
        
        # ----------------------------------------------------
        # ROW 1: Velocity (km/h) - Now the top row!
        # ----------------------------------------------------
        ax_vel = axes[0, col_idx]
        ax_vel.plot(t_def_vel, vel_def, color=COLOR_DEFAULT, linewidth=2.0, alpha=0.85, label="Actual")
        ax_vel.plot(t_marl_vel, vel_marl, color=COLOR_MARL, linewidth=2.0, alpha=0.85, label="Optimised")
        ax_vel.grid(True, linestyle='--', alpha=0.5)
        ax_vel.tick_params(axis='both', which='major', labelsize=16)
        
        # Set titles as headers a, b, c, d, e on the top row of subplots
        ax_vel.set_title(f"{ev_name}", fontsize=20, fontweight='bold', pad=10)
        
        # Retained to the normal standard scale [-2, 75]
        ax_vel.set_ylim(-2, 75)
        
        if col_idx == 0:
            ax_vel.set_ylabel("Speed (km/h)", fontsize=18, fontweight='bold')
            ax_vel.legend(loc='upper right', fontsize=16, framealpha=0.9, edgecolor='black')
            
        # ----------------------------------------------------
        # ROW 2: Cumulative Energy Consumption (kWh) - Now the bottom row!
        # ----------------------------------------------------
        ax_energy = axes[1, col_idx]
        if not energy_def.empty:
            ax_energy.plot(t_def_energy, energy_def, color=COLOR_DEFAULT, linewidth=2.8)
        if not energy_marl.empty:
            ax_energy.plot(t_marl_energy, energy_marl, color=COLOR_MARL, linewidth=2.8)
        ax_energy.grid(True, linestyle='--', alpha=0.5)
        ax_energy.set_xlabel("Time (minutes)", fontsize=18, fontweight='bold')
        ax_energy.tick_params(axis='both', which='major', labelsize=16)
        
        # Extremely tight dynamic energy consumption limits to eliminate whitespace
        if not energy_def.empty and not energy_marl.empty:
            max_energy = max(energy_def.max(), energy_marl.max()) + 0.04
            ax_energy.set_ylim(-0.04, max_energy)
        
        if col_idx == 0:
            ax_energy.set_ylabel("Energy Consumed (kWh)", fontsize=18, fontweight='bold')
            
    # Compact layout optimization to reduce gaps between subplots
    plt.tight_layout(pad=1.2, h_pad=0.8, w_pad=0.8)
    
    # Save the figure
    plt.savefig(PLOT_PATH, bbox_inches='tight')
    plt.close()
    print(f"[SUCCESS] Compact 2x5 Grid Comparison Plot saved successfully to: {PLOT_PATH}")

if __name__ == '__main__':
    generate_grid_plot()
