#!/usr/bin/env python3
"""
Generates individual 3-panel comparison plots for each EV, comparing 
Without MARL (SUMO Default) vs With MARL (Eco-Driving) in the same subplots.
"""

import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# Directories
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_DIR = os.path.join(BASE_DIR, 'output')

# Aesthetics - Custom color palette
COLOR_DEFAULT = '#E74C3C'  # Aggressive Red
COLOR_MARL = '#27AE60'     # Eco-Driving Emerald Green

EV_NAMES = {
    'ev_01': 'EV 01 (Small - 40 kWh)',
    'ev_02': 'EV 02 (Medium - 60 kWh)',
    'ev_03': 'EV 03 (Large - 75 kWh)',
    'ev_04': 'EV 04 (Medium - 50 kWh)',
    'ev_05': 'EV 05 (Medium - 55 kWh)'
}

def load_and_clean_csv(file_path):
    df = pd.read_csv(file_path)
    # Replace N/A with NaN
    df = df.replace('N/A', np.nan)
    # Convert numerical columns to float
    for col in df.columns:
        if col not in ['Time(Time)', 'Time(HH:MM:SS)', 'VehicleID']:
            df[col] = pd.to_numeric(df[col], errors='coerce')
    return df

def generate_individual_comparison_plots():
    print("[INFO] Loading comparative data files...")
    
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
    
    df_marl_soc = load_and_clean_csv(marl_soc_file)
    df_marl_vel = load_and_clean_csv(marl_vel_file)
    df_marl_energy_raw = load_and_clean_csv(marl_energy_file)
    df_marl_energy = df_marl_energy_raw.pivot(index='Timestamp(s)', columns='VehicleID', values='Energy_Consumed(kWh)').reset_index()
    
    # Process each EV individually
    for ev_id, ev_title in EV_NAMES.items():
        print(f"[INFO] Generating comparison plot for {ev_id}...")
        
        # Filter and clean time vectors for DEFAULT
        t_def_soc = df_def_soc['Timestamp(s)'] / 60.0
        soc_def = df_def_soc[ev_id].dropna()
        t_def_soc = t_def_soc.loc[soc_def.index]
        
        t_def_vel = df_def_vel['Timestamp(s)'] / 60.0
        vel_def = df_def_vel[ev_id].dropna()
        t_def_vel = t_def_vel.loc[vel_def.index]
        
        t_def_energy = df_def_energy['Timestamp(s)'] / 60.0
        energy_def = df_def_energy[ev_id].dropna() if ev_id in df_def_energy.columns else pd.Series(dtype=float)
        t_def_energy = t_def_energy.loc[energy_def.index]
        
        # Filter and clean time vectors for MARL
        t_marl_soc = df_marl_soc['Timestamp(s)'] / 60.0
        soc_marl = df_marl_soc[ev_id].dropna()
        t_marl_soc = t_marl_soc.loc[soc_marl.index]
        
        t_marl_vel = df_marl_vel['Timestamp(s)'] / 60.0
        vel_marl = df_marl_vel[ev_id].dropna()
        t_marl_vel = t_marl_vel.loc[vel_marl.index]
        
        t_marl_energy = df_marl_energy['Timestamp(s)'] / 60.0
        energy_marl = df_marl_energy[ev_id].dropna() if ev_id in df_marl_energy.columns else pd.Series(dtype=float)
        t_marl_energy = t_marl_energy.loc[energy_marl.index]
        
        # Create 3-panel subplot (3 rows, 1 col)
        fig, (ax_soc, ax_vel, ax_energy) = plt.subplots(3, 1, figsize=(12, 14), sharex=True, dpi=150)
        
        # --- PANEL 1: State of Charge (SOC) ---
        ax_soc.plot(t_def_soc, soc_def, label="Actual", color=COLOR_DEFAULT, linewidth=2.5)
        ax_soc.plot(t_marl_soc, soc_marl, label="Optimised", color=COLOR_MARL, linewidth=2.5)
        ax_soc.set_title("State of Charge (SOC) Comparison", fontsize=12, fontweight='bold', pad=8)
        ax_soc.set_ylabel("Battery SOC (%)", fontsize=11, fontweight='bold')
        ax_soc.grid(True, linestyle='--', alpha=0.5)
        ax_soc.legend(loc='lower left', frameon=True, facecolor='white', framealpha=0.9)
        
        # Format y-axis to focus closely on the active SOC range to remove white space
        min_soc = min(soc_def.min(), soc_marl.min()) - 1
        max_soc = max(soc_def.max(), soc_marl.max()) + 1
        ax_soc.set_ylim(min_soc, max_soc)
        
        # --- PANEL 2: Speed Profile ---
        ax_vel.plot(t_def_vel, vel_def, label="Actual", color=COLOR_DEFAULT, linewidth=1.8, alpha=0.9)
        ax_vel.plot(t_marl_vel, vel_marl, label="Optimised", color=COLOR_MARL, linewidth=1.8, alpha=0.9)
        ax_vel.set_title("Vehicle Velocity Profile Comparison", fontsize=12, fontweight='bold', pad=8)
        ax_vel.set_ylabel("Speed (km/h)", fontsize=11, fontweight='bold')
        ax_vel.grid(True, linestyle='--', alpha=0.5)
        ax_vel.legend(loc='upper right', frameon=True, facecolor='white', framealpha=0.9)
        ax_vel.set_ylim(-2, 75)
        
        # --- PANEL 3: Cumulative Energy Consumption ---
        if not energy_def.empty:
            ax_energy.plot(t_def_energy, energy_def, label="Actual", color=COLOR_DEFAULT, linewidth=2.5)
        if not energy_marl.empty:
            ax_energy.plot(t_marl_energy, energy_marl, label="Optimised", color=COLOR_MARL, linewidth=2.5)
        ax_energy.set_title("Cumulative Energy Consumption", fontsize=12, fontweight='bold', pad=8)
        ax_energy.set_ylabel("Energy Consumed (kWh)", fontsize=11, fontweight='bold')
        ax_energy.set_xlabel("Time (minutes)", fontsize=11, fontweight='bold')
        ax_energy.grid(True, linestyle='--', alpha=0.5)
        ax_energy.legend(loc='upper left', frameon=True, facecolor='white', framealpha=0.9)
        
        # Title of the overall figure
        fig.suptitle(f"{ev_title} Performance Comparison\nWithout MARL (SUMO Default) vs. With MARL (Eco-Driving) over 23.8 km Round-Trip", 
                     fontsize=15, fontweight='bold', y=0.96)
        
        plt.tight_layout(rect=[0, 0.02, 1, 0.93])
        
        # Save plot
        plot_filename = f'{ev_id}_marl_comparison.png'
        plot_path = os.path.join(OUTPUT_DIR, plot_filename)
        plt.savefig(plot_path, bbox_inches='tight')
        plt.close()
        print(f"[SUCCESS] Saved individual comparison plot to: {plot_path}")

if __name__ == '__main__':
    generate_individual_comparison_plots()
