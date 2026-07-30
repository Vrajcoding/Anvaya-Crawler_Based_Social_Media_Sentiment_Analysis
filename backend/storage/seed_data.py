import os
import json
import uuid
from datetime import datetime, timedelta
from storage.db_client import db

def initialize_seed_data():
    """Populate initial seed data into DB only if store is empty."""
    if len(db.posts) > 0:
        print(f"[OK] Database loaded {len(db.posts)} real crawled posts from disk.")
        return

    print("[OK] Initializing real live data store.")
