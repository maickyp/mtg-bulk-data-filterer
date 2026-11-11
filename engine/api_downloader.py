import requests
import json
import consts as CONSTS

SCRYFALL_BULK_DATA_URL = "https://api.scryfall.com/bulk-data"
SCRYFALL_SETS_URL = "https://api.scryfall.com/sets"

def download_from_api(url):
    """Downloads data from the given URL and returns it as a JSON object."""

    headers = {
        "user-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json"
        }


    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()

def write_file(data, file_path, list=False):
    """Writes the given data to a file in JSON format."""
    breakpoint()  # Debugging breakpoint to inspect the URL and headers
    with open(file_path, "w", encoding="utf-8") as f:
        if list:
            f.write("[\n")
            for index, card in enumerate(data):
                separator = "," if index < len(data) - 1 else ""
                f.write(json.dumps(card, ensure_ascii=False) + separator + "\n")
            f.write("]")
        else:
            json.dump(data, f, ensure_ascii=False, indent=2)

def download_bulk_data(bulk_data_type="oracle_cards"):
        """Downloads the bulk data from Scryfall and saves it to a local file."""

        print(f"Downloading bulk data from Scryfall for type '{bulk_data_type}'...")
        
        # Get the whole bulk data dictionary pointers from Scryfall
        bulk_data_info = download_from_api(SCRYFALL_BULK_DATA_URL)

        # Find the default card data
        card_data_info = next((data for data in bulk_data_info["data"] if data["type"] == bulk_data_type), None)
        if not card_data_info:
            raise ValueError(f"{bulk_data_type} not found in Scryfall bulk data.")

        # Download the actual card data
        card_data_url = card_data_info["download_uri"]
        cards_data = download_from_api(card_data_url)

        # Save to a local file
        output_file = CONSTS.BULK_CARD_DATA_FILE
        write_file(cards_data, output_file, list=True)

        print(f"Downloaded and saved bulk data to {output_file}")

def download_expansions_data():
    """Downloads the expansions data from Scryfall and saves it to a local file."""

    print("Downloading expansions data from Scryfall...")

    sets = download_from_api(SCRYFALL_SETS_URL)["data"]
    write_file(sets, CONSTS.EXPANSIONS_FILE)
