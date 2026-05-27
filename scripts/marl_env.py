#!/usr/bin/env python3
"""
Multi-Agent Reinforcement Learning (MARL) Environment for SUMO EV Simulation
Formulates a Gym-compatible Multi-Agent Environment interface for RL training.
Optimizes EV Energy Efficiency, Velocity alignment, and Congestion control.
"""

import os
import sys
import numpy as np
from pathlib import Path

# Add SUMO tools to path
if 'SUMO_HOME' in os.environ:
    tools = os.path.join(os.environ['SUMO_HOME'], 'tools')
    sys.path.append(tools)
else:
    print("[WARNING] SUMO_HOME environment variable not set.")

try:
    import traci
except ImportError:
    print("[WARNING] TraCI library not found. Please install sumolib and traci.")

# Environment Config Constants
EV_SPECS = {
    'ev_01': {'capacity': 40, 'initial_soc': 80},
    'ev_02': {'capacity': 60, 'initial_soc': 85},
    'ev_03': {'capacity': 75, 'initial_soc': 90},
    'ev_04': {'capacity': 50, 'initial_soc': 70},
    'ev_05': {'capacity': 55, 'initial_soc': 75}
}

CONSUMPTION_RATE = 0.15  # kWh per km

class SUMOMARLEnv:
    """
    SUMO Multi-Agent Reinforcement Learning Gym-like environment.
    Decoupled environment wrapper for training MARL algorithms.
    """
    def __init__(self, sumo_config_path=None, max_steps=1200):
        # Resolve config paths
        if sumo_config_path is None:
            self.sumo_config = os.path.join(os.path.dirname(__file__), '..', 'config', 'simulation.sumocfg')
        else:
            self.sumo_config = sumo_config_path
            
        self.max_steps = max_steps
        self.agents = list(EV_SPECS.keys())
        
        # Observation and Action Spaces
        # State space size: 9 (v_i, SOC_i, E_i, d_i, x_junc, N_bg, v_bg, N_ped, v_limit)
        self.observation_dim = 9
        # Action space size: 3 (0: DECEL, 1: COAST, 2: ACCEL)
        self.action_dim = 3
        
        # State normalization factors (min-max scaling limits)
        self.max_speed_ref = 22.22  # 80 km/h in m/s
        self.max_energy_ref = 15.0  # max expected leg energy consumption in kWh
        
        # Environment runtime parameters
        self.timestep = 0
        self.ev_data = {}
        
    def reset(self):
        """
        Resets the SUMO simulation environment.
        Returns:
            observations (dict): Initial joint state observations {agent_id: observation_vector}
        """
        self.timestep = 0
        
        # Initialize EV logs
        self.ev_data = {
            ev_id: {
                'soc': specs['initial_soc'],
                'energy_consumed': 0.0,
                'distance': 0.0,
                'capacity': specs['capacity'],
                'prev_speed': 0.0
            }
            for ev_id, specs in EV_SPECS.items()
        }
        
        # Start/Restart SUMO simulation via TraCI
        sumo_cmd = ['sumo', '-c', self.sumo_config, '--step-length', '1.0', 
                    '--no-step-log', '--xml-validation', 'never', '--no-warnings']
        
        # If TraCI is already running, close it first
        try:
            traci.close()
        except Exception:
            pass
            
        traci.start(sumo_cmd)
        
        # Advance simulation one step to populate initial vehicles
        traci.simulationStep()
        self.timestep = 1
        
        return self._get_observations()
        
    def step(self, joint_action):
        """
        Advances the simulation by 1 step applying the joint actions.
        Args:
            joint_action (dict): {agent_id: action_id} where action_id in [0, 1, 2]
        Returns:
            observations (dict): Joint observation vectors
            rewards (dict): Joint reward floats
            terminations (dict): Joint termination boolean flags (True if EV exited)
            truncations (dict): Joint truncation boolean flags (True if timestep limit reached)
            infos (dict): Diagnostic info dictionary
        """
        # 1. Apply Actions to all active EV agents
        active_vehicles = traci.vehicle.getIDList()
        
        for agent_id in self.agents:
            if agent_id in active_vehicles and agent_id in joint_action:
                action = joint_action[agent_id]
                self._apply_agent_action(agent_id, action)
                
        # 2. Advance SUMO simulation by 1 second (1 step)
        traci.simulationStep()
        self.timestep += 1
        
        # Update local physical states (SOC, distance, consumption) for active vehicles
        active_vehicles = traci.vehicle.getIDList()
        for ev_id in self.agents:
            if ev_id in active_vehicles:
                try:
                    speed = traci.vehicle.getSpeed(ev_id)
                    # Update internal tracking variables
                    self._update_ev_internals(ev_id, speed)
                except traci.TraCIException:
                    pass
                    
        # 3. Calculate observations, rewards, and status flags
        observations = self._get_observations()
        rewards = self._get_rewards(observations)
        
        # Terminations: true if EV has completed its route and exited the simulation
        terminations = {
            agent_id: (agent_id not in active_vehicles and self.timestep > 10)
            for agent_id in self.agents
        }
        
        # Truncations: true if global simulation duration limit is hit
        truncations = {
            agent_id: (self.timestep >= self.max_steps)
            for agent_id in self.agents
        }
        
        # Overall termination check
        all_done = all(terminations.values()) or all(truncations.values())
        if all_done:
            try:
                traci.close()
            except Exception:
                pass
                
        infos = {
            'step': self.timestep,
            'active_evs': [v for v in self.agents if v in active_vehicles]
        }
        
        return observations, rewards, terminations, truncations, infos
        
    def _apply_agent_action(self, agent_id, action_id):
        """
        Maps discrete actions to live TraCI command calls.
        Decoded Actions:
          0: DECEL (-1.5 m/s^2)
          1: COAST (Maintain speed, 0 acceleration)
          2: ACCEL (+1.5 m/s^2)
        """
        try:
            current_speed = traci.vehicle.getSpeed(agent_id)
            
            # Action Mapping
            if action_id == 0:  # DECEL
                target_speed = max(0.0, current_speed - 1.5)
                # Apply decel target speed using TraCI (duration 1 second)
                traci.vehicle.slowDown(agent_id, target_speed, 1.0)
            elif action_id == 2:  # ACCEL
                speed_limit = traci.vehicle.getAllowedSpeed(agent_id)
                target_speed = min(speed_limit, current_speed + 1.5)
                traci.vehicle.slowDown(agent_id, target_speed, 1.0)
            else:  # COAST / Maintain speed
                # Let SUMO car-following model maintain the speed naturally
                traci.vehicle.setSpeed(agent_id, -1)  
        except traci.TraCIException:
            pass
            
    def calculate_dynamic_energy(self, ev_id, current_speed, prev_speed, dt=1.0):
        """Calculates dynamic electrical energy consumed (in kWh) in this step using tractive physics"""
        # Mass by battery capacity
        masses = {
            'ev_01': 1600,
            'ev_02': 1800,
            'ev_03': 2000,
            'ev_04': 1700,
            'ev_05': 1750
        }
        m = masses.get(ev_id, 1800)
        
        # Physics constants
        g = 9.81
        rho = 1.2
        Cd = 0.28
        A = 2.2
        fr = 0.01
        
        # Calculate forces
        F_drag = 0.5 * rho * Cd * A * (current_speed ** 2)
        F_rolling = m * g * fr
        
        # Acceleration
        a = (current_speed - prev_speed) / dt
        F_accel = m * a
        
        F_total = F_drag + F_rolling + F_accel
        
        # Tractive Power (Watts)
        P_tractive = F_total * current_speed
        
        # Electrical Power (Watts)
        if P_tractive > 0:
            P_elec = P_tractive / 0.90  # 90% motor efficiency
        else:
            P_elec = P_tractive * 0.70  # 70% regenerative efficiency
            
        # Convert Watts to kWh over the time step
        energy_kwh = (P_elec * dt) / 3600000.0
        
        # Bound power spikes for physical realism
        # Max discharge: 150 kW, Max regen: 80 kW
        max_discharge_kwh = (150000.0 * dt) / 3600000.0
        max_regen_kwh = (-80000.0 * dt) / 3600000.0
        
        energy_kwh = max(max_regen_kwh, min(max_discharge_kwh, energy_kwh))
        return energy_kwh
            
    def _update_ev_internals(self, ev_id, speed, dt=1.0):
        """Updates internal charge and distance metrics based on speed"""
        distance_km = (speed * dt) / 1000.0
        
        # Calculate dynamic energy consumption
        prev_speed = self.ev_data[ev_id]['prev_speed']
        energy_consumed = self.calculate_dynamic_energy(ev_id, speed, prev_speed, dt)
        
        self.ev_data[ev_id]['distance'] += distance_km
        self.ev_data[ev_id]['energy_consumed'] += energy_consumed
        
        # Calculate SOC
        initial_energy = self.ev_data[ev_id]['capacity'] * (EV_SPECS[ev_id]['initial_soc'] / 100.0)
        remaining_energy = initial_energy - self.ev_data[ev_id]['energy_consumed']
        soc = (remaining_energy / self.ev_data[ev_id]['capacity']) * 100.0
        self.ev_data[ev_id]['soc'] = max(0.0, min(100.0, soc))
        self.ev_data[ev_id]['prev_speed'] = speed
        
    def _get_observations(self):
        """
        Assembles observation state vector for all 5 EVs.
        Outputs normalized float observations.
        """
        active_vehicles = []
        try:
            active_vehicles = traci.vehicle.getIDList()
        except Exception:
            pass
            
        observations = {}
        
        # Calculate global traffic variables
        total_vehicles = len(active_vehicles)
        bg_count = sum(1 for v in active_vehicles if v not in self.agents)
        ev_count = total_vehicles - bg_count
        
        # Average background speed
        bg_speeds = []
        for v_id in active_vehicles:
            if v_id not in self.agents:
                try:
                    bg_speeds.append(traci.vehicle.getSpeed(v_id))
                except Exception:
                    pass
        avg_bg_speed = sum(bg_speeds) / len(bg_speeds) if bg_speeds else 0.0
        
        # Pedestrians
        try:
            active_pedestrians = len(traci.person.getIDList())
        except Exception:
            active_pedestrians = 0
            
        # Assemble observation for each agent
        for agent_id in self.agents:
            if agent_id in active_vehicles:
                try:
                    # Local State Variables
                    speed = traci.vehicle.getSpeed(agent_id)
                    speed_limit = traci.vehicle.getAllowedSpeed(agent_id)
                    soc = self.ev_data[agent_id]['soc']
                    energy = self.ev_data[agent_id]['energy_consumed']
                    distance = self.ev_data[agent_id]['distance']
                    
                    # Estimate distance to next junction using current lane length and position
                    try:
                        lane_id = traci.vehicle.getLaneID(agent_id)
                        lane_length = traci.lane.getLength(lane_id)
                        lane_pos = traci.vehicle.getLanePosition(agent_id)
                        dist_to_junc = max(0.0, lane_length - lane_pos)
                    except Exception:
                        dist_to_junc = 500.0
                    
                    # Normalize observations to [0, 1] range for RL training stability
                    obs_vector = np.array([
                        speed / self.max_speed_ref,                  # 1. Normalized speed
                        soc / 100.0,                                 # 2. Normalized SOC
                        energy / self.max_energy_ref,                # 3. Normalized energy
                        distance / 25.0,                             # 4. Normalized distance (scale based on 23.8km trip)
                        min(1.0, dist_to_junc / 1000.0),             # 5. Normalized junction proximity
                        min(1.0, bg_count / 400.0),                  # 6. Normalized background vehicles
                        avg_bg_speed / self.max_speed_ref,           # 7. Normalized traffic average speed
                        min(1.0, active_pedestrians / 50.0),         # 8. Normalized pedestrians
                        speed_limit / self.max_speed_ref             # 9. Normalized speed limit
                    ], dtype=np.float32)
                    
                except Exception:
                    # Fallback observation if TraCI query fails intermittently
                    obs_vector = np.zeros(self.observation_dim, dtype=np.float32)
            else:
                # Agent has either not departed yet or has successfully completed its route
                obs_vector = np.zeros(self.observation_dim, dtype=np.float32)
                
            observations[agent_id] = obs_vector
            
        return observations
        
    def _get_rewards(self, observations):
        """
        Calculates individual multi-objective reward for all 5 agents.
        Optimizes travel delay and energy efficiency.
        """
        rewards = {}
        active_vehicles = []
        try:
            active_vehicles = traci.vehicle.getIDList()
        except Exception:
            pass
            
        for agent_id in self.agents:
            if agent_id in active_vehicles:
                # 1. Energy consumption penalty (delta energy in last second) using physics-based dynamic model
                speed = traci.vehicle.getSpeed(agent_id)
                prev_speed = self.ev_data[agent_id]['prev_speed']
                delta_energy = self.calculate_dynamic_energy(agent_id, speed, prev_speed, 1.0)
                energy_penalty = -100.0 * delta_energy         # Weight: 100.0
                
                # 2. Speed matching utility (reward speed close to limit)
                speed_limit = traci.vehicle.getAllowedSpeed(agent_id)
                if speed_limit > 0:
                    speed_ratio = speed / speed_limit
                    speed_reward = 1.0 - abs(speed_ratio - 1.0)
                else:
                    speed_reward = 0.0
                    
                # 3. Standstill penalty: penalize staying at speed 0 unless there is traffic
                # If traffic speed is flowing (> 5 m/s) but EV speed is 0
                bg_speed_vector = observations[agent_id][6] * self.max_speed_ref
                standstill_penalty = 0.0
                if speed < 0.5 and bg_speed_vector > 5.0:
                    standstill_penalty = -2.0
                    
                # Balanced joint reward
                rewards[agent_id] = float(energy_penalty + 0.5 * speed_reward + standstill_penalty)
            else:
                # If the agent has completed its route and exited, reward it for successful completion
                if self.timestep > 10 and self.ev_data[agent_id]['distance'] > 20.0:
                    rewards[agent_id] = 100.0  # Big positive completion reward
                else:
                    rewards[agent_id] = 0.0
                    
        return rewards
        
    def close(self):
        """Closes TraCI connection and shuts down SUMO"""
        try:
            traci.close()
        except Exception:
            pass

if __name__ == '__main__':
    # Verify environment class works and is ready for integration
    env = SUMOMARLEnv()
    print("[SUCCESS] MARL Environment class structure created successfully!")
    print(f"  - Observation Dimension: {env.observation_dim}")
    print(f"  - Action Dimension: {env.action_dim}")
    print(f"  - Configured Agents: {env.agents}")
