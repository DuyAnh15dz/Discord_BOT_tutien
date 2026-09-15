import os
from dotenv import load_dotenv

load_dotenv()

# ===== Discord =====
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')

# ===== Admin =====
_admin_ids_str = os.getenv('ADMIN_IDS', '')
ADMIN_IDS = [
    int(x.strip()) for x in _admin_ids_str.split(',') if x.strip()
]

# ===== Database =====
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': int(os.getenv('DB_PORT', 3306)),
    'database': os.getenv('DB_NAME', 'tu_tien_db'),
    'user': os.getenv('DB_USER', 'bot_user'),
    'password': os.getenv('DB_PASSWORD'),
    'charset': 'utf8mb4',
    'collation': 'utf8mb4_unicode_ci',
    'autocommit': False,
}