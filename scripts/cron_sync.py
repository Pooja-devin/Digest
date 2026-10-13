import sys
import os

# Project root directory-ah python path-la add panrom
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import init_db
from app.scraper import sync_feeds

def run_cron():
    print("[CRON] Initializing database...")
    init_db()
    
    print("[CRON] Fetching live feeds & extracting opportunities...")
    new_count = sync_feeds()
    
    print(f"[CRON] Completed successfully. {new_count} new opportunities added.")

if __name__ == "__main__":
    run_cron()