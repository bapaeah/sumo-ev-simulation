#!/usr/bin/env python3
"""
Generates a comprehensive 2x3 grid comparison plot for the RL reward function.
Row 1: Actual (Without MARL - Default Run) Rewards for all 5 EVs
Row 2: Optimised (With MARL - MARL Run) Rewards for all 5 EVs
Columns: Low Traffic, Medium Traffic, Heavy Traffic
X-axis: 1-Minute Window (0 to 60 seconds)
"""

import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# Directories
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_DIR = os.path.join(BASE_DIR, 'output')
PLOT_PATH = os.path.join(OUTPUT_DIR, 'ev_rewards_traffic_comparison.png')

# EV IDs and Colors
EV_IDS = ['ev_01', 'ev_02', 'ev_03', 'ev_04', 'ev_05']
EV_COLORS = {
    'ev_01': '#FF6B6B',    # Red
    'ev_02': '#4ECDC4',    # Teal
    'ev_03': '#45B7D1',    # Blue
    'ev_04': '#FFA07A',    # Orange
    'ev_05': '#98D8C8'     # Mint
}

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
    # Align DataFrames on Timestamp(s)
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
        # 1. Delta Energy (kWh)
        curr_energy = row[f'{ev_id}_energy']
        if idx == 0:
            delta_energy = 0.0
        else:
            delta_energy = max(0.0, curr_energy - prev_energy)
        prev_energy = curr_energy
        
        # Energy penalty (weight -100.0)
        energy_penalty = -100.0 * delta_energy
        
        # 2. Speed matching utility
        speed_limit_mps = 15.0  # Road Speed Limit: 54 km/h (15 m/s)
        speed_mps = row[f'{ev_id}_vel'] / 3.6  # Convert km/h to m/s
        
        speed_ratio = speed_mps / speed_limit_mps
        speed_reward = 1.0 - abs(speed_ratio - 1.0)
        
        # 3. Standstill penalty
        bg_speed_mps = row['Avg_Background_Speed(km/h)'] / 3.6
        standstill_penalty = 0.0
        if speed_mps < 0.5 and bg_speed_mps > 5.0:
            standstill_penalty = -2.0
            
        # Balanced step reward
        step_reward = energy_penalty + 0.5 * speed_reward + standstill_penalty
        rewards.append(step_reward)
        
    df['Reward'] = rewards
    return df

def generate_rewards_grid():
    print("[INFO] Loading files for reward function comparison plots...")
    
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
    
    # Calculate rewards for both runs for all 5 EVs
    def_rewards = {}
    marl_rewards = {}
    for ev_id in EV_IDS:
        def_rewards[ev_id] = calculate_rewards(df_def_vel, df_def_energy, df_traffic, ev_id)
        marl_rewards[ev_id] = calculate_rewards(df_marl_vel, df_marl_energy, df_traffic, ev_id)
        
    # Define 1-minute windows
    windows = {
        'Low Traffic': (109, 168),
        'Medium Traffic': (655, 714),
        'Heavy Traffic': (1084, 1143)
    }
    
    # Create 2x3 subplot grid (Row 0: Actual, Row 1: Optimised)
    fig, axes = plt.subplots(2, 3, figsize=(22, 12), sharex='col', sharey='row', dpi=150)
    
    plt.rcParams.update({
        'font.size': 13,
        'axes.labelsize': 16,
        'xtick.labelsize': 14,
        'ytick.labelsize': 14,
        'legend.fontsize': 11
    })
    
    time_sec = np.arange(1, 61)  # 1 to 60 seconds
    
    for col_idx, (level_name, (start_t, end_t)) in enumerate(windows.items()):
        # ----------------------------------------------------
        # ROW 1: Actual (Without MARL - Default)
        # ----------------------------------------------------
        ax_def = axes[0, col_idx]
        for ev_id in EV_IDS:
            ev_rew_df = def_rewards[ev_id]
            sub = ev_rew_df[(ev_rew_df['Timestamp(s)'] >= start_t) & (ev_rew_df['Timestamp(s)'] <= end_t)].copy()
            sub = sub.sort_values(by='Timestamp(s)').reset_index(drop=True)
            ax_def.plot(time_sec, sub['Reward'][:60], color=EV_COLORS[ev_id], linewidth=2.0, label=f"{ev_id.upper()}")
            
        ax_def.grid(True, linestyle='--', alpha=0.5)
        ax_def.tick_params(axis='both', which='major', labelsize=14)
        ax_def.set_title(f"{level_name} - Actual", fontsize=16, fontweight='bold', pad=8)
        if col_idx == 0:
            ax_def.set_ylabel("Step Reward (Actual)", fontsize=16, fontweight='bold')
            ax_def.legend(loc='lower left', ncol=5, framealpha=0.9)
            
        # ----------------------------------------------------
        # ROW 2: Optimised (With MARL - Eco-Driving)
        # ----------------------------------------------------
        ax_marl = axes[1, col_idx]
        for ev_id in EV_IDS:
            ev_rew_df = marl_rewards[ev_id]
            sub = ev_rew_df[(ev_rew_df['Timestamp(s)'] >= start_t) & (ev_rew_df['Timestamp(s)'] <= end_t)].copy()
            sub = sub.sort_values(by='Timestamp(s)').reset_index(drop=True)
            ax_marl.plot(time_sec, sub['Reward'][:60], color=EV_COLORS[ev_id], linewidth=2.0, label=f"{ev_id.upper()}")
            
        ax_marl.grid(True, linestyle='--', alpha=0.5)
        ax_marl.tick_params(axis='both', which='major', labelsize=14)
        ax_marl.set_xlabel("Time (seconds)", fontsize=16, fontweight='bold')
        ax_marl.set_title(f"{level_name} - Optimised", fontsize=16, fontweight='bold', pad=8)
        if col_idx == 0:
            ax_marl.set_ylabel("Step Reward (Optimised)", fontsize=16, fontweight='bold')
            ax_marl.legend(loc='lower left', ncol=5, framealpha=0.9)
            
        # Set y-limits to encapsulate standard reward ranges [e.g., -5, 2]
        # In case of massive penalties, let's keep it tight but visible
        ax_def.set_ylim(-4.5, 1.5)
        ax_marl.set_ylim(-4.5, 1.5)
        
    plt.suptitle("RL Reward Function Profile Analysis: 1-Minute Detailed Window Comparison\nDecentralized Step Rewards for all 5 EVs under Dynamic Traffic Volumes", 
                 fontsize=18, fontweight='bold', y=0.97)
    
    plt.tight_layout(rect=[0, 0.02, 1, 0.93])
    plt.savefig(PLOT_PATH, bbox_inches='tight')
    plt.close()
    print(f"[SUCCESS] Saved rewards comparative plot successfully to: {PLOT_PATH}")

if __name__ == '__main__':
    generate_rewards_grid()
