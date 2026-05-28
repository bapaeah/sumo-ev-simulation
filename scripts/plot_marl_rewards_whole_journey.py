#!/usr/bin/env python3
"""
Generates a highly-detailed 1x5 grid plot for the RL reward functions over the WHOLE journey.
Columns:
  a, b, c, d, e (corresponding to ev_01, ev_02, ev_03, ev_04, ev_05)
X-axis: Whole Journey (0 to 35 minutes)
In each subplot: Plots the raw optimised step reward (faint green) and a 30-second rolling average (solid green).
Shades the background to denote the Low, Medium, and Heavy traffic congestion phases in the network.
"""

import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# Directories
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_DIR = os.path.join(BASE_DIR, 'output')
PLOT_PATH = os.path.join(OUTPUT_DIR, 'marl_rewards_whole_journey.png')

# EV IDs and column mappings
EV_MAPPINGS = {
    'ev_01': 'a',
    'ev_02': 'b',
    'ev_03': 'c',
    'ev_04': 'd',
    'ev_05': 'e'
}
EV_IDS = list(EV_MAPPINGS.keys())

# Shading colors for traffic phases
COLOR_LOW_BG = '#2ECC71'    # Faint Green for Low Traffic Phase
COLOR_MED_BG = '#F39C12'    # Faint Orange for Medium Traffic Phase
COLOR_HEAVY_BG = '#E74C3C'  # Faint Red for Heavy Traffic Phase

COLOR_MARL_RAW = '#A3E4D7'   # Light transparent mint for raw rewards
COLOR_MARL_ROLL = '#16A085'  # Deep solid teal for rolling average

def load_and_clean_csv(file_path):
    df = pd.read_csv(file_path)
    df = df.replace('N/A', np.nan)
    for col in df.columns:
        if col not in ['Time(Time)', 'Time(HH:MM:SS)', 'VehicleID']:
            df[col] = pd.to_numeric(df[col], errors='coerce')
    return df

def calculate_rewards(df_vel, df_energy, df_traffic, ev_id):
    """
    Computes the second-by-second reward function for a specific EV.
    """
    df = pd.merge(df_vel[['Timestamp(s)', ev_id]], df_traffic[['Timestamp(s)', 'Avg_Background_Speed(km/h)']], on='Timestamp(s)')
    if ev_id in df_energy.columns:
        df = pd.merge(df, df_energy[['Timestamp(s)', ev_id]], on='Timestamp(s)', suffixes=('_vel', '_energy'))
    else:
        df[f'{ev_id}_energy'] = 0.0
        df.rename(columns={ev_id: f'{ev_id}_vel'}, inplace=True)
        
    df.sort_values(by='Timestamp(s)', inplace=True)
    df.reset_index(drop=True, inplace=True)
    
    rewards = []
    prev_energy = 0.0
    
    for idx, row in df.iterrows():
        curr_energy = row[f'{ev_id}_energy']
        if idx == 0:
            delta_energy = 0.0
        else:
            delta_energy = max(0.0, curr_energy - prev_energy)
        prev_energy = curr_energy
        
        energy_penalty = -100.0 * delta_energy
        
        speed_limit_mps = 15.0  # 54 km/h (15 m/s)
        speed_mps = row[f'{ev_id}_vel'] / 3.6
        
        speed_ratio = speed_mps / speed_limit_mps
        speed_reward = 1.0 - abs(speed_ratio - 1.0)
        
        bg_speed_mps = row['Avg_Background_Speed(km/h)'] / 3.6
        standstill_penalty = 0.0
        if speed_mps < 0.5 and bg_speed_mps > 5.0:
            standstill_penalty = -2.0
            
        step_reward = energy_penalty + 0.5 * speed_reward + standstill_penalty
        rewards.append(step_reward)
        
    df['Reward'] = rewards
    return df

