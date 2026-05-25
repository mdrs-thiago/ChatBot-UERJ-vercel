import os
import sys

# Get the path to the root directory
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Add the myapi directory to the python path
sys.path.insert(0, os.path.join(root_dir, 'myapi'))

# Import the WSGI application
from myapi.wsgi import application

# Expose as app for Vercel
app = application
