#!/usr/bin/env bash
set -e

pushd "$(dirname "$0")/../modules/lambda/code"
zip -r ../lambda_package.zip lambda_function.py requirements.txt
popd