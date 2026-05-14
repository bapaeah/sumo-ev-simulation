#!/usr/bin/env python3
"""
SUMO Network Diagram Generator
Creates a comprehensive visualization of the SUMO network with roads, junctions,
and vehicle routes for the Marathalli to ETV simulation.
"""

import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import FancyBboxPatch, Circle, FancyArrowPatch, Polygon
from matplotlib.collections import PatchCollection
import numpy as np
from pathlib import Path
import os

# Network Configuration
NETWORK_X_MIN, NETWORK_X_MAX = -500, 12000
NETWORK_Y_MIN, NETWORK_Y_MAX = -500, 5500

# Junction definitions
JUNCTIONS = {
    'marathalli': {'pos': (0, 0), 'name': 'Marathalli', 'color': '#FFD700'},
    'whitefield': {'pos': (5000, 1500), 'name': 'Whitefield', 'color': '#FFD700'},
    'silk_board': {'pos': (8500, 3200), 'name': 'Silk Board', 'color': '#FFD700'},
    'etv_junction': {'pos': (11000, 4500), 'name': 'ETV Junction', 'color': '#FFD700'}
}

# Edge (Road) definitions
EDGES = [
    {
        'id': 'marathalli_whitefield',
        'from': 'marathalli',
        'to': 'whitefield',
        'start': (0, 0),
        'end': (5000, 1500),
        'name': 'Marathalli → Whitefield',
        'type': 'main',
        'speed': 15,
        'lanes': 3
    },
    {
        'id': 'whitefield_silk',
        'from': 'whitefield',
        'to': 'silk_board',
        'start': (5000, 1500),
        'end': (8500, 3200),
        'name': 'Whitefield → Silk Board',
        'type': 'main',
        'speed': 12,
        'lanes': 3
    },
    {
        'id': 'silk_etv',
        'from': 'silk_board',
        'to': 'etv_junction',
        'start': (8500, 3200),
        'end': (11000, 4500),
        'name': 'Silk Board → ETV',
        'type': 'main',
        'speed': 10,
        'lanes': 3
    },
    {
        'id': 'etv_silk',
        'from': 'etv_junction',
        'to': 'silk_board',
        'start': (11000, 4500),
        'end': (8500, 3200),
        'name': 'ETV → Silk Board',
        'type': 'return',
        'speed': 10,
        'lanes': 3
    },
    {
        'id': 'silk_whitefield',
        'from': 'silk_board',
        'to': 'whitefield',
        'start': (8500, 3200),
        'end': (5000, 1500),
        'name': 'Silk Board → Whitefield',
        'type': 'return',
        'speed': 12,
        'lanes': 3
    },
    {
        'id': 'whitefield_marathalli',
        'from': 'whitefield',
        'to': 'marathalli',
        'start': (5000, 1500),
        'end': (0, 0),
        'name': 'Whitefield → Marathalli',
        'type': 'return',
        'speed': 15,
        'lanes': 3
    }
]

# EV Specifications
EV_SPECS = {
    'ev_01': {'capacity': 40, 'initial_soc': 80, 'color': '#FF6B6B'},
    'ev_02': {'capacity': 60, 'initial_soc': 85, 'color': '#4ECDC4'},
    'ev_03': {'capacity': 75, 'initial_soc': 90, 'color': '#45B7D1'},
    'ev_04': {'capacity': 50, 'initial_soc': 70, 'color': '#FFA07A'},
    'ev_05': {'capacity': 55, 'initial_soc': 75, 'color': '#98D8C8'}
}


def draw_road_with_lanes(ax, start, end, edge_type, num_lanes=3, width=80):
    """
    Draw a road with multiple lanes and direction indicators
    """
    x1, y1 = start
    x2, y2 = end
    
    # Calculate direction vector
    dx = x2 - x1
    dy = y2 - y1
    length = np.sqrt(dx**2 + dy**2)
    dx_norm = dx / length
    dy_norm = dy / length
    
    # Perpendicular vector for lane width
    px = -dy_norm * width
    py = dx_norm * width
    
    # Road color based on type
    if edge_type == 'main':
        road_color = '#D3D3D3'  # Light gray
        line_color = '#808080'   # Dark gray
    else:
        road_color = '#E8E8E8'  # Lighter gray
        line_color = '#A9A9A9'   # Darker line
    
    # Draw road background
    road_rect = Polygon([
        (x1 + px, y1 + py),
        (x2 + px, y2 + py),
        (x2 - px, y2 - py),
        (x1 - px, y1 - py)
    ], closed=True, facecolor=road_color, edgecolor=line_color, linewidth=2)
    ax.add_patch(road_rect)
    
    # Draw lane markings
    for i in range(1, num_lanes):
        offset = (i / num_lanes) * 2 * width - width
        ax.plot([x1 + offset * dy_norm, x2 + offset * dy_norm],
               [y1 - offset * dx_norm, y2 - offset * dx_norm],
               'w--', linewidth=1, alpha=0.6)
    
    # Draw direction arrows
    num_arrows = 3
    for i in range(1, num_arrows + 1):
        arrow_pos = i / (num_arrows + 1)
        arrow_x = x1 + arrow_pos * dx
        arrow_y = y1 + arrow_pos * dy
        arrow = FancyArrowPatch(
            (arrow_x - dx_norm * 150, arrow_y - dy_norm * 150),
            (arrow_x + dx_norm * 150, arrow_y + dy_norm * 150),
            arrowstyle='->', mutation_scale=20, linewidth=2,
            color=line_color, alpha=0.6
        )
        ax.add_patch(arrow)


