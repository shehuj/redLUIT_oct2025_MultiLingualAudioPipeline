#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/../lambda_src"
rm -rf build
mkdir build
pip install --upgrade pip
pip install -r requirements.txt -t build/
cp handler.py build/
cd build
zip -r ../deploy.zip .
cd ..
echo "Created deploy.zip in lambda_src/"