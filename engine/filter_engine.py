from collections import namedtuple
import json
import os
import re
import requests

import consts as CONSTS
import engine.api_downloader as api_downloader

REMOVAL_PATTERNS = [r"destroy", r"deals \d+ damage to", r"sacrifice", r"return to hand", r"exile", r"-\d+/-\d+", r"-x/-x", r"fight", r"tap target creature"]
CARD_ADVANTAGE_PATTERNS = [r"draw", r"mill", r"exile top", r"look at the top", r"return target card from your graveyard", r"search", r"reveal", r"discard", r"sacrifices"]
MANA_RAMP_PATTERNS = [r"add \{", r"search your library for a land", r"mana value", r"landcycling", r"swampcycling", r"forestcycling", r"mountaincycling", r"islandcycling", r"plainscycling"]
PROTECTION_PATTERNS = [r"indestructible", r"hexproof", r"ward", r"counter target", r"prevent all damage", r"shroud", r"protection", r"regenerate"]
COMBAT_PATTERNS = [r"flying", r"trample", r"haste", r"first strike", r"double strike", r"vigilance", r"deathtouch"]
TOKEN_GENERATION_PATTERNS = [r"token", r"create a token", r"populate", r"emblem", r"amass", r"create a copy of", r"copy target", r"token creature", r"create a", r"put a +1/+1 counter", r"enters with"]
PLANESWALKER_PATTERNS = [r"planeswalker", r"loyalty", r"loyalty counters", r"loyalty ability"]
COUNTERSPELLS_PATTERNS = [r"counter target spell", r"counter target ability", r"counter target activated ability", r"counter target triggered ability"]
STAX_PATTERNS = [r"can't cast", r"tax", r"tapped", r"defender", r"skip", r"can't attack", r"can't block", r"can't be blocked", r"can't be regenerated"]
RECURSION_PATTERNS = [r"return target", r"graveyard", r"reanimate", r"from your graveyard to the battlefield"]
LIFE_GAIN_LOSS_PATTERNS = [r"gain \d+ life", r"gain that life", r"lose \d+ life", r"life total", r"lifelink"]

DECK_LIST_CARD_PATTERN = r"\d+\s+(.+)"
BASIC_LANDS = ["Plains", "Island", "Swamp", "Mountain", "Forest"]



