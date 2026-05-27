#!/usr/bin/env python3
import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# Directories
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_DIR = os.path.join(BASE_DIR, 'output')
PLOT_PATH = os.path.join(OUTPUT_DIR, 'marl_comparison.png')

# EV Specifications
EV_COLORS = {
    'ev_01': '#FF6B6B',    # Red
    'ev_02': '#4ECDC4',    # Teal
    'ev_03': '#45B7D1',    # Blue
    'ev_04': '#FFA07A',    # Light Salmon
    'ev_05': '#98D8C8'     # Mint
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

def generate_comparison_plots():
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
    
    # Convert Timestamp(s) to Minutes for X-axis
    time_min_def_soc = df_def_soc['Timestamp(s)'] / 60.0
    time_min_def_vel = df_def_vel['Timestamp(s)'] / 60.0
    time_min_def_energy = df_def_energy['Timestamp(s)'] / 60.0
    
    time_min_marl_soc = df_marl_soc['Timestamp(s)'] / 60.0
    time_min_marl_vel = df_marl_vel['Timestamp(s)'] / 60.0
    time_min_marl_energy = df_marl_energy['Timestamp(s)'] / 60.0
    
    # Create 6-panel plot: 3 rows, 2 columns
    fig, axes = plt.subplots(3, 2, figsize=(20, 15), sharex='col', sharey='row', dpi=150)
    ((ax_def_soc, ax_marl_soc), (ax_def_vel, ax_marl_vel), (ax_def_energy, ax_marl_energy)) = axes
    
    # --- ROW 1: State of Charge (SOC) ---
    # Left Column: Default
    ax_def_soc.set_title('WITHOUT MARL (Standard Aggressive) - State of Charge (%)', fontsize=12, fontweight='bold', pad=10)
    for ev_id, color in EV_COLORS.items():
        if ev_id in df_def_soc.columns:
            ax_def_soc.plot(time_min_def_soc, df_def_soc[ev_id], label=f"{ev_id}", color=color, linewidth=2.5)
    ax_def_soc.set_ylabel('State of Charge (%)', fontsize=11, fontweight='bold')
    ax_def_soc.set_ylim(40, 100)
    ax_def_soc.grid(True, linestyle='--', alpha=0.5)
    ax_def_soc.legend(loc='lower left', ncol=5)
    
    # Right Column: MARL
    ax_marl_soc.set_title('WITH MARL (Coordinated Eco-Driving) - State of Charge (%)', fontsize=12, fontweight='bold', pad=10)
    for ev_id, color in EV_COLORS.items():
        if ev_id in df_marl_soc.columns:
            ax_marl_soc.plot(time_min_marl_soc, df_marl_soc[ev_id], label=f"{ev_id}", color=color, linewidth=2.5)
    ax_marl_soc.set_ylim(40, 100)
    ax_marl_soc.grid(True, linestyle='--', alpha=0.5)
    ax_marl_soc.legend(loc='lower left', ncol=5)
    
    # --- ROW 2: Velocity ---
    # Left Column: Default
    ax_def_vel.set_title('WITHOUT MARL - Speed Profile ($km/h$)', fontsize=12, fontweight='bold', pad=10)
    for ev_id, color in EV_COLORS.items():
        if ev_id in df_def_vel.columns:
            ax_def_vel.plot(time_min_def_vel, df_def_vel[ev_id], label=f"{ev_id}", color=color, linewidth=2)
    ax_def_vel.set_ylabel('Speed (km/h)', fontsize=11, fontweight='bold')
    ax_def_vel.set_ylim(-5, 75)
    ax_def_vel.grid(True, linestyle='--', alpha=0.5)
    
    # Right Column: MARL
    ax_marl_vel.set_title('WITH MARL - Coordinated Speed Profile ($km/h$)', fontsize=12, fontweight='bold', pad=10)
    for ev_id, color in EV_COLORS.items():
        if ev_id in df_marl_vel.columns:
            ax_marl_vel.plot(time_min_marl_vel, df_marl_vel[ev_id], label=f"{ev_id}", color=color, linewidth=2)
    ax_marl_vel.set_ylim(-5, 75)
    ax_marl_vel.grid(True, linestyle='--', alpha=0.5)
    
    # --- ROW 3: Cumulative Energy Consumption ---
    # Left Column: Default
    ax_def_energy.set_title('WITHOUT MARL - Cumulative Consumption ($kWh$)', fontsize=12, fontweight='bold', pad=10)
    for ev_id, color in EV_COLORS.items():
        if ev_id in df_def_energy.columns:
            ax_def_energy.plot(time_min_def_energy, df_def_energy[ev_id], label=f"{ev_id}", color=color, linewidth=2.5)
    ax_def_energy.set_ylabel('Energy Consumed (kWh)', fontsize=11, fontweight='bold')
    ax_def_energy.set_xlabel('Time (minutes)', fontsize=11, fontweight='bold')
    ax_def_energy.grid(True, linestyle='--', alpha=0.5)
    
    # Right Column: MARL
    ax_marl_energy.set_title('WITH MARL - Optimized Consumption ($kWh$)', fontsize=12, fontweight='bold', pad=10)
    for ev_id, color in EV_COLORS.items():
        if ev_id in df_marl_energy.columns:
            ax_marl_energy.plot(time_min_marl_energy, df_marl_energy[ev_id], label=f"{ev_id}", color=color, linewidth=2.5)
    ax_marl_energy.set_xlabel('Time (minutes)', fontsize=11, fontweight='bold')
    ax_marl_energy.grid(True, linestyle='--', alpha=0.5)
    
    # Global visual enhancements
    plt.suptitle('Multi-Agent Reinforcement Learning (MARL) Performance Comparison\nDynamic Eco-Driving vs Standard Aggressive Driving (Bengaluru 35m Round Trip Cycle)', 
                 fontsize=18, fontweight='bold', y=0.97)
    
    plt.tight_layout(rect=[0, 0.02, 1, 0.94])
    
    # Save the figure
    os.makedirs(os.path.dirname(PLOT_PATH), exist_ok=True)
    plt.savefig(PLOT_PATH, bbox_inches='tight')
    plt.close()
    print(f"[SUCCESS] Comparative plot saved successfully to: {PLOT_PATH}")

if __name__ == '__main__':
    generate_comparison_plots()
