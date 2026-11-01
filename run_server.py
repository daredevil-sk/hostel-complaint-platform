"""
Run script for the FastAPI + React Hostel Grievance Platform.
Usage:
    python run_server.py
"""

import uvicorn
import os
import sys

if __name__ == "__main__":
    # Ensure current directory is in path
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    print("=" * 60)
    print("Hostel Grievance Platform (FastAPI + React)")
    print("Server running at: http://localhost:8000")
    print("Swagger API docs at: http://localhost:8000/docs")
    print("=" * 60)
    uvicorn.run("backend.app:app", host="127.0.0.1", port=8000, reload=True)
