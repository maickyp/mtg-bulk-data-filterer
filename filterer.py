import sys
import os
import argparse

current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

print(current_dir)

import engine.filter_cli as filter_cli
import gui.app as gui

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="MTG Bulk Data Filter Engine")
    parser.add_argument("--cli", type=str, default=None, help="Path to the bulk data JSON file")
    args = parser.parse_args()

    if args.cli:
        filter_cli.main(args.cli)
    
    else:
        gui.main()
    

    