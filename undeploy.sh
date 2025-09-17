#!/bin/bash

set -e

echo "Starting undeploy process..."

echo "Step 1: Running stop.sh"
./stop.sh

echo "Step 2: Running stop_save_app.sh"
./stop_save_app.sh

echo "Undeploy completed successfully!"