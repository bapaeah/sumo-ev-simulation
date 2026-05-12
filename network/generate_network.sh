#!/bin/bash
# Script to generate SUMO network from node and edge files

if [ -z "$SUMO_HOME" ]; then
    echo "Error: SUMO_HOME is not set"
    echo "Please set SUMO_HOME environment variable pointing to your SUMO installation"
    exit 1
fi

echo "Generating SUMO network..."
cd "$(dirname "$0")"

# Run netconvert to generate the network file
$SUMO_HOME/bin/netconvert -c generate_network.netcfg --no-turnarounds

if [ $? -eq 0 ]; then
    echo "Network generated successfully: marathalli_etv.net.xml"
else
    echo "Error generating network"
    exit 1
fi
