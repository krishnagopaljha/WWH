#!/bin/bash

# Check if requirements.txt exists
if [[ ! -f requirements.txt ]]; then
    echo "Error: requirements.txt not found!"
    exit 1
fi

# Install requirements from requirements.txt
echo "Installing dependencies from requirements.txt..."
pip install -r requirements.txt

# Check if wwh.py exists
if [[ ! -f wwh.py ]]; then
    echo "Error: wwh.py not found!"
    exit 1
fi

# Move wwh.py to /usr/bin/wwh
echo "Moving wwh.py to /usr/bin/wwh..."
sudo cp wwh.py /usr/bin/wwh

# Make wwh executable
sudo chmod +x /usr/bin/wwh

# Provide user with instructions
echo "Installation complete!"
echo "You can now run the script directly by typing 'wwh' from any directory in your terminal."
echo "Usage: wwh <URL> [options]"

