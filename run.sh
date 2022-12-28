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

install_pre_commit () {
    # Activate Python virtual environment
    source .venv/bin/activate
    # Install pre-commit hooks
    pre-commit install --install-hooks
}

download_kaggle_data () {
    # Activate Python virtual environment
    source .venv/bin/activate
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

start_jupyter_server () {
    # Activate Python virtual environment
    source .venv/bin/activate
    # Get GitPod custom domain to allow requests to Jupyter server
    JUPYTER_PORT=8888
    GITPOD_DOMAIN=$(gp url "$JUPYTER_PORT")
    # Start Jupyter server
    jupyter notebook --port="$JUPYTER_PORT" --NotebookApp.allow_origin="$GITPOD_DOMAIN"
}

# Run commands based on chosen shortcut and options

# Install main project dependencies needed for immediate development
if [ "$1" == "install-project" ]; then
    # Install Python requirements
    install_python_requirements

# Install dependencies in the background that will be used later
elif [ "$1" == "install-background" ]; then
    # Download Kaggle data
    download_kaggle_data
    # Install pre-commit
    install_pre_commit

# Install only Python requirements
elif [ "$1" == "install-python-requirements" ]; then
    install_python_requirements

# Run Jupyter notebook server
elif [ "$1" == "jupyter" ]; then
    start_jupyter_server

else
    echo "No run shortcut found for: '$1'"
fi
