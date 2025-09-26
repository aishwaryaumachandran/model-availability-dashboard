"""
Runner script for the Azure AI Model Capacity Dashboard
"""

import subprocess
import sys
import os

def check_dependencies():
    """Check if required packages are installed."""
    try:
        import streamlit
        import pandas
        import plotly
        return True
    except ImportError as e:
        print(f"Missing dependencies: {e}")
        print("Please install required packages:")
        print("pip install -r requirements.txt")
        return False

def run_streamlit_app():
    """Launch the Streamlit application."""
    if not check_dependencies():
        return
    
    # Change to the script directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    
    print("🚀 Starting Azure AI Model Capacity Dashboard...")
    print("📊 The dashboard will open in your default web browser")
    print("🔗 URL: http://localhost:8501")
    print("⏹️  Press Ctrl+C to stop the server")
    print("-" * 50)
    
    try:
        # Run Streamlit app from portal folder
        portal_app = os.path.join("portal", "app.py")
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", portal_app,
            "--server.port=8501",
            "--server.address=localhost",
            "--browser.gatherUsageStats=false"
        ])
    except KeyboardInterrupt:
        print("\n✅ Dashboard stopped successfully")
    except Exception as e:
        print(f"❌ Error running dashboard: {e}")

if __name__ == "__main__":
    run_streamlit_app()