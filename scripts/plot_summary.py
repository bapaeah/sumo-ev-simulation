#!/usr/bin/env python3
import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# Directories
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_DIR = os.path.join(BASE_DIR, 'output')
INDIVIDUAL_DIR = os.path.join(OUTPUT_DIR, 'ev_plots')
PLOT_PATH = os.path.join(OUTPUT_DIR, 'ev_simulation_summary.png')

# EV Specifications
EV_COLORS = {
    'ev_01': '#FF6B6B',    # Red
    'ev_02': '#4ECDC4',    # Teal
    'ev_03': '#45B7D1',    # Blue
    'ev_04': '#FFA07A',    # Light Salmon
    'ev_05': '#98D8C8'     # Mint
}

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

def generate_plots():
    print("[INFO] Loading output data files...")
    soc_file = os.path.join(OUTPUT_DIR, 'ev_state_of_charge.csv')
    vel_file = os.path.join(OUTPUT_DIR, 'ev_velocity.csv')
    energy_file = os.path.join(OUTPUT_DIR, 'ev_energy_consumption.csv')
    
    if not (os.path.exists(soc_file) and os.path.exists(vel_file) and os.path.exists(energy_file)):
        print("[ERROR] Output CSV files missing. Please run the simulation first.")
        return
        
    df_soc = load_and_clean_csv(soc_file)
    df_vel = load_and_clean_csv(vel_file)
    df_energy_raw = load_and_clean_csv(energy_file)
    
    # Pivot energy consumption
    df_energy = df_energy_raw.pivot(index='Timestamp(s)', columns='VehicleID', values='Energy_Consumed(kWh)')
    df_energy = df_energy.reset_index()
    
    # Convert Timestamp(s) to Minutes for better readability
    time_min_soc = df_soc['Timestamp(s)'] / 60.0
    time_min_vel = df_vel['Timestamp(s)'] / 60.0
    time_min_energy = df_energy['Timestamp(s)'] / 60.0
    
    # Create the individual output directory
    os.makedirs(INDIVIDUAL_DIR, exist_ok=True)
    
    # ----------------------------------------------------
    # GENERATE 5 INDIVIDUAL PLOTS (ONE FOR EACH EV)
    # ----------------------------------------------------
    for ev_id, color in EV_COLORS.items():
        print(f"[INFO] Generating individual plot for {ev_id}...")
        fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(12, 10), sharex=True, dpi=120)
        
        # Plot SOC for this EV
        ax1.set_title(f'State of Charge (SOC) - {EV_NAMES[ev_id]}', fontsize=12, fontweight='bold')
        if ev_id in df_soc.columns:
            ax1.plot(time_min_soc, df_soc[ev_id], color=color, linewidth=3)
        ax1.set_ylabel('SOC (%)', fontsize=10, fontweight='bold')
        ax1.set_ylim(50, 100)
        ax1.grid(True, linestyle='--', alpha=0.5)
        
        # Plot Velocity for this EV
        ax2.set_title(f'Velocity ($km/h$) - {EV_NAMES[ev_id]}', fontsize=12, fontweight='bold')
        if ev_id in df_vel.columns:
            ax2.plot(time_min_vel, df_vel[ev_id], color=color, linewidth=2.5)
        ax2.set_ylabel('Speed (km/h)', fontsize=10, fontweight='bold')
        ax2.set_ylim(-5, 75)
        ax2.grid(True, linestyle='--', alpha=0.5)
        
        # Plot Energy Consumption for this EV
        ax3.set_title(f'Cumulative Energy Consumption ($kWh$) - {EV_NAMES[ev_id]}', fontsize=12, fontweight='bold')
        if ev_id in df_energy.columns:
            ax3.plot(time_min_energy, df_energy[ev_id], color=color, linewidth=3)
        ax3.set_ylabel('Energy Consumed (kWh)', fontsize=10, fontweight='bold')
        ax3.set_xlabel('Time (minutes)', fontsize=11, fontweight='bold')
        ax3.grid(True, linestyle='--', alpha=0.5)
        
        # Global visual enhancements for individual plot
        plt.xlim(0, max(time_min_soc))
        plt.suptitle(f'EV Performance Report: {EV_NAMES[ev_id]}', fontsize=15, fontweight='bold', y=0.96)
        plt.tight_layout(rect=[0, 0.02, 1, 0.94])
        
        individual_plot_path = os.path.join(INDIVIDUAL_DIR, f'{ev_id}_summary.png')
        plt.savefig(individual_plot_path, bbox_inches='tight')
        plt.close()
        print(f"  [SUCCESS] Saved individual summary to: {individual_plot_path}")
        
    # ----------------------------------------------------
    # GENERATE GLOBAL COMBINED PLOT
    # ----------------------------------------------------
    print("[INFO] Generating global combined summary plot...")
    fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(15, 12), sharex=True, dpi=150)
    
    # Plot SOC
    ax1.set_title('EV State of Charge (SOC) Over Full Journey Cycle', fontsize=12, fontweight='bold')
    for ev_id, color in EV_COLORS.items():
        if ev_id in df_soc.columns:
            ax1.plot(time_min_soc, df_soc[ev_id], label=f"{ev_id} SOC", color=color, linewidth=2.5)
    ax1.set_ylabel('State of Charge (%)', fontsize=10, fontweight='bold')
    ax1.set_ylim(50, 100)
    ax1.grid(True, linestyle='--', alpha=0.5)
    ax1.legend(loc='lower left', ncol=5, frameon=True, facecolor='white', framealpha=0.9)
    
    # Plot Velocity
    ax2.set_title('EV Real-time Velocity ($km/h$)', fontsize=12, fontweight='bold')
    for ev_id, color in EV_COLORS.items():
        if ev_id in df_vel.columns:
            ax2.plot(time_min_vel, df_vel[ev_id], label=f"{ev_id} Speed", color=color, linewidth=2)
    ax2.set_ylabel('Speed (km/h)', fontsize=10, fontweight='bold')
    ax2.set_ylim(-5, 75)
    ax2.grid(True, linestyle='--', alpha=0.5)
    ax2.legend(loc='upper right', ncol=5, frameon=True, facecolor='white', framealpha=0.9)
    
    # Plot Energy Consumption
    ax3.set_title('EV Cumulative Energy Consumption ($kWh$)', fontsize=12, fontweight='bold')
    for ev_id, color in EV_COLORS.items():
        if ev_id in df_energy.columns:
            ax3.plot(time_min_energy, df_energy[ev_id], label=f"{ev_id} Energy", color=color, linewidth=2.5)
    ax3.set_ylabel('Energy Consumed (kWh)', fontsize=10, fontweight='bold')
    ax3.set_xlabel('Time (minutes)', fontsize=11, fontweight='bold')
    ax3.grid(True, linestyle='--', alpha=0.5)
    ax3.legend(loc='upper left', ncol=5, frameon=True, facecolor='white', framealpha=0.9)
    
    # Global visual enhancements
    plt.xlim(0, max(time_min_soc))
    plt.suptitle('SUMO EV Simulation Summary Report - Bengaluru Round Trip Cycle', fontsize=16, fontweight='bold', y=0.96)
    plt.tight_layout(rect=[0, 0.02, 1, 0.94])
    
    plt.savefig(PLOT_PATH, bbox_inches='tight')
    plt.close()
    print(f"[SUCCESS] Global summary plot saved successfully to: {PLOT_PATH}")

if __name__ == '__main__':
    generate_plots()
