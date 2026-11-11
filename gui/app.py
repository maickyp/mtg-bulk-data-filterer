
import customtkinter as ctk
import gui.deck_list as deck_list
import gui.card_filter as filterer
from engine.filter_engine import FilterEngine
import consts as CONSTS

class MTG_App(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.data_loaded = False
        self.title("MTG Filter App")
        self.geometry("400x400")
        self.grid_columnconfigure((0, 1), weight=1)
        self.buttons= []
        self.filter_engine = None

        self.load_bulk_data_button = ctk.CTkButton(self, text="Load Card Database", command=self.load_data_base)
        self.load_bulk_data_button.grid(row=0, column=0, padx=20, pady=20, sticky="ew", columnspan=2)
        self.filterer_chooser = ctk.CTkButton(self, text="Get Deck list data", command=self.open_deck_list_window, state="disabled")
        self.filterer_chooser.grid(row=1, column=0, padx=20, pady=20, sticky="ew", columnspan=2)
        self.buttons.append(self.filterer_chooser)

        self.card_params_button = ctk.CTkButton(self, text="Filterer", command=self.open_filterer_window, state="disabled")
        self.card_params_button.grid(row=3, column=0, padx=20, pady=20, sticky="ew", columnspan=2)
        self.buttons.append(self.card_params_button)

        self.close_app_button = ctk.CTkButton(self, text="Close App", command=self.destroy)
        self.close_app_button.grid(row=4, column=0, padx=20, pady=20, sticky="ew", columnspan=2)

    def load_data_base(self):
        self.filter_engine = FilterEngine(CONSTS.BULK_CARD_DATA_FILE)  # Initialize the filter engine
        for button in self.buttons:
            button.configure(state="normal")
    
    def open_deck_list_window(self):
        deck_list.DeckListWindow(self, filter_engine=self.filter_engine)
    
    def open_filterer_window(self):
        filterer.CardParamsWindow(self, filter_engine=self.filter_engine)

def main():
    app = MTG_App()
    app.mainloop()