def draw_junction(ax, pos, name):
    """
    Draw a junction as a large circle with label
    """
    circle = Circle(pos, 180, color='#FFD700', ec='black', linewidth=3, zorder=5)
    ax.add_patch(circle)
    
    # Add junction name
    ax.text(pos[0], pos[1], name, ha='center', va='center',
           fontsize=10, fontweight='bold', zorder=6)


def draw_ev_symbol(ax, pos, ev_id, color, capacity, soc):
    """
    Draw an EV symbol on the route
    """
    # Car body
    car = FancyBboxPatch(
        (pos[0] - 80, pos[1] - 40),
        160, 80,
        boxstyle="round,pad=10",
        facecolor=color,
        edgecolor='black',
        linewidth=2,
        alpha=0.9,
        zorder=4
    )
    ax.add_patch(car)
    
    # Label
    ax.text(pos[0], pos[1] + 60, f"{ev_id}\n{capacity}kWh",
           ha='center', va='bottom', fontsize=8, fontweight='bold',
           bbox=dict(boxstyle='round', facecolor=color, alpha=0.7))


def create_network_diagram():
    """
    Create a comprehensive SUMO network diagram
    """
    fig, ax = plt.subplots(figsize=(18, 10), dpi=150)
    
    # Set network bounds
    ax.set_xlim(NETWORK_X_MIN, NETWORK_X_MAX)
    ax.set_ylim(NETWORK_Y_MIN, NETWORK_Y_MAX)
    ax.set_aspect('equal')
    
    # Background
    ax.set_facecolor('#F5F5F5')
    
    # Title
    title = "SUMO EV Simulation Network Diagram\nMarathalli to ETV Route"
    ax.set_title(title, fontsize=18, fontweight='bold', pad=20)
    
    # Draw roads
    for edge in EDGES:
        draw_road_with_lanes(ax, edge['start'], edge['end'], edge['type'])
    
    # Draw junctions
    for junction_id, junction_info in JUNCTIONS.items():
        draw_junction(ax, junction_info['pos'], junction_info['name'])
    
    # Draw EVs on their starting positions
    ev_positions = [
        (500, 200, 'ev_01'),
        (1000, 400, 'ev_02'),
        (1500, 600, 'ev_03'),
        (2000, 800, 'ev_04'),
        (2500, 1000, 'ev_05')
    ]
    
    for x, y, ev_id in ev_positions:
        draw_ev_symbol(ax, (x, y), ev_id, EV_SPECS[ev_id]['color'],
                      EV_SPECS[ev_id]['capacity'], EV_SPECS[ev_id]['initial_soc'])
    
    # Add grid
    ax.grid(True, alpha=0.2, linestyle=':', color='gray')
    
    # Axis labels
    ax.set_xlabel('X Coordinate (meters)', fontsize=12, fontweight='bold')
    ax.set_ylabel('Y Coordinate (meters)', fontsize=12, fontweight='bold')
    
    # Legend - Network Info
    legend_text = "Network Information:\n"
    legend_text += "━━━━━━━━━━━━━━━━━━━━━━━━\n"
    legend_text += "Junctions: 4\n"
    legend_text += "Roads: 6 (3 forward, 3 return)\n"
    legend_text += "Total Distance: ~21 km\n"
    legend_text += "Vehicles: 5 EVs\n"
    legend_text += "Consumption: 0.15 kWh/km"
    
    ax.text(0.02, 0.98, legend_text, transform=ax.transAxes,
           fontsize=10, verticalalignment='top', family='monospace',
           bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.9, pad=1))
    
    # EV Specifications Box
    ev_info = "EV Fleet Specifications:\n"
    ev_info += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
    for ev_id, specs in EV_SPECS.items():
        ev_info += f"● {ev_id}: {specs['capacity']} kWh, "
        ev_info += f"SOC: {specs['initial_soc']}%\n"
    
    ax.text(0.02, 0.65, ev_info, transform=ax.transAxes,
           fontsize=9, verticalalignment='top', family='monospace',
           bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.9, pad=1))
    
    # Road Details Box
    road_info = "Road Details:\n"
    road_info += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
    for i, edge in enumerate(EDGES, 1):
        road_info += f"{edge['name']}\n"
        road_info += f"  Speed: {edge['speed']} m/s | "
        road_info += f"Lanes: {edge['lanes']}\n"
    
    ax.text(0.98, 0.98, road_info, transform=ax.transAxes,
           fontsize=8, verticalalignment='top', horizontalalignment='right',
           family='monospace',
           bbox=dict(boxstyle='round', facecolor='lightgreen', alpha=0.9, pad=1))
    
    # Simulation Parameters
    param_info = "Simulation Parameters:\n"
    param_info += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
    param_info += "Duration: 600 seconds (10 min)\n"
    param_info += "Time Step: 1.0 second\n"
    param_info += "Screenshot Interval: 30 sec\n"
    param_info += "Traffic Flow: Enabled\n"
    param_info += "Pedestrians: 37 (3 flows)\n"
    param_info += "Vehicles: 5 EVs + Traffic"
    
    ax.text(0.98, 0.45, param_info, transform=ax.transAxes,
           fontsize=8, verticalalignment='top', horizontalalignment='right',
           family='monospace',
           bbox=dict(boxstyle='round', facecolor='lightsalmon', alpha=0.9, pad=1))
    
    # Vehicle Status Legend
    status_info = "Vehicle Status Legend:\n"
    status_info += "━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
    status_info += "🟢 HEALTHY: SOC > 50%\n"
    status_info += "🟡 WARNING: 20% < SOC ≤ 50%\n"
    status_info += "🔴 CRITICAL: SOC ≤ 20%"
    
    ax.text(0.98, 0.02, status_info, transform=ax.transAxes,
           fontsize=9, verticalalignment='bottom', horizontalalignment='right',
           family='monospace',
           bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.9, pad=1))
    
    # Add EV symbols legend at bottom left
    ax.text(0.02, 0.02, "EV Color Key:", transform=ax.transAxes,
           fontsize=9, verticalalignment='bottom', fontweight='bold')
    
    y_offset = 0.05
    for ev_id, specs in EV_SPECS.items():
        ax.text(0.02, y_offset, f"█ {ev_id}", transform=ax.transAxes,
               fontsize=10, verticalalignment='bottom',
               color=specs['color'], fontweight='bold')
        y_offset += 0.03
    
    # Add route flow annotation
    route_text = "Primary Route: Marathalli → Whitefield → Silk Board → ETV → (Return)"
    ax.text(0.5, -0.05, route_text, transform=ax.transAxes,
           fontsize=11, ha='center', style='italic', fontweight='bold',
           bbox=dict(boxstyle='round', facecolor='lightcyan', alpha=0.8))
    
    plt.tight_layout()
    
    # Save diagram
    output_dir = Path('output')
    output_dir.mkdir(exist_ok=True)
    
    diagram_path = output_dir / 'SUMO_network_diagram.png'
    plt.savefig(diagram_path, dpi=150, bbox_inches='tight', facecolor='white')
    print(f"✓ Network diagram saved: {diagram_path}")
    
    plt.show()


