import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
BULK_CARD_DATA_FILE = os.path.join(DATA_DIR, "bulk_data.json")
EXPANSIONS_FILE = os.path.join(DATA_DIR, "expansions.json")