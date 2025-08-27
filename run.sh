#!/bin/bash
echo "Starting Email Automation System (without Docker)"
echo "================================================"

# Activate virtual environment
source .venv/Scripts/activate

# Check if .env file exists
if [ ! -f .env ]; then
    echo "ERROR: .env file not found!"
    echo "Please make sure .env file exists with your configuration."
    exit 1
fi

# Function to show menu
show_menu() {
    echo ""
    echo "Available commands:"
    echo ""
    echo "1. run-dispatcher        - Run the main dispatcher once"
    echo "2. run-continuous        - Run dispatcher continuously"  
    echo "3. check-runtime-states  - Check account runtime states"
    echo "4. fix-runtime-states    - Fix problematic runtime states"
    echo "5. list-campaigns        - List all campaigns"
    echo "6. list-leads            - List campaign leads"
    echo "7. exit                  - Exit"
    echo ""
}

# Main menu loop
while true; do
    show_menu
    read -p "Enter your choice (1-7): " choice
    
    case $choice in
        1)
            echo "Running dispatcher once..."
            python -m app.cli.main run-dispatcher --verbose
            ;;
        2)
            echo "Running dispatcher continuously..."
            echo "Press Ctrl+C to stop"
            python -m app.cli.main run-continuous
            ;;
        3)
            echo "Checking runtime states..."
            python -m app.cli.main check-runtime-states
            ;;
        4)
            echo "Fixing runtime states..."
            python -m app.cli.main fix-runtime-states
            ;;
        5)
            echo "Listing campaigns..."
            python -m app.cli.main list-campaigns
            ;;
        6)
            echo "Listing leads..."
            python -m app.cli.main list-leads
            ;;
        7)
            echo "Goodbye!"
            exit 0
            ;;
        *)
            echo "Invalid choice. Please try again."
            ;;
    esac
done