def create_detailed_junction_diagram():
    """
    Create detailed diagrams of each junction
    """
    fig, axes = plt.subplots(2, 2, figsize=(14, 12), dpi=150)
    fig.suptitle('SUMO Junction Details - Marathalli to ETV Route', fontsize=16, fontweight='bold')
    
    junction_details = [
        {
            'name': 'Marathalli Junction',
            'pos': (0, 0),
            'in_edges': ['whitefield_marathalli'],
            'out_edges': ['marathalli_whitefield'],
            'ax': axes[0, 0]
        },
        {
            'name': 'Whitefield Junction',
            'pos': (5000, 1500),
            'in_edges': ['marathalli_whitefield', 'silk_whitefield'],
            'out_edges': ['whitefield_silk', 'whitefield_marathalli'],
            'ax': axes[0, 1]
        },
        {
            'name': 'Silk Board Junction',
            'pos': (8500, 3200),
            'in_edges': ['whitefield_silk', 'etv_silk'],
            'out_edges': ['silk_etv', 'silk_whitefield'],
            'ax': axes[1, 0]
        },
        {
            'name': 'ETV Junction',
            'pos': (11000, 4500),
            'in_edges': ['silk_etv'],
            'out_edges': ['etv_silk'],
            'ax': axes[1, 1]
        }
    ]
    
    for junction in junction_details:
        ax = junction['ax']
        ax.set_xlim(-500, 1000)
        ax.set_ylim(-500, 1000)
        ax.set_aspect('equal')
        ax.set_facecolor('#F5F5F5')
        ax.grid(True, alpha=0.2)
        
        # Draw junction
        junction_circle = Circle((500, 500), 100, color='#FFD700', ec='black', linewidth=2)
        ax.add_patch(junction_circle)
        ax.text(500, 500, 'J', ha='center', va='center', fontsize=12, fontweight='bold')
        
        # Draw incoming edges
        for i, edge in enumerate(junction['in_edges']):
            angle = i * (2 * np.pi / (len(junction['in_edges']) + len(junction['out_edges'])))
            start_x = 500 + 300 * np.cos(angle + np.pi)
            start_y = 500 + 300 * np.sin(angle + np.pi)
            ax.arrow(start_x, start_y, 150 * np.cos(-angle - np.pi), 150 * np.sin(-angle - np.pi),
                    head_width=30, head_length=20, fc='green', ec='darkgreen', linewidth=2)
            ax.text(start_x - 100, start_y - 100, f"← {edge}", fontsize=8, color='darkgreen')
        
        # Draw outgoing edges
        for i, edge in enumerate(junction['out_edges']):
            angle = (i + len(junction['in_edges'])) * (2 * np.pi / (len(junction['in_edges']) + len(junction['out_edges'])))
            end_x = 500 + 300 * np.cos(angle)
            end_y = 500 + 300 * np.sin(angle)
            ax.arrow(500, 500, 150 * np.cos(angle), 150 * np.sin(angle),
                    head_width=30, head_length=20, fc='blue', ec='darkblue', linewidth=2)
            ax.text(end_x + 50, end_y + 50, f"{edge} →", fontsize=8, color='darkblue')
        
        ax.set_title(junction['name'], fontsize=12, fontweight='bold')
        ax.set_xlabel('X (m)', fontsize=10)
        ax.set_ylabel('Y (m)', fontsize=10)
    
    plt.tight_layout()
    
    # Save junction diagram
    output_dir = Path('output')
    output_dir.mkdir(exist_ok=True)
    
    junction_path = output_dir / 'SUMO_junction_details.png'
    plt.savefig(junction_path, dpi=150, bbox_inches='tight', facecolor='white')
    print(f"✓ Junction diagram saved: {junction_path}")
    
    plt.show()


