#!/usr/bin/env python3
"""
Sora 2 Web App Launcher
=======================

Convenience script to launch the Sora 2 web interface from the project root.

This proxy script simply imports and runs the Flask application from src/app/web_app.py,
allowing you to start the web server without navigating to the src/app directory.

Usage:
    python run_web_app.py

The web interface will be available at:
    http://localhost:5000

Press Ctrl+C to stop the server.
"""

import sys
import os

# Add src/app to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src', 'app'))

# Import and run the Flask app
if __name__ == '__main__':
    # Import the app module
    from web_app import app, VIDEOS_DIR, TEMP_DIR, PROJECT_ROOT
    
    # Ensure directories exist
    os.makedirs(VIDEOS_DIR, exist_ok=True)
    os.makedirs(TEMP_DIR, exist_ok=True)
    
    print("=" * 60)
    print("Sora 2 API Web Interface")
    print("=" * 60)
    print(f"\nProject root: {PROJECT_ROOT}")
    print(f"Videos directory: {VIDEOS_DIR}")
    print("\nStarting server at http://localhost:5000")
    print("Press Ctrl+C to stop\n")
    print("=" * 60)
    
    # Run the Flask app
    app.run(debug=True, host='0.0.0.0', port=5000)
