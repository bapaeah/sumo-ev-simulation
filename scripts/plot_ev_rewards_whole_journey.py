#!/usr/bin/env python3
"""
Generates a highly-detailed 1x5 grid plot comparing Actual (Default) vs. Optimised (MARL)
step rewards over the WHOLE journey (35 minutes / 2100 seconds) for all 5 EVs.
Columns:
  a, b, c, d, e (corresponding to ev_01, ev_02, ev_03, ev_04, ev_05)
X-axis: Whole Journey (0 to 35 minutes)
In each subplot:
  - Actual Raw Step Reward (faint red) & 30s Rolling Average (solid crimson red)
  - Optimised Raw Step Reward (faint green) & 30s Rolling Average (solid emerald green)
  - Shades the background to denote the Low, Medium, and Heavy traffic congestion phases.
"""

import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# Directories
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_DIR = os.path.join(BASE_DIR, 'output')
PLOT_PATH = os.path.join(OUTPUT_DIR, 'ev_rewards_whole_journey_comparison.png')

# EV IDs and column mappings
EV_MAPPINGS = {
    'ev_01': 'a',
    'ev_02': 'b',
    'ev_03': 'c',
    'ev_04': 'd',
    'ev_05': 'e'
}
EV_IDS = list(EV_MAPPINGS.keys())

# Colors for background shading (faint alpha applied in axvspan)
COLOR_LOW_BG = '#2ECC71'    # Faint Green for Low Traffic Phase
COLOR_MED_BG = '#F39C12'    # Faint Orange for Medium Traffic Phase
COLOR_HEAVY_BG = '#E74C3C'  # Faint Red for Heavy Traffic Phase

# Curve styling
COLOR_ACTUAL_RAW = '#FADBD8'   # Very faint light red
COLOR_ACTUAL_ROLL = '#C0392B'  # Deep crimson red for Actual rolling average
COLOR_MARL_RAW = '#D5F5E3'     # Very faint light green
COLOR_MARL_ROLL = '#27AE60'    # Deep emerald green for Optimised rolling average

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

def generate_rewards_whole_journey_comparison():
    print("[INFO] Loading files for whole journey Actual vs. Optimised reward plots...")
    
    # File paths
    def_soc_file = os.path.join(OUTPUT_DIR, 'default_ev_state_of_charge.csv')
    def_vel_file = os.path.join(OUTPUT_DIR, 'default_ev_velocity.csv')
    def_energy_file = os.path.join(OUTPUT_DIR, 'default_ev_energy_consumption.csv')
    
    marl_soc_file = os.path.join(OUTPUT_DIR, 'marl_ev_state_of_charge.csv')
    marl_vel_file = os.path.join(OUTPUT_DIR, 'marl_ev_velocity.csv')
    marl_energy_file = os.path.join(OUTPUT_DIR, 'marl_ev_energy_consumption.csv')
    
    traffic_file = os.path.join(OUTPUT_DIR, 'traffic_info.csv')
    
    files = [def_soc_file, def_vel_file, def_energy_file, marl_soc_file, marl_vel_file, marl_energy_file, traffic_file]
    if not all(os.path.exists(f) for f in files):
        print("[ERROR] CSV files missing. Please run simulation first.")
        return
        
    # Load and clean data
    df_def_vel = load_and_clean_csv(def_vel_file)
    df_def_energy_raw = load_and_clean_csv(def_energy_file)
    df_def_energy = df_def_energy_raw.pivot(index='Timestamp(s)', columns='VehicleID', values='Energy_Consumed(kWh)').reset_index()
    
    df_marl_vel = load_and_clean_csv(marl_vel_file)
    df_marl_energy_raw = load_and_clean_csv(marl_energy_file)
    df_marl_energy = df_marl_energy_raw.pivot(index='Timestamp(s)', columns='VehicleID', values='Energy_Consumed(kWh)').reset_index()
    
    df_traffic = load_and_clean_csv(traffic_file)
    
    # Calculate step rewards
    def_rewards = {}
    marl_rewards = {}
    for ev_id in EV_IDS:
        def_rewards[ev_id] = calculate_rewards(df_def_vel, df_def_energy, df_traffic, ev_id)
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
        
        # 1. Plot Default (Actual)
        df_ev_def = def_rewards[ev_id].dropna(subset=[f'{ev_id}_vel'])
        time_min_def = df_ev_def['Timestamp(s)'] / 60.0
        raw_rewards_def = df_ev_def['Reward']
        rolling_rewards_def = raw_rewards_def.rolling(window=30, min_periods=1).mean()
        
        ax.plot(time_min_def, raw_rewards_def, color=COLOR_ACTUAL_RAW, alpha=0.45, linewidth=0.8)
        ax.plot(time_min_def, rolling_rewards_def, color=COLOR_ACTUAL_ROLL, linewidth=2.2, label='Actual (Default)')
        
        # 2. Plot MARL (Optimised)
        df_ev_marl = marl_rewards[ev_id].dropna(subset=[f'{ev_id}_vel'])
        time_min_marl = df_ev_marl['Timestamp(s)'] / 60.0
        raw_rewards_marl = df_ev_marl['Reward']
        rolling_rewards_marl = raw_rewards_marl.rolling(window=30, min_periods=1).mean()
        
        ax.plot(time_min_marl, raw_rewards_marl, color=COLOR_MARL_RAW, alpha=0.45, linewidth=0.8)
        ax.plot(time_min_marl, rolling_rewards_marl, color=COLOR_MARL_ROLL, linewidth=2.2, label='Optimised (MARL)')
        
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
            ax.set_ylabel("Step Reward Comparison", fontsize=18, fontweight='bold')
            
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
    print(f"[SUCCESS] Saved whole journey reward comparison plot to: {PLOT_PATH}")

if __name__ == '__main__':
    generate_rewards_whole_journey_comparison()