class FilterEngine:
    def __init__(self, bulk_data_file=None):

        if bulk_data_file is None or not os.path.exists(bulk_data_file):
            print("Bulk data file not found. Downloading from Scryfall...")
            api_downloader.download_bulk_data()
            self.bulk_data_file = CONSTS.BULK_CARD_DATA_FILE

        self.bulk_data_file = bulk_data_file
        self._open_file(bulk_data_file)

        self.sets = None
        if not os.path.exists(CONSTS.EXPANSIONS_FILE):
            self.get_expansions_available()

        self.sets = json.load(open(CONSTS.EXPANSIONS_FILE, "r", encoding="utf-8"))

        self.condition_keys = {}
        self.keep_keys = []

        # List to keep the filtered cards
        self.commander = []
        self.draft = []


        # Options for filtering

        # If True, the cards will be segregated into commander and draft based on rarity.
        self.draft_segregation = False

        # For splitting the output into multiple files
        self.split_output = False
        self.chunk_size = 50



    def _open_file(self, file_path):
        """Opens a JSON file and loads its content as a list of dictionaries."""
        print(f"Reading {file_path}...")
        with open(file_path, "r", encoding="utf-8") as f:
            self.cards_data  = json.load(f)
        if not isinstance(self.cards_data, list):
            raise ValueError(
                "Input JSON file must contain a list of items."
            )
        print("Loaded...")

    def update_condition_keys(self, new_condition_keys: dict):
        """Updates the condition keys for filtering."""
        self.condition_keys = new_condition_keys

    def update_keep_keys(self, new_keep_keys: list):
        """Updates the keys to keep in the filtered items."""
        self.keep_keys = new_keep_keys

    def check_condition_keys(self, item):
        compliant = True
        for llave, valor_esperado in self.condition_keys.items():
            if item.get(llave) != valor_esperado:
                compliant = False
                break
        return compliant

    def filter_cards(self, card_sets):
        """Filters the cards based on the condition keys and card sets."""
        if self.draft_segregation:
            commander, draft = self._filter_cards_with_draft(card_sets)
            self.commander = commander
            self.draft = draft
            print(f"Filtered cards: {len(commander)} commander, {len(draft)} draft.")
            return

        commander = self._filter_cards(card_sets)
        self.commander = commander
        self.draft = []
        print(f"Filtered cards: {len(commander)} commander.")

    def _filter_cards(self, card_sets):
        """Filters cards without draft segregation."""
        filtered_cards = []
        added_cards = set()  # To avoid duplicates
        for item in self.cards_data:
            if not self.valid_card(item, card_sets):
                continue

            if not self.check_condition_keys(item):
                continue

            card_name = item.get("name")
            if card_name in added_cards:
                continue

            if len(self.keep_keys) > 0:
                filtered_item = {key: item[key] for key in self.keep_keys if key in item}
            else:
                filtered_item = item

            classified_tags = self.classify_card(filtered_item)
            filtered_item["tags"] = classified_tags

            filtered_cards.append(filtered_item)

        return filtered_cards

    def _filter_cards_with_draft(self, card_sets):
        """Filters cards with draft segregation."""
        commander = []
        draft = []
        added_cards = set()  # To avoid duplicates

        for item in self.cards_data:
            if not self.valid_card(item, card_sets):
                continue

            if not self.check_condition_keys(item):
                continue

            card_name = item.get("name")
            if card_name in added_cards:
                continue

            if len(self.keep_keys) > 0:
                filtered_item = {key: item[key] for key in self.keep_keys if key in item}
            else:
                filtered_item = item

            classified_tags = self.classify_card(filtered_item)
            filtered_item["tags"] = classified_tags

            if filtered_item.get("rarity") == "common":
                draft.append(filtered_item)
            else:
                commander.append(filtered_item)

            added_cards.add(card_name)

        return commander, draft

    def write_to_file(self, base_name):
        """Writes the filtered cards to files."""
        func_name = self._write_chunked_json if self.split_output else self._write_json

        if self.draft_segregation:
            func_name(f"{base_name}_commander", self.commander)
            func_name(f"{base_name}_draft", self.draft)
        else:
            func_name(base_name, self.commander)

    def _write_json(self, file_name, items):
        """Writes a list of items to a JSON file."""
        with open(file_name, "w", encoding="utf-8") as f:
            json.dump(items, f, ensure_ascii=False, indent=2)
        print(f"Saved {len(items)} items to {file_name}")

    def _write_chunked_json(self, base_name, items):
        """Writes a list of items to multiple JSON files with a maximum number of items per file."""
        if not items:
            print(f"No items to write for {base_name}.")
            return

        for index in range(0, len(items), self.chunk_size):
            chunk = items[index : index + self.chunk_size]
            part = index // self.chunk_size + 1
            suffix = "" if part == 1 else f"_part{part}"
            file_name = f"{base_name}{suffix}.txt"
            with open(file_name, "w", encoding="utf-8") as f:
                json.dump(chunk, f, ensure_ascii=False, indent=2)
            print(f"Saved {len(chunk)} items to {file_name}")

    def valid_card(self, item, card_sets=None):
        """Check if a card is valid for Commander based on specific criteria.

        :param item: A dictionary representing a MTG card.
        :param card_sets: A list of sets that are to be filtered. If a card's set is not in this list, it will be considered invalid.
        :return: True if the card is valid for Commander, False otherwise.
        """
        if item.get("reprint") is True:
            return False

        if item.get("variation") is True:
            return False

        if "paper" not in item.get("games", []):
            return False

        if item.get("legalities", {}).get("commander") != "legal":
            return False

        if card_sets is not None and item.get("set") not in card_sets:
            return False

        return True

    def classify_card(self, card):
        """
        Classifies a card based on its oracle text and returns a list of tags.
        :param card: A dictionary representing a MTG card.
        :return: A list of tags that describe the card's functionality.
        """
        tags = []
        text = card.get("oracle_text", "").lower()

        if any(re.search(pattern, text) for pattern in REMOVAL_PATTERNS):
            tags.append("Removal")
        if any(word in text for word in CARD_ADVANTAGE_PATTERNS):
            tags.append("Card Advantage")
        if any(word in text for word in MANA_RAMP_PATTERNS):
            tags.append("Mana Ramp")
        if any(word in text for word in PROTECTION_PATTERNS):
            tags.append("Protection")
        if any(word in text for word in COMBAT_PATTERNS):
            tags.append("Combat")
        if any(word in text for word in TOKEN_GENERATION_PATTERNS):
            tags.append("Token Generation")
        if any(word in text for word in PLANESWALKER_PATTERNS):
            tags.append("Planeswalker")
        if any(word in text for word in COUNTERSPELLS_PATTERNS):
            tags.append("Counterspells")
        if any(word in text for word in STAX_PATTERNS):
            tags.append("Stax")
        if any(word in text for word in RECURSION_PATTERNS):
            tags.append("Recursion")
        if any(word in text for word in LIFE_GAIN_LOSS_PATTERNS):
            tags.append("Life Gain/Loss")

        return tags

    def get_expansions_available(self):
        """Returns a list of unique set names from the cards data."""
        if self.sets is not None:
            return

        api_downloader.download_expansions_data()


    def get_detailed_deck_list(self, deck_list_file):
        """Reads a deck list from a file and searchs for the cards in the whole bulk data,
        appending at the end of the file the detailed information of each card found in the bulk data
        in the same way as the filtered cards, including the tags generated by the classify_card method.
        """
        with open(deck_list_file, "r", encoding="utf-8") as f:
            deck_list = f.read().splitlines()

        detailed_deck_list = []
        

        for card_bulk in self.cards_data:
            for card_list in deck_list:
                card_name = re.search(DECK_LIST_CARD_PATTERN, card_list, re.IGNORECASE)
                card_found = card_name.group(1).lower() == card_bulk.get("name").lower() if card_name else False
                if not card_found or card_name.group(1) in BASIC_LANDS:
                    continue

                filtered_item = {key: card_bulk[key] for key in self.keep_keys if key in card_bulk}
                classified_tags = self.classify_card(filtered_item)
                filtered_item["tags"] = classified_tags
                detailed_deck_list.append(filtered_item)
                card_found = True
                break

        with open(deck_list_file, "a", encoding="utf-8") as f:
            f.write("\n\n==============================\n\nDetailed Deck Info:\n")
            json.dump(detailed_deck_list, f, ensure_ascii=False, indent=2)

    


