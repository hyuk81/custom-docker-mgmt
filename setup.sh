#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}Installing Python and required tools...${NC}"

# Update package list
echo -e "${YELLOW}Updating package list...${NC}"
sudo apt-get update

# Install Python 3 and pip
echo -e "${YELLOW}Installing Python 3 and pip...${NC}"
sudo apt-get install -y python3 python3-pip python3-venv

# Install git if not installed
echo -e "${YELLOW}Installing git...${NC}"
sudo apt-get install -y git

# Create virtual environment
echo -e "${YELLOW}Creating virtual environment...${NC}"
python3 -m venv venv

# Activate virtual environment
echo -e "${YELLOW}Activating virtual environment...${NC}"
source venv/bin/activate

# Install requirements
echo -e "${YELLOW}Installing Python dependencies...${NC}"
pip install -r requirements.txt

# Make script executable
echo -e "${YELLOW}Making docker_manager.py executable...${NC}"
chmod +x docker_manager.py

echo -e "${GREEN}Setup completed successfully!${NC}"
echo -e "${YELLOW}To start using the tool:${NC}"
echo -e "1. Activate the virtual environment: ${GREEN}source venv/bin/activate${NC}"
echo -e "2. Run the tool: ${GREEN}./docker_manager.py --interactive${NC}" 