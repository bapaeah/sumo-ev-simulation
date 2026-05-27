#!/usr/bin/env python3
"""
Reads the simulation CSV outputs from output/ and compiles two separate
comparison CSV reports: one for SOC and one for Energy consumption (Without vs. With MARL).
"""

import os
import csv
import pandas as pd
import numpy as np

# Directories
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_DIR = os.path.join(BASE_DIR, 'output')
SOC_REPORT_PATH = os.path.join(OUTPUT_DIR, 'marl_soc_comparison_report.csv')
ENERGY_REPORT_PATH = os.path.join(OUTPUT_DIR, 'marl_energy_comparison_report.csv')

EV_SPECS = {
    'ev_01': {'capacity': 40, 'initial_soc': 80},
    'ev_02': {'capacity': 60, 'initial_soc': 85},
    'ev_03': {'capacity': 75, 'initial_soc': 90},
    'ev_04': {'capacity': 50, 'initial_soc': 70},
    'ev_05': {'capacity': 55, 'initial_soc': 75}
}

def load_and_clean_csv(file_path):
    df = pd.read_csv(file_path)
    df = df.replace('N/A', np.nan)
    for col in df.columns:
        if col not in ['Time(Time)', 'Time(HH:MM:SS)', 'VehicleID']:
            df[col] = pd.to_numeric(df[col], errors='coerce')
    return df

def generate_reports():
    print("[INFO] Loading comparative data files...")
    
    # File Paths
    def_soc_file = os.path.join(OUTPUT_DIR, 'default_ev_state_of_charge.csv')
    marl_soc_file = os.path.join(OUTPUT_DIR, 'marl_ev_state_of_charge.csv')
    def_energy_file = os.path.join(OUTPUT_DIR, 'default_ev_energy_consumption.csv')
    marl_energy_file = os.path.join(OUTPUT_DIR, 'marl_ev_energy_consumption.csv')
    
    if not all(os.path.exists(f) for f in [def_soc_file, marl_soc_file, def_energy_file, marl_energy_file]):
        print("[ERROR] Simulation outputs are missing. Run the simulation first.")
        return
        
    df_def_soc = load_and_clean_csv(def_soc_file)
    df_marl_soc = load_and_clean_csv(marl_soc_file)
    
    df_def_energy_raw = load_and_clean_csv(def_energy_file)
    df_def_energy = df_def_energy_raw.pivot(index='Timestamp(s)', columns='VehicleID', values='Energy_Consumed(kWh)').reset_index()
    
    df_marl_energy_raw = load_and_clean_csv(marl_energy_file)
    df_marl_energy = df_marl_energy_raw.pivot(index='Timestamp(s)', columns='VehicleID', values='Energy_Consumed(kWh)').reset_index()
    
    # --- Report 1: SOC Comparison ---
    soc_headers = ['VehicleID', 'Initial_SOC(%)', 'Final_SOC_Without_MARL(%)', 'Final_SOC_With_MARL(%)', 'SOC_Saved(%)']
    soc_rows = []
    
    # --- Report 2: Energy Comparison ---
    energy_headers = ['VehicleID', 'Battery_Capacity(kWh)', 'Energy_Without_MARL(kWh)', 'Energy_With_MARL(kWh)', 'Energy_Saved(kWh)', 'Efficiency_Gain(%)']
    energy_rows = []
    
    total_def_energy = 0.0
    total_marl_energy = 0.0
    total_capacity = 0.0
    
    for ev_id, specs in EV_SPECS.items():
        capacity = specs['capacity']
        init_soc = specs['initial_soc']
        total_capacity += capacity
        
        # SOC Data Extraction
        soc_def = df_def_soc[ev_id].dropna().iloc[-1]
        soc_marl = df_marl_soc[ev_id].dropna().iloc[-1]
        soc_saved = soc_marl - soc_def
        
        soc_rows.append([
            ev_id,
            f"{init_soc:.1f}",
            f"{soc_def:.2f}",
            f"{soc_marl:.2f}",
            f"{soc_saved:.2f}"
        ])
        
        # Energy Data Extraction
        energy_def = df_def_energy[ev_id].dropna().iloc[-1] if ev_id in df_def_energy.columns else 0.0
        energy_marl = df_marl_energy[ev_id].dropna().iloc[-1] if ev_id in df_marl_energy.columns else 0.0
        
        total_def_energy += energy_def
        total_marl_energy += energy_marl
        
        energy_saved = energy_def - energy_marl
        efficiency_gain = (energy_saved / energy_def) * 100.0 if energy_def > 0 else 0.0
        
        energy_rows.append([
            ev_id,
            f"{capacity}",
            f"{energy_def:.3f}",
            f"{energy_marl:.3f}",
            f"{energy_saved:.3f}",
            f"{efficiency_gain:.1f}"
        ])
        
    # Add summary rows
    soc_rows.append([
        'AVERAGE/SUMMARY',
        'N/A',
        'N/A',
        'N/A',
        'N/A'
    ])
    
    total_energy_saved = total_def_energy - total_marl_energy
    total_efficiency_gain = (total_energy_saved / total_def_energy) * 100.0 if total_def_energy > 0 else 0.0
    
    energy_rows.append([
        'TOTAL',
        f"{total_capacity}",
        f"{total_def_energy:.3f}",
        f"{total_marl_energy:.3f}",
        f"{total_energy_saved:.3f}",
        f"{total_efficiency_gain:.1f}"
    ])
    
    # Save SOC CSV
    with open(SOC_REPORT_PATH, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(soc_headers)
        writer.writerows(soc_rows)
        
    # Save Energy CSV
    with open(ENERGY_REPORT_PATH, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(energy_headers)
        writer.writerows(energy_rows)
        
    print(f"[SUCCESS] SOC comparison saved to: {SOC_REPORT_PATH}")
    print(f"[SUCCESS] Energy comparison saved to: {ENERGY_REPORT_PATH}")

if __name__ == '__main__':
    generate_reports()