def generate_rewards_whole_journey():
    print("[INFO] Loading files for optimised whole journey reward plots...")
    
    # File paths
    marl_soc_file = os.path.join(OUTPUT_DIR, 'marl_ev_state_of_charge.csv')
    marl_vel_file = os.path.join(OUTPUT_DIR, 'marl_ev_velocity.csv')
    marl_energy_file = os.path.join(OUTPUT_DIR, 'marl_ev_energy_consumption.csv')
    
    traffic_file = os.path.join(OUTPUT_DIR, 'traffic_info.csv')
    
    files = [marl_soc_file, marl_vel_file, marl_energy_file, traffic_file]
    if not all(os.path.exists(f) for f in files):
        print("[ERROR] CSV files missing. Please run simulation first.")
        return
        
    # Load and clean data
    df_marl_vel = load_and_clean_csv(marl_vel_file)
    df_marl_energy_raw = load_and_clean_csv(marl_energy_file)
    df_marl_energy = df_marl_energy_raw.pivot(index='Timestamp(s)', columns='VehicleID', values='Energy_Consumed(kWh)').reset_index()
    
    df_traffic = load_and_clean_csv(traffic_file)
    
    # Calculate step rewards
    marl_rewards = {}
    for ev_id in EV_IDS:
        marl_rewards[ev_id] = calculate_rewards(df_marl_vel, df_marl_energy, df_traffic, ev_id)
        
    # Create 1x5 subplot grid
    fig, axes = plt.subplots(1, 5, figsize=(25, 6), sharey=True, dpi=150)
    
    # Enable premium styling
    plt.rcParams.update({
        'font.size': 14,
        'axes.labelsize': 18,
        'xtick.labelsize': 16,
        'ytick.labelsize': 16,
        'legend.fontsize': 11
    })
    
    for col_idx, ev_id in enumerate(EV_IDS):
        ax = axes[col_idx]
        df_ev = marl_rewards[ev_id].dropna(subset=[f'{ev_id}_vel'])
        
        time_min = df_ev['Timestamp(s)'] / 60.0
        raw_rewards = df_ev['Reward']
        
        # Calculate 30-second rolling average (window=30)
        rolling_rewards = raw_rewards.rolling(window=30, min_periods=1).mean()
        
        # Plot raw rewards in faint transparent green
        ax.plot(time_min, raw_rewards, color=COLOR_MARL_RAW, alpha=0.55, linewidth=1.0, label='Raw Step Reward')
        
        # Plot rolling average in solid teal
        ax.plot(time_min, rolling_rewards, color=COLOR_MARL_ROLL, linewidth=2.5, label='30s Rolling Avg')
        
        # Shades for traffic phases based on actual simulated background counts:
        # Phase 1: Low Traffic (0 to 4.2 minutes)
        ax.axvspan(0.0, 4.2, color=COLOR_LOW_BG, alpha=0.08, label='Low Traffic')
        # Phase 2: Medium Traffic (4.2 to 15.8 minutes)
        ax.axvspan(4.2, 15.8, color=COLOR_MED_BG, alpha=0.08, label='Medium Traffic')
        # Phase 3: Heavy Traffic (15.8 to 30.0 minutes)
        ax.axvspan(15.8, 30.0, color=COLOR_HEAVY_BG, alpha=0.08, label='Heavy Traffic')
        
        ax.grid(True, linestyle='--', alpha=0.5)
        ax.tick_params(axis='both', which='major', labelsize=16)
        
        # Column headers sequential a to e
        ax.set_title(f"{EV_MAPPINGS[ev_id]}", fontsize=22, fontweight='bold', pad=10)
        
        # Y-axis label on the first column of subplots
        if col_idx == 0:
            ax.set_ylabel("Optimised Step Reward", fontsize=18, fontweight='bold')
            
        # X-axis label on all subplots
        ax.set_xlabel("Time (minutes)", fontsize=18, fontweight='bold')
            
        # Add legend only to the first subplot to keep layout completely clean
        if col_idx == 0:
            ax.legend(loc='lower left', framealpha=0.9, fontsize=11)
            
        # Fix standard vertical reward range to encapsulate all curves perfectly
        ax.set_ylim(-4.5, 1.5)
        ax.set_xlim(0, 35)
        
    # Compact layout optimization
    plt.tight_layout(pad=1.2, w_pad=0.8)
    
    # Save the figure
    plt.savefig(PLOT_PATH, bbox_inches='tight')
    plt.close()
    print(f"[SUCCESS] Saved optimised whole journey reward comparison plot to: {PLOT_PATH}")

if __name__ == '__main__':
    generate_rewards_whole_journey()
