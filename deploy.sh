#!/bin/bash

set -e

echo "Starting deployment process..."

echo "Step 1: Running modify-core.sh"
./modify-core.sh

echo "Step 2: Running start.sh"
./start.sh

echo "Step 3: Running start_save_app.sh"
./start_save_app.sh

echo "Step 4: Committing and pushing to master"
git add .
git commit -m "Automated deployment - $(date)"
git push origin master

echo "Deployment completed successfully!"