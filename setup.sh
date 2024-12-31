#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to check Python version
check_python_version() {
    if command_exists python3; then
        python3 --version | awk '{print $2}' | cut -d. -f1,2
    else
        echo "0"
    fi
}

echo -e "${GREEN}Checking and installing required tools...${NC}"

# Update package list
echo -e "${YELLOW}Updating package list...${NC}"
sudo apt-get update

# Check and install Python 3
PYTHON_VERSION=$(check_python_version)
if [ "$PYTHON_VERSION" \< "3.8" ]; then
    echo -e "${YELLOW}Installing Python 3.8 or higher...${NC}"
    sudo apt-get install -y python3
else
    echo -e "${GREEN}✓ Python $PYTHON_VERSION is already installed${NC}"
fi

# Check and install pip
if ! command_exists pip3; then
    echo -e "${YELLOW}Installing pip3...${NC}"
    sudo apt-get install -y python3-pip
else
    echo -e "${GREEN}✓ pip3 is already installed${NC}"
fi

# Check and install python3-venv
if ! dpkg -l | grep -q python3-venv; then
    echo -e "${YELLOW}Installing python3-venv...${NC}"
    sudo apt-get install -y python3-venv
else
    echo -e "${GREEN}✓ python3-venv is already installed${NC}"
fi

# Check and install git
if ! command_exists git; then
    echo -e "${YELLOW}Installing git...${NC}"
    sudo apt-get install -y git
else
    echo -e "${GREEN}✓ git is already installed${NC}"
fi

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}Creating virtual environment...${NC}"
    python3 -m venv venv
else
    echo -e "${GREEN}✓ Virtual environment already exists${NC}"
fi

# Activate virtual environment
echo -e "${YELLOW}Activating virtual environment...${NC}"
source venv/bin/activate

# Install or upgrade requirements
echo -e "${YELLOW}Installing/upgrading Python dependencies...${NC}"
pip install --upgrade pip
pip install -r requirements.txt

# Install the package
echo -e "${YELLOW}Installing docker-mgmt package...${NC}"
pip install .

# Make script executable if it isn't already
if [ ! -x "docker-mgmt" ]; then
    echo -e "${YELLOW}Making docker-mgmt executable...${NC}"
    chmod +x docker-mgmt
else
    echo -e "${GREEN}✓ docker-mgmt is already executable${NC}"
fi

echo -e "\n${GREEN}Setup completed successfully!${NC}"
echo -e "\n${YELLOW}To start using the tool:${NC}"
echo -e "1. Activate the virtual environment: ${GREEN}source venv/bin/activate${NC}"
echo -e "2. Run the tool: ${GREEN}./docker-mgmt --interactive${NC}"
echo -e "   or: ${GREEN}python -m docker_mgmt --interactive${NC}"

# Check if we're in a virtual environment
if [ -z "$VIRTUAL_ENV" ]; then
    echo -e "\n${YELLOW}Note: The virtual environment is not currently activated.${NC}"
    echo -e "Run ${GREEN}source venv/bin/activate${NC} to activate it."
fi 