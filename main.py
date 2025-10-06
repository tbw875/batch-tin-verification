#!/usr/bin/env python3
"""
Simple Python script with hello world example.
"""

import os
from dotenv import load_dotenv


def hello_world():
    """Print a hello world message."""
    print("Hello, World!")
    print("This is a simple Python script.")


def main():
    """Main function to run the script."""
    # Load environment variables from .env file
    load_dotenv()
    
    # Get environment variable (if set)
    name = os.getenv('NAME', 'World')
    print(f"Hello, {name}!")
    
    # Call the hello world function
    hello_world()
    
    # Print some environment info
    print(f"Python version: {os.sys.version}")
    print(f"Current working directory: {os.getcwd()}")


if __name__ == "__main__":
    main()
