import os
import sys
import time

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

log_dir = 'logs'
max_age_days = 30
for file in os.listdir(log_dir):
    file_path = os.path.join(log_dir, file)
    if os.path.isfile(file_path) and time.time() - os.path.getmtime(file_path) > max_age_days * 86400:
        os.remove(file_path)
        print(f"Deleted old log: {file_path}")