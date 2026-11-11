import os

import customtkinter as ctk
import json
import consts as CONSTS
import copy
import gui.consts as GUI_CONSTS

class ConfigFrame(ctk.CTkScrollableFrame):
    def __init__(self, master, values={}, label="Configuration"):
        super().__init__(master)
        self.checkboxes = {}
        self.values = values

        self.label = ctk.CTkLabel(self, text=label)
        self.label.grid(row=0, column=0, padx=20, pady=(0, 0))

        for display_text, key in self.values.items():
            checkbox = ctk.CTkCheckBox(self, text=display_text, state="normal")
            checkbox.grid(row=len(self.grid_slaves()), column=0, padx=20, pady=(0, 10), sticky="w")
            self.checkboxes[key] = checkbox

    def get(self):
        return {f"{key}": checkbox.get() for key, checkbox in self.checkboxes.items()}

class CardParamsWindow(ctk.CTkToplevel):
    def __init__(self, master, filter_engine):
        super().__init__(master)
        self.filter_engine = filter_engine
        self.title("Filtered Data")
        self.geometry("800x600")
        self.grid_columnconfigure((0, 1), weight=1)


        sets = {}
        for game_set in filter_engine.sets:
            if "Tokens" in game_set["name"] or "Art" in game_set["name"]:
                continue
            sets[game_set["name"]] = game_set["code"]


        self.config_frame = ConfigFrame(self, values=GUI_CONSTS.KEEP_KEYS, label="Select Keys to Keep")
        self.config_frame.grid(row=0, column=0, padx=20, pady=20)

        self.set_frame = ConfigFrame(self, values=sets, label="Select Set")
        self.set_frame.grid(row=1, column=0, padx=20, pady=20)

        self.format_frame = ConfigFrame(self, values=GUI_CONSTS.FORMAT_KEYS, label="Select Format")
        self.format_frame.grid(row=0, column=1, padx=20, pady=20)

        self.games_frame = ConfigFrame(self, values=GUI_CONSTS.GAMES_KEYS, label="Select Game")
        self.games_frame.grid(row=1, column=1, padx=20, pady=20)

        self.colors_frame = ConfigFrame(self, values=GUI_CONSTS.COLOR_KEYS, label="Select Color Identity")
        self.colors_frame.grid(row=2, column=0, padx=20, pady=20)

        # self.keywords_frame = ConfigFrame(self, values=GUI_CONSTS.KEYWORDS_KEYS, label="Select Keywords")
        # self.keywords_frame.grid(row=2, column=1, padx=20, pady=20)

        ctk.CTkButton(self,
                      text="Save Configuration",
                      command=self.send_config).grid(row=3, column=0, sticky="ew", padx=20, pady=(0, 20), columnspan=2)

    def send_config(self):
        config = self.config_frame.get()
        config.update(self.set_frame.get())
        config.update(self.format_frame.get())
        config.update(self.games_frame.get())
        config.update(self.colors_frame.get())
        self.master.receive_config(config)
        self.destroy()