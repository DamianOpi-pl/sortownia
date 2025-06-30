#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}==== Clothing Sorting System Setup ====${NC}"
echo "This script will set up the application for first use."

# Create and activate virtual environment
echo -e "\n${YELLOW}Creating virtual environment...${NC}"
python3 -m venv venv
if [ $? -ne 0 ]; then
    echo -e "${RED}Failed to create virtual environment. Please make sure python3-venv is installed.${NC}"
    exit 1
fi

# Activate virtual environment
echo -e "\n${YELLOW}Activating virtual environment...${NC}"
source venv/bin/activate
if [ $? -ne 0 ]; then
    echo -e "${RED}Failed to activate virtual environment.${NC}"
    exit 1
fi

# Install dependencies
echo -e "\n${YELLOW}Installing dependencies...${NC}"
pip install -r requirements.txt
if [ $? -ne 0 ]; then
    echo -e "${RED}Failed to install dependencies.${NC}"
    exit 1
fi

# Run migrations
echo -e "\n${YELLOW}Setting up database...${NC}"
python manage.py makemigrations
python manage.py migrate
if [ $? -ne 0 ]; then
    echo -e "${RED}Failed to set up database.${NC}"
    exit 1
fi



# Create a superuser
echo -e "\n${YELLOW}Would you like to create a superuser account? (y/n)${NC}"
read create_superuser

if [ "$create_superuser" = "y" ] || [ "$create_superuser" = "Y" ]; then
    python manage.py createsuperuser
fi

# Collect static files
echo -e "\n${YELLOW}Collecting static files...${NC}"
python manage.py collectstatic --noinput
if [ $? -ne 0 ]; then
    echo -e "${RED}Failed to collect static files.${NC}"
    exit 1
fi

echo -e "\n${GREEN}==== Setup complete! ====${NC}"
echo -e "You can now run the application with: ${YELLOW}python manage.py runserver${NC}"
echo -e "Then access it at: ${YELLOW}http://127.0.0.1:8000/${NC}"
echo -e "Admin interface is available at: ${YELLOW}http://127.0.0.1:8000/admin/${NC}"
echo -e "\n${GREEN}Remember to activate the virtual environment with:${NC}"
echo -e "${YELLOW}source venv/bin/activate${NC}"
echo -e "${GREEN}when you want to run the application in the future.${NC}"
