import os
import sys

# Ensure project root directory is accessible on Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app

# Vercel WSGI entry point
app = create_app()

if __name__ == '__main__':
    app.run()