def create_traffic_flow_diagram():
    """
    Create a diagram showing traffic flows and vehicle routes
    """
    fig, ax = plt.subplots(figsize=(16, 8), dpi=150)
    
    # Set network bounds
    ax.set_xlim(NETWORK_X_MIN, NETWORK_X_MAX)
    ax.set_ylim(NETWORK_Y_MIN, NETWORK_Y_MAX)
    ax.set_aspect('equal')
    ax.set_facecolor('#F5F5F5')
    
    # Title
    ax.set_title("SUMO Traffic Flow and Vehicle Routes - Marathalli to ETV",
                fontsize=16, fontweight='bold', pad=20)
    
    # Draw roads (simplified)
    for edge in EDGES:
        x1, y1 = edge['start']
        x2, y2 = edge['end']
        ax.plot([x1, x2], [y1, y2], color='#666666', linewidth=4, zorder=1)
        
        # Add edge label
        mid_x, mid_y = (x1 + x2) / 2, (y1 + y2) / 2
        ax.text(mid_x + 200, mid_y + 200, f"{edge['name']}\n{edge['speed']} m/s",
               fontsize=9, ha='center', bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.8))
    
    # Draw junctions
    for junction_id, junction_info in JUNCTIONS.items():
        circle = Circle(junction_info['pos'], 200, color='#FFD700', ec='black', linewidth=3)
        ax.add_patch(circle)
        ax.text(junction_info['pos'][0], junction_info['pos'][1],
               junction_info['name'], ha='center', va='center',
               fontsize=10, fontweight='bold')
    
    # Draw vehicle flow routes
    route_points = [
        (0, 0),      # Marathalli
        (5000, 1500),    # Whitefield
        (8500, 3200),    # Silk Board
        (11000, 4500),   # ETV
        (8500, 3200),    # Back to Silk Board
        (5000, 1500),    # Back to Whitefield
        (0, 0)           # Back to Marathalli
    ]
    
    # Draw route as thick colored lines
    for i in range(len(route_points) - 1):
        x1, y1 = route_points[i]
        x2, y2 = route_points[i + 1]
        
        # Forward route in bold
        if i < 3:
            ax.plot([x1, x2], [y1, y2], color='#FF6B6B', linewidth=6, alpha=0.6, zorder=2, label='Forward Route' if i == 0 else '')
        else:
            ax.plot([x1, x2], [y1, y2], color='#4ECDC4', linewidth=6, alpha=0.6, zorder=2, label='Return Route' if i == 3 else '')
    
    # Add distance markers
    total_distance = 0
    distances = [5.18, 3.63, 2.77, 2.77, 3.63, 5.18]  # km per edge
    distance_sum = 0
    for i in range(len(route_points) - 1):
        x1, y1 = route_points[i]
        x2, y2 = route_points[i + 1]
        mid_x, mid_y = (x1 + x2) / 2, (y1 + y2) / 2
        distance_sum += distances[i]
        ax.text(mid_x, mid_y - 300, f"{distances[i]:.2f}km\n({distance_sum:.2f}km total)",
               fontsize=8, ha='center', bbox=dict(boxstyle='round', facecolor='white', alpha=0.9))
    
    # Add grid
    ax.grid(True, alpha=0.2, linestyle=':')
    
    # Axis labels
    ax.set_xlabel('X Coordinate (meters)', fontsize=12, fontweight='bold')
    ax.set_ylabel('Y Coordinate (meters)', fontsize=12, fontweight='bold')
    
    # Legend
    legend_text = "Traffic Flow Information:\n"
    legend_text += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
    legend_text += "● Forward Route (Red): 16.58 km\n"
    legend_text += "● Return Route (Teal): 11.58 km\n"
    legend_text += "● Total Loop: 28.16 km\n"
    legend_text += "\nTraffic Flows:\n"
    legend_text += "• Flow 1: 600 veh/hour\n"
    legend_text += "• Flow 2: 500 veh/hour\n"
    legend_text += "• Flow 3: 400 veh/hour\n"
    legend_text += "• Total: 1500 veh/hour"
    
    ax.text(0.02, 0.98, legend_text, transform=ax.transAxes,
           fontsize=10, verticalalignment='top', family='monospace',
           bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.9, pad=1))
    
    # EV Route Information
    ev_route = "EV Route Configuration:\n"
    ev_route += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
    ev_route += "All 5 EVs follow same route:\n"
    ev_route += "\n1. ev_01: Start 0s, 40 kWh\n"
    ev_route += "2. ev_02: Start 2s, 60 kWh\n"
    ev_route += "3. ev_03: Start 4s, 75 kWh\n"
    ev_route += "4. ev_04: Start 6s, 50 kWh\n"
    ev_route += "5. ev_05: Start 8s, 55 kWh"
    
    ax.text(0.98, 0.98, ev_route, transform=ax.transAxes,
           fontsize=9, verticalalignment='top', horizontalalignment='right',
           family='monospace',
           bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.9, pad=1))
    
    plt.tight_layout()
    
    # Save flow diagram
    output_dir = Path('output')
    output_dir.mkdir(exist_ok=True)
    
    flow_path = output_dir / 'SUMO_traffic_flow_diagram.png'
    plt.savefig(flow_path, dpi=150, bbox_inches='tight', facecolor='white')
    print(f"✓ Traffic flow diagram saved: {flow_path}")
    
    plt.show()


def main():
    """
    Generate all SUMO diagrams
    """
    print("\n" + "="*80)
    print(" SUMO Network Diagram Generator")
    print("="*80 + "\n")
    
    print("Generating SUMO network diagrams...\n")
    
    print("1. Creating main network diagram...")
    create_network_diagram()
    
    print("\n2. Creating detailed junction diagrams...")
    create_detailed_junction_diagram()
    
    print("\n3. Creating traffic flow diagram...")
    create_traffic_flow_diagram()
    
    print("\n" + "="*80)
    print(" All diagrams generated successfully!")
    print("="*80)
    print("\nGenerated files:")
    print("  - output/SUMO_network_diagram.png")
    print("  - output/SUMO_junction_details.png")
    print("  - output/SUMO_traffic_flow_diagram.png")
    print("\n" + "="*80 + "\n")


if __name__ == '__main__':
    main()
