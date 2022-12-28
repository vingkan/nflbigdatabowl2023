#!/bin/bash

# Tells the script to exit if a command fails instead of continuing
set -e

install_python_requirements () {
    # Create and activate Python virtual environment
    python3 -m venv .venv
    source .venv/bin/activate
    # Install Python dependencies
    pip3 install -r requirements-dev.txt
    pip3 install -r requirements.txt
}

download_kaggle_data () {
    # Create necessary folders, if they do not exist
    mkdir -p data/zipped
    mkdir -p data/raw
    # Refresh GitPod workspace environment variables
    eval $(gp env -e)
    # Download data using Kaggle credentials from user environment variables
    kaggle competitions download -c nfl-big-data-bowl-2023 -p data/zipped
    # Unzip raw data
    unzip data/zipped/nfl-big-data-bowl-2023.zip -d data/raw
    # Delete zipped data
    rm -rf data/zipped
}

# Run commands based on chosen shortcut and options
if [ "$1" == "install-project" ]; then
    # Install Python requirements
    install_python_requirements
    # Download Kaggle data
    download_kaggle_data

elif [ "$1" == "install-python-requirements" ]; then
    # Install Python requirements
    install_python_requirements

else
    echo "No run shortcut found for: '$1'"
fi
