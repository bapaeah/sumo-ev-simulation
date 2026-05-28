#!/usr/bin/env python3
"""
Generates a highly-detailed 1x5 grid comparison plot for the RL reward functions.
Overlays the Optimised (MARL) rewards for all three traffic levels (Low, Medium, Heavy)
on a single plot for each of the 5 EVs.
Columns:
  a, b, c, d, e (corresponding to ev_01, ev_02, ev_03, ev_04, ev_05)
In each subplot: Overlays Low Traffic (Green), Medium Traffic (Orange), and Heavy Traffic (Red) Optimised rewards.
"""

import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# Directories
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_DIR = os.path.join(BASE_DIR, 'output')
PLOT_PATH = os.path.join(OUTPUT_DIR, 'marl_rewards_levels_comparison.png')

# EV IDs and column mappings
EV_MAPPINGS = {
    'ev_01': 'a',
    'ev_02': 'b',
    'ev_03': 'c',
    'ev_04': 'd',
    'ev_05': 'e'
}
EV_IDS = list(EV_MAPPINGS.keys())

# Premium traffic colors
COLOR_LOW = '#2ECC71'    # Emerald Green for Low Traffic
COLOR_MED = '#F39C12'    # Vibrant Orange for Medium Traffic
COLOR_HEAVY = '#E74C3C'  # Crimson Red for Heavy Traffic

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

def generate_rewards_comparison():
    print("[INFO] Loading files for optimised reward function levels comparison grid...")
    
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
        
    # Define Windows
    windows = {
        'Low Traffic': (109, 168),
        'Medium Traffic': (655, 714),
        'Heavy Traffic': (1084, 1143)
    }
    
    # Create 1x5 subplot grid
    fig, axes = plt.subplots(1, 5, figsize=(25, 6), sharey=True, dpi=150)
    
    # Enable premium styling
    plt.rcParams.update({
        'font.size': 14,
        'axes.labelsize': 18,
        'xtick.labelsize': 16,
        'ytick.labelsize': 16,
        'legend.fontsize': 13
    })
    
    time_sec = np.arange(1, 61)  # 1 to 60 seconds
    
    for col_idx, ev_id in enumerate(EV_IDS):
        ax = axes[col_idx]
        
        # Plot each traffic state's optimised reward
        # Low Traffic (Green)
        df_low = marl_rewards[ev_id]
        sub_low = df_low[(df_low['Timestamp(s)'] >= windows['Low Traffic'][0]) & (df_low['Timestamp(s)'] <= windows['Low Traffic'][1])].copy()
        sub_low = sub_low.sort_values(by='Timestamp(s)').reset_index(drop=True)
        ax.plot(time_sec, sub_low['Reward'][:60], color=COLOR_LOW, linewidth=2.5, label='Low Traffic')
        
        # Medium Traffic (Orange)
        df_med = marl_rewards[ev_id]
        sub_med = df_med[(df_med['Timestamp(s)'] >= windows['Medium Traffic'][0]) & (df_med['Timestamp(s)'] <= windows['Medium Traffic'][1])].copy()
        sub_med = sub_med.sort_values(by='Timestamp(s)').reset_index(drop=True)
        ax.plot(time_sec, sub_med['Reward'][:60], color=COLOR_MED, linewidth=2.5, label='Medium Traffic')
        
        # Heavy Traffic (Red)
        df_heavy = marl_rewards[ev_id]
        sub_heavy = df_heavy[(df_heavy['Timestamp(s)'] >= windows['Heavy Traffic'][0]) & (df_heavy['Timestamp(s)'] <= windows['Heavy Traffic'][1])].copy()
        sub_heavy = sub_heavy.sort_values(by='Timestamp(s)').reset_index(drop=True)
        ax.plot(time_sec, sub_heavy['Reward'][:60], color=COLOR_HEAVY, linewidth=2.5, label='Heavy Traffic')
        
        ax.grid(True, linestyle='--', alpha=0.5)
        ax.tick_params(axis='both', which='major', labelsize=16)
        
        # Column headers sequential
        ax.set_title(f"{EV_MAPPINGS[ev_id]}", fontsize=22, fontweight='bold', pad=10)
        
        # Y-axis label on the first column of subplots
        if col_idx == 0:
            ax.set_ylabel("Optimised Step Reward", fontsize=18, fontweight='bold')
            
        # X-axis label on all subplots
        ax.set_xlabel("Time (seconds)", fontsize=18, fontweight='bold')
            
        # Add legend only to the first subplot to keep layout completely clean
        if col_idx == 0:
            ax.legend(loc='lower left', framealpha=0.9, fontsize=13)
            
        # Fix standard vertical reward range to encapsulate all curves perfectly
        ax.set_ylim(-4.5, 1.5)
        
    # Compact layout optimization
    plt.tight_layout(pad=1.2, w_pad=0.8)
    
    # Save the figure
    plt.savefig(PLOT_PATH, bbox_inches='tight')
    plt.close()
    print(f"[SUCCESS] Saved optimised reward levels comparison plot to: {PLOT_PATH}")

if __name__ == '__main__':
    generate_rewards_comparison()