if __name__ == "__main__":

    INPUT_FILE = "cards_bulk.json"
    filterer = card_filter(INPUT_FILE)

    condition_keys= {
    }

    keep_keys = ["name",
                 "mana_cost",
                 "cmc",
                 "type_line",
                 "oracle_text",
                 "color_identity",
                 "keywords",
                 "set_name",
                 "rarity",
                 "power",
                 "toughness",
                 "loyalty",
                 "produced_mana",
                 "card_faces",
                 "type_line"]

    filterer.update_condition_keys(condition_keys)
    filterer.update_keep_keys(keep_keys)

    # set_name = "ecl"
    # OUTPUT_FILE = f"set_{set_name}.txt"  # Archivo de salida
    # card_sets= [f"{set_name}", "ecc"]
    # filterer.filter_cards(card_sets)
    # filterer.write_to_file(OUTPUT_FILE)

    # set_name = "tla"
    # OUTPUT_FILE = f"set_{set_name}.txt"  # Archivo de salida
    # card_sets= [f"{set_name}", "tlc"]
    # filterer.filter_cards(card_sets)
    # filterer.write_to_file(OUTPUT_FILE)

    # set_name = "tmt"
    # OUTPUT_FILE = f"set_{set_name}.txt"  # Archivo de salida
    # card_sets= [f"{set_name}", "tmc"]
    # filterer.filter_cards(card_sets)
    # filterer.write_to_file(OUTPUT_FILE)

    # sets = filterer.get_expansions_available()
    # print(len(sets))
    # for set in sets:
    #     print(f"{set.code}: {set.name}")

    # Ejemplo de uso de get_detailed_deck_list
    deck_list_file = "Deck_Zuko_v2.txt"  # Archivo de lista de mazo
    filterer.get_detailed_deck_list(deck_list_file)
