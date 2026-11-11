import customtkinter as ctk
import tkinter.messagebox as messagebox


INIT_MSG = "Type your deck list here..."
class DeckListWindow(ctk.CTkToplevel):
    def __init__(self, master, filter_engine):
        super().__init__(master)
        self.title("Filtered Data")
        self.filter_engine = filter_engine
        self.geometry("400x600")
        self.grid_columnconfigure((0, 1), weight=1)

        ctk.CTkLabel(self, text="Write a deck list:").grid(row=0, column=0, padx=20, pady=(20, 10), sticky="w")

        self.textbox = ctk.CTkTextbox(self, height=120)
        self.textbox.grid(row=1, column=0, padx=20, pady=(0, 10), columnspan=2)
        self.textbox.insert("0.0", INIT_MSG)

        ctk.CTkButton(self,
                      text="Save Deck List",
                      command=self.send_deck_list).grid(row=2, column=0, padx=20, pady=(0, 20), columnspan=2)

    def send_deck_list(self):
        text = self.textbox.get("1.0", "end").strip()
        is_valid, error_message = self.validate_deck_list(text)
        if not is_valid:
            messagebox.showerror("Invalid Input", error_message)
            return
        print(f"Deck list received: {text}")
        print("Sending deck list to filter engine...")
        self.destroy()

    def validate_deck_list(self, text):
        # Implement your validation logic here
        # For example, check if the text is not empty and follows a specific format
        if not text:
            return False, "Deck list cannot be empty."
        if text == INIT_MSG:
            return False, "Please enter a valid deck list."
        # Add more validation rules as needed
        return True, ""