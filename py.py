import datetime
import json
import random
import tkinter as tk
from tkinter import messagebox
import urllib.error
import urllib.parse
import urllib.request
import chess


WORD_LIST = (
    "APPLE",
    "BEACH",
    "BRAVE",
    "CHAIR",
    "CLOUD",
    "CRANE",
    "DREAM",
    "EARTH",
    "FLAME",
    "FROST",
    "GHOST",
    "GRAPE",
    "HEART",
    "HONEY",
    "HOUSE",
    "LIGHT",
    "MANGO",
    "METAL",
    "NIGHT",
    "OCEAN",
    "PAPER",
    "PIZZA",
    "PLANT",
    "QUEST",
    "RIVER",
    "ROBOT",
    "SHADE",
    "SMILE",
    "SOLAR",
    "STONE",
    "STORM",
    "TIGER",
    "TRAIN",
    "TRUST",
    "WATER",
    "WHEEL",
    "WORLD",
    "YOUNG",
    "ZEBRA",
    "ALERT",
    "AMBER",
    "BASIC",
    "BERRY",
    "BLACK",
    "BREAD",
    "BRICK",
    "BRUSH",
    "CANDY",
    "CHESS",
    "CLEAR",
    "CORAL",
    "DANCE",
    "DATED",
    "ELDER",
    "FIELD",
    "FRESH",
    "FRUIT",
    "GIANT",
    "GLASS",
    "GREEN",
    "HAPPY",
    "HORSE",
    "IVORY",
    "JELLY",
    "JUICE",
    "KNIFE",
    "LEMON",
    "MAGIC",
    "MAPLE",
    "MONEY",
    "MONTH",
    "MOUSE",
    "MOVIE",
    "MUSIC",
    "NERVE",
    "NOBLE",
    "NOVEL",
    "OLIVE",
    "PANDA",
    "PEACH",
    "PEARL",
    "PIANO",
    "PRIDE",
    "QUEEN",
    "QUIET",
    "RADIO",
    "RAINY",
    "ROUND",
    "ROYAL",
    "SALTY",
    "SCALE",
    "SHEEP",
    "SHINE",
    "SHIRT",
    "SHORE",
    "SKATE",
    "SLEEP",
    "SOUTH",
    "SPACE",
    "SPARK",
    "SPEED",
    "SPIKE",
    "SPOON",
    "SPRING",
    "SUGAR",
    "TABLE",
    "THUMB",
    "TODAY",
    "TOWER",
    "TULIP",
    "UNDER",
    "VITAL",
    "VOICE",
    "WATCH",
    "WHITE",
    "WINDY",
    "WOMAN",
    "YOUTH",
)


def get_todays_word():
    today = datetime.date.today().strftime("%Y-%m-%d")
    url = f"https://www.nytimes.com/svc/wordle/v2/{today}.json"
    request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})

    with urllib.request.urlopen(request, timeout=10) as response:
        data = json.load(response)

    word = data.get("solution", "").upper()
    if len(word) != 5:
        raise RuntimeError("Today's Wordle is not a five-letter word")
    return word


def get_unlimited_word():
    return random.choice(WORD_LIST)


WORD_VALIDATION_CACHE = {}


def is_real_word(word):
    word = word.upper()
    if word in WORD_VALIDATION_CACHE:
        return WORD_VALIDATION_CACHE[word]

    if word in WORD_LIST:
        WORD_VALIDATION_CACHE[word] = True
        return True

    url = f"https://api.datamuse.com/words?sp={urllib.parse.quote(word.lower())}&md=d&max=20"
    request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})

    try:
        with urllib.request.urlopen(request, timeout=3) as response:
            matches = json.load(response)
        valid = any(match["word"].upper() == word for match in matches)
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, json.JSONDecodeError):
        valid = False

    WORD_VALIDATION_CACHE[word] = valid
    return valid


class WordleGame:
    def __init__(self, root, secret_word):
        self.root = root
        self.secret_word = secret_word
        self.current_row = 0
        self.current_guess = ""
        self.game_over = False

        root.title("Wordle")
        root.configure(bg="#121213")
        root.resizable(False, False)

        header = tk.Frame(root, bg="#121213")
        header.grid(row=0, column=0, columnspan=5, pady=(12, 10), sticky="ew")

        restart_button = tk.Button(
            header,
            text="↻ Restart",
            font=("Arial", 9, "bold"),
            fg="#FFFFFF",
            bg="#3A3A3C",
            activebackground="#565758",
            activeforeground="#FFFFFF",
            relief="flat",
            command=self.restart_game,
        )
        restart_button.grid(row=0, column=0, padx=(10, 4), sticky="w")

        menu_button = tk.Button(
            header,
            text="← Menu",
            font=("Arial", 9, "bold"),
            fg="#FFFFFF",
            bg="#3A3A3C",
            activebackground="#565758",
            activeforeground="#FFFFFF",
            relief="flat",
            command=self.return_to_main_menu,
        )
        menu_button.grid(row=0, column=1, padx=(4, 10), sticky="w")

        title = tk.Label(
            header,
            text="WORDLE",
            font=("Arial", 24, "bold"),
            fg="#FFFFFF",
            bg="#121213",
        )
        title.grid(row=0, column=2)

        header.columnconfigure(0, weight=1)
        header.columnconfigure(1, weight=0)
        header.columnconfigure(2, weight=1)
        header.columnconfigure(3, weight=1)

        self.letters_visible = False
        self.letter_button = tk.Button(
            header,
            text="Letters  ▼",
            font=("Arial", 9, "bold"),
            fg="#FFFFFF",
            bg="#3A3A3C",
            activebackground="#565758",
            activeforeground="#FFFFFF",
            relief="flat",
            command=self.toggle_letter_panel,
        )
        self.letter_button.grid(row=0, column=3, padx=(20, 10), sticky="e")

        self.letter_panel = tk.Frame(root, bg="#121213")
        self.letter_panel.grid(row=3, column=0, columnspan=5, padx=(10, 4), pady=(0, 8))
        self.letter_panel.grid_remove()

        self.letter_labels = {}
        letter_keyboard = tk.Frame(self.letter_panel, bg="#121213")
        letter_keyboard.grid(row=0, column=0, padx=(0, 8), pady=2)

        keyboard_rows = ("QWERTYUIOP", "ASDFGHJKL", "ZXCVBNM")
        for row_number, letters in enumerate(keyboard_rows):
            row_frame = tk.Frame(letter_keyboard, bg="#121213")
            row_frame.grid(row=row_number, column=0, pady=1)

            for letter in letters:
                button = tk.Button(
                    row_frame,
                    text=letter,
                    width=3,
                    height=1,
                    font=("Arial", 10, "bold"),
                    fg="#FFFFFF",
                    bg="#3A3A3C",
                    activebackground="#565758",
                    activeforeground="#FFFFFF",
                    relief="raised",
                    borderwidth=2,
                    command=lambda value=letter: self.add_letter(value),
                )
                button.pack(side="left", padx=1)
                self.letter_labels[letter] = button

        enter_button = tk.Button(
            self.letter_panel,
            text="ENTER",
            width=5,
            height=2,
            font=("Arial", 9, "bold"),
            fg="#FFFFFF",
            bg="#538D4E",
            activebackground="#6AAA64",
            activeforeground="#FFFFFF",
            relief="raised",
            borderwidth=2,
            command=self.submit_guess,
        )
        enter_button.grid(row=0, column=1, padx=(3, 0), pady=0, sticky="n")

        backspace_button = tk.Button(
            self.letter_panel,
            text="⌫",
            width=5,
            height=1,
            font=("Arial", 10, "bold"),
            fg="#FFFFFF",
            bg="#3A3A3C",
            activebackground="#565758",
            activeforeground="#FFFFFF",
            relief="raised",
            borderwidth=2,
            command=self.delete_letter,
        )
        backspace_button.grid(row=1, column=1, padx=(3, 0), pady=(0, 0), sticky="n")

        self.keyboard_state = {letter: "#3A3A3C" for letter in "ABCDEFGHIJKLMNOPQRSTUVWXYZ"}

        self.tiles = []
        board = tk.Frame(root, bg="#121213")
        board.grid(row=1, column=0, columnspan=5, padx=20)

        for row in range(6):
            tile_row = []
            for column in range(5):
                tile = tk.Label(
                    board,
                    text="",
                    width=4,
                    height=2,
                    font=("Arial", 18, "bold"),
                    fg="#FFFFFF",
                    bg="#121213",
                    relief="solid",
                    borderwidth=2,
                    highlightthickness=1,
                    highlightbackground="#3A3A3C",
                )
                tile.grid(row=row, column=column, padx=3, pady=3)
                tile_row.append(tile)
            self.tiles.append(tile_row)

        self.status = tk.Label(
            root,
            text="Type a five-letter word",
            font=("Arial", 11),
            fg="#FFFFFF",
            bg="#121213",
        )
        self.status.grid(row=2, column=0, columnspan=5, pady=(8, 12))

        root.bind("<Key>", self.handle_key)

    def toggle_letter_panel(self):
        if self.letters_visible:
            self.letter_panel.grid_remove()
            self.letter_button.configure(text="Letters  ▼")
        else:
            self.letter_panel.grid()
            self.letter_button.configure(text="Letters  ▲")
        self.letters_visible = not self.letters_visible

    def handle_key(self, event):
        if self.game_over:
            return

        key = event.keysym
        if key == "BackSpace":
            self.delete_letter()
        elif key == "Return":
            self.submit_guess()
        elif len(event.char) == 1 and event.char.isalpha():
            self.add_letter(event.char.upper())

    def add_letter(self, letter):
        if len(self.current_guess) >= 5:
            return

        self.current_guess += letter
        column = len(self.current_guess) - 1
        tile = self.tiles[self.current_row][column]
        tile.configure(text=letter)

    def delete_letter(self):
        if not self.current_guess:
            return

        column = len(self.current_guess) - 1
        self.tiles[self.current_row][column].configure(text="")
        self.current_guess = self.current_guess[:-1]

    def submit_guess(self):
        if len(self.current_guess) != 5:
            self.status.configure(text="Not enough letters")
            self.shake_row()
            return

        guess = self.current_guess
        if not is_real_word(guess):
            self.status.configure(text="Not in word list")
            self.shake_row()
            return

        colors = self.get_letter_colors(guess)

        for column, letter in enumerate(guess):
            self.tiles[self.current_row][column].configure(
                text=letter,
                bg=colors[column],
                highlightthickness=0,
            )
            self.update_keyboard_state(letter, colors[column])

        if guess == self.secret_word:
            self.status.configure(text="You guessed it!")
            self.game_over = True
            self.root.after(200, self.ask_to_play_again)
        elif self.current_row == 5:
            self.status.configure(text=f"The word was {self.secret_word}")
            self.game_over = True
            self.root.after(200, self.ask_to_play_again)
        else:
            self.current_row += 1
            self.current_guess = ""
            self.status.configure(text="Next guess")

    def update_keyboard_state(self, letter, color):
        priority = {"#3A3A3C": 0, "#B59F3B": 1, "#538D4E": 2}
        current = self.keyboard_state[letter]

        # Grey means this letter is absent. It may be downgraded or
        # upgraded by another guess, but can never replace yellow or green.
        if priority[color] >= priority[current]:
            self.keyboard_state[letter] = color
            self.letter_labels[letter].configure(bg=color)

    def get_letter_colors(self, guess):
        result = ["#3A3A3C"] * 5
        remaining = list(self.secret_word)

        for index, letter in enumerate(guess):
            if letter == self.secret_word[index]:
                result[index] = "#538D4E"
                remaining[index] = None

        for index, letter in enumerate(guess):
            if result[index] != "#538D4E" and letter in remaining:
                result[index] = "#B59F3B"
                remaining[remaining.index(letter)] = None

        return result

    def shake_row(self):
        original_x = self.root.winfo_x()

        def move(offset, delay):
            self.root.after(delay, lambda: self.root.geometry(f"+{original_x + offset}+{self.root.winfo_y()}"))

        move(-8, 40)
        move(8, 80)
        move(-4, 120)
        move(4, 160)
        move(0, 200)

    def ask_to_play_again(self):
        if messagebox.askyesno("Play again", "Choose another game?"):
            show_main_menu(self.root)

    def restart_game(self):
        if messagebox.askyesno("Restart", "Return to the Wordle mode menu?"):
            show_mode_menu(self.root)

    def return_to_main_menu(self):
        if messagebox.askyesno("Main Menu", "Return to the Mini Game Studio?"):
            show_main_menu(self.root)


def show_mode_menu(root):
    root.unbind("<Key>")
    root.title("Mini Game Studio")
    root.configure(bg="#121213")
    root.resizable(False, False)

    for widget in root.winfo_children():
        widget.destroy()

    panel = tk.Frame(root, bg="#121213", padx=24, pady=20)
    panel.grid(row=0, column=0)

    logo_frame = tk.Frame(panel, bg="#121213")
    logo_frame.grid(row=0, column=0, pady=(0, 14))

    logo_letters = ("W", "O", "R", "D", "L", "E")
    for index, letter in enumerate(logo_letters):
        color = "#538D4E" if index in (0, 5) else "#B59F3B" if index in (1, 4) else "#3A3A3C"
        tk.Label(
            logo_frame,
            text=letter,
            width=3,
            height=1,
            font=("Arial", 16, "bold"),
            fg="#FFFFFF",
            bg=color,
            relief="flat",
        ).grid(row=0, column=index, padx=2)

    tk.Label(
        panel,
        text="WORDLE",
        font=("Arial", 12, "bold"),
        fg="#FFFFFF",
        bg="#121213",
    ).grid(row=1, column=0, pady=(0, 18))

    tk.Label(
        panel,
        text="Choose a game",
        font=("Arial", 18, "bold"),
        fg="#FFFFFF",
        bg="#121213",
    ).grid(row=2, column=0, pady=(0, 12))

    def launch(mode):
        for widget in root.winfo_children():
            widget.destroy()

        if mode == "today":
            try:
                secret_word = get_todays_word()
            except (
                urllib.error.URLError,
                urllib.error.HTTPError,
                TimeoutError,
                RuntimeError,
                json.JSONDecodeError,
            ) as error:
                messagebox.showerror("Unable to load today's Wordle", str(error))
                show_mode_menu(root)
                return
        else:
            secret_word = get_unlimited_word()

        WordleGame(root, secret_word)

    cards = tk.Frame(panel, bg="#121213")
    cards.grid(row=3, column=0)

    for card_index, (label, description, mode) in enumerate((
        ("TODAY", "The official daily word", "today"),
        ("UNLIMITED", "A fresh random word", "unlimited"),
    )):
        card = tk.Button(
            cards,
            text=f"{label}\n{description}",
            font=("Arial", 11, "bold"),
            fg="#FFFFFF",
            bg="#538D4E" if card_index == 0 else "#3A3A3C",
            activebackground="#6AAA64" if card_index == 0 else "#565758",
            activeforeground="#FFFFFF",
            width=20,
            height=3,
            relief="raised",
            borderwidth=3,
            command=lambda selected_mode=mode: launch(selected_mode),
        )
        card.grid(row=0, column=card_index, padx=8)

    tk.Button(
        panel,
        text="← Main Menu",
        font=("Arial", 10, "bold"),
        fg="#FFFFFF",
        bg="#3A3A3C",
        activebackground="#565758",
        activeforeground="#FFFFFF",
        width=18,
        relief="raised",
        command=lambda: show_main_menu(root),
    ).grid(row=4, column=0, pady=(12, 0))


def show_chess_menu(root):
    for widget in root.winfo_children():
        widget.destroy()

    root.title("Chess Mode")
    root.configure(bg="#121213")

    panel = tk.Frame(root, bg="#121213", padx=24, pady=20)
    panel.grid(row=0, column=0)

    tk.Label(panel, text="CHESS", font=("Arial", 22, "bold"), fg="#FFFFFF", bg="#121213").grid(row=0, column=0, columnspan=2, pady=(0, 16))

    def launch(mode):
        ChessGame(root, mode)

    modes = (
        ("2 Players", "2-player"),
        ("Easy AI", "easy"),
        ("Medium AI", "medium"),
        ("Hard AI", "hard"),
    )

    for index, (label, mode) in enumerate(modes):
        tk.Button(panel, text=label, command=lambda selected=mode: launch(selected), font=("Arial", 11, "bold"), fg="#FFFFFF", bg="#538D4E" if mode == "2-player" else "#3A3A3C", width=18, height=2).grid(row=1 + index, column=0, padx=10, pady=5)

    tk.Button(panel, text="← Main Menu", command=lambda: show_main_menu(root), font=("Arial", 10), fg="#FFFFFF", bg="#3A3A3C", width=18).grid(row=5, column=0, pady=(12, 0))


def show_tic_tac_toe_menu(root):
    for widget in root.winfo_children():
        widget.destroy()

    root.title("Tic-Tac-Toe Mode")
    root.configure(bg="#121213")

    panel = tk.Frame(root, bg="#121213", padx=24, pady=20)
    panel.grid(row=0, column=0)

    tk.Label(panel, text="TIC-TAC-TOE", font=("Arial", 22, "bold"), fg="#FFFFFF", bg="#121213").grid(row=0, column=0, pady=(0, 16))

    def launch(mode):
        TicTacToeGame(root, mode)

    modes = (
        ("2 Players", "2-player"),
        ("Easy AI", "easy"),
        ("Medium AI", "medium"),
        ("Hard AI", "hard"),
    )

    for index, (label, mode) in enumerate(modes):
        tk.Button(panel, text=label, command=lambda selected=mode: launch(selected), font=("Arial", 11, "bold"), fg="#FFFFFF", bg="#538D4E" if mode == "2-player" else "#3A3A3C", width=18, height=2).grid(row=1 + index, column=0, padx=10, pady=5)

    tk.Button(panel, text="← Main Menu", command=lambda: show_main_menu(root), font=("Arial", 10), fg="#FFFFFF", bg="#3A3A3C", width=18).grid(row=5, column=0, pady=(12, 0))


def show_main_menu(root):
    root.unbind("<Key>")
    root.title("Mini Game Studio")
    root.configure(bg="#121213")
    root.resizable(False, False)

    for widget in root.winfo_children():
        widget.destroy()

    panel = tk.Frame(root, bg="#121213", padx=28, pady=24)
    panel.grid(row=0, column=0)

    tk.Label(
        panel,
        text="MINI GAME STUDIO",
        font=("Arial", 22, "bold"),
        fg="#FFFFFF",
        bg="#121213",
    ).grid(row=0, column=0, columnspan=3, pady=(0, 18))

    games = (
        ("♟", "CHESS", "Classic board game", "chess"),
        ("W", "WORDLE", "Five-letter word game", "wordle"),
        ("#", "TIC-TAC-TOE", "Three-in-a-row", "tic_tac_toe"),
    )

    for column, (symbol, name, description, game) in enumerate(games):
        card = tk.Frame(panel, bg="#1F1F1F", relief="raised", borderwidth=3)
        card.grid(row=1, column=column, padx=8, ipadx=8, ipady=10)

        tk.Label(
            card,
            text=symbol,
            font=("Arial", 24, "bold"),
            fg="#FFFFFF",
            bg="#538D4E" if game == "wordle" else "#3A3A3C",
            width=4,
            height=2,
            relief="flat",
        ).grid(row=0, column=0, padx=12, pady=(10, 8))

        tk.Label(
            card,
            text=name,
            font=("Arial", 12, "bold"),
            fg="#FFFFFF",
            bg="#1F1F1F",
        ).grid(row=1, column=0, padx=12, pady=(0, 4))

        tk.Label(
            card,
            text=description,
            font=("Arial", 9),
            fg="#BBBBBB",
            bg="#1F1F1F",
        ).grid(row=2, column=0, padx=12, pady=(0, 10))

        if game == "wordle":
            command = lambda: show_mode_menu(root)
        elif game == "chess":
            command = lambda: show_chess_menu(root)
        else:
            command = lambda: show_tic_tac_toe_menu(root)

        tk.Button(
            card,
            text="PLAY",
            font=("Arial", 10, "bold"),
            fg="#FFFFFF",
            bg="#538D4E" if game != "tic_tac_toe" else "#B59F3B",
            activebackground="#6AAA64" if game != "tic_tac_toe" else "#C9B458",
            activeforeground="#FFFFFF",
            width=12,
            relief="raised",
            borderwidth=2,
            command=command,
        ).grid(row=3, column=0, pady=(0, 12))


def start_game():
    root = tk.Tk()
    show_main_menu(root)
    root.mainloop()


if __name__ == "__main__":
    start_game()


class TicTacToeGame:
    def __init__(self, root, mode="easy"):
        self.root = root
        self.mode = mode
        self.board = [""] * 9
        self.current = "X"
        self.game_over = False

        root.title("Tic-Tac-Toe")
        root.configure(bg="#121213")

        for widget in root.winfo_children():
            widget.destroy()

        tk.Button(root, text="← Menu", command=lambda: show_main_menu(root), font=("Arial", 9, "bold"), fg="#FFFFFF", bg="#3A3A3C", relief="flat").grid(row=0, column=0, sticky="w", padx=8, pady=8)
        tk.Label(root, text="TIC-TAC-TOE", font=("Arial", 20, "bold"), fg="#FFFFFF", bg="#121213").grid(row=0, column=1, columnspan=3, pady=8)

        self.status = tk.Label(root, text="X's turn", font=("Arial", 11), fg="#FFFFFF", bg="#121213")
        self.status.grid(row=1, column=0, columnspan=3, pady=(0, 8))

        self.buttons = []
        for index in range(9):
            row, column = divmod(index, 3)
            button = tk.Button(root, text="", font=("Arial", 24, "bold"), width=4, height=2, fg="#FFFFFF", bg="#3A3A3C", activebackground="#565758", command=lambda i=index: self.play(i))
            button.grid(row=row + 2, column=column, padx=3, pady=3)
            self.buttons.append(button)

    def play(self, index):
        if self.game_over or self.board[index]:
            return

        if self.mode == "2-player":
            self.make_move(index, self.current)
        else:
            self.make_move(index, "X")

        if self.game_over:
            return

        if self.mode == "2-player":
            return

        self.status.configure(text="AI is thinking...")
        self.root.after(250, self.ai_move)

    def ai_move(self):
        if self.game_over:
            return
        available = [i for i, value in enumerate(self.board) if not value]
        if not available:
            return

        if self.mode == "easy":
            move = random.choice(available)
        else:
            move = self.best_move()

        self.make_move(move, "O")

    def best_move(self):
        for mark in ("O", "X"):
            for index in [i for i, value in enumerate(self.board) if not value]:
                self.board[index] = mark
                if self.is_winner(mark):
                    self.board[index] = ""
                    return index
                self.board[index] = ""

        available = [i for i, value in enumerate(self.board) if not value]
        return random.choice(available) if self.mode == "medium" else max(available, key=lambda i: self.corner_score(i))

    def corner_score(self, index):
        return 4 if index in (0, 2, 6, 8) else 3 if index == 4 else 1

    def make_move(self, index, mark):
        self.board[index] = mark
        self.buttons[index].configure(text=mark)

        if self.is_winner(mark):
            self.game_over = True
            self.status.configure(text=f"{mark} wins!")
            self.root.after(300, lambda: self.ask_again())
        elif "" not in self.board:
            self.game_over = True
            self.status.configure(text="Draw!")
            self.root.after(300, lambda: self.ask_again())
        else:
            self.current = "O" if mark == "X" else "X"
            self.status.configure(text=f"{self.current}'s turn")

    def is_winner(self, mark):
        lines = ((0,1,2),(3,4,5),(6,7,8),(0,3,6),(1,4,7),(2,5,8),(0,4,8),(2,4,6))
        return any(all(self.board[i] == mark for i in line) for line in lines)

    def ask_again(self):
        if messagebox.askyesno("Play again", "Play another Tic-Tac-Toe game?"):
            TicTacToeGame(self.root, self.mode)


class ChessGame:
    PIECES = {
        "P":"♙","N":"♘","B":"♗","R":"♖","Q":"♕","K":"♔",
        "p":"♟","n":"♞","b":"♝","r":"♜","q":"♛","k":"♚",
    }

    def __init__(self, root, mode="2-player"):
        self.root = root
        self.mode = mode
        self.board = chess.Board()
        self.selected = None

        root.title("Chess")
        root.configure(bg="#121213")
        root.resizable(False, False)

        for widget in root.winfo_children():
            widget.destroy()

        header = tk.Frame(root, bg="#121213")
        header.grid(row=0, column=0, columnspan=8, pady=8)
        tk.Button(header, text="← Menu", command=lambda: show_main_menu(root), font=("Arial", 9, "bold"), fg="#FFFFFF", bg="#3A3A3C", relief="flat").grid(row=0, column=0, padx=(0, 80))
        tk.Label(header, text="CHESS", font=("Arial", 20, "bold"), fg="#FFFFFF", bg="#121213").grid(row=0, column=1)

        self.status = tk.Label(root, text="White to move", font=("Arial", 10), fg="#FFFFFF", bg="#121213")
        self.status.grid(row=1, column=0, columnspan=8, pady=(0, 6))

        self.buttons = {}
        for rank in range(8):
            for file in range(8):
                square = chess.square(file, 7 - rank)
                button = tk.Button(root, text="", font=("Arial", 22), width=2, height=1, relief="flat", borderwidth=0, command=lambda s=square: self.click_square(s))
                button.grid(row=rank + 2, column=file, padx=0, pady=0)
                self.buttons[square] = button
        self.draw()

    def piece_symbol(self, piece):
        return "" if piece is None else self.PIECES[piece.symbol()]

    def draw(self):
        for rank in range(8):
            for file in range(8):
                square = chess.square(file, 7 - rank)
                piece = self.board.piece_at(square)
                base = "#EEEED2" if (rank + file) % 2 == 0 else "#769656"
                fg = "#FFFFFF" if piece and piece.color == chess.BLACK else "#111111"
                self.buttons[square].configure(text=self.piece_symbol(piece), bg=base, activebackground=base, fg=fg)

        if self.selected is not None:
            self.buttons[self.selected].configure(bg="#F6F669")

        if self.board.is_checkmate():
            winner = "Black" if self.board.turn == chess.WHITE else "White"
            self.status.configure(text=f"Checkmate — {winner} wins!")
            self.root.after(300, lambda: self.ask_again())
        elif self.board.is_stalemate() or self.board.is_insufficient_material():
            self.status.configure(text="Draw!")
            self.root.after(300, lambda: self.ask_again())
        elif self.board.is_check():
            self.status.configure(text=("Black" if self.board.turn == chess.BLACK else "White") + " is in check")
        else:
            self.status.configure(text=("Black" if self.board.turn == chess.BLACK else "White") + " to move")

    def click_square(self, square):
        if self.mode != "2-player" and self.board.turn == chess.BLACK:
            return
        piece = self.board.piece_at(square)

        if self.selected is None:
            if piece and piece.color == self.board.turn:
                self.selected = square
                self.draw()
            return

        move = chess.Move(self.selected, square)
        if move in self.board.legal_moves:
            self.board.push(move)
            self.selected = None
            self.draw()
            if self.mode != "2-player" and not self.board.is_game_over():
                self.status.configure(text="AI is thinking...")
                self.root.after(300, self.ai_move)
        else:
            if piece and piece.color == self.board.turn:
                self.selected = square
            else:
                self.selected = None
            self.draw()

    def ai_move(self):
        if self.board.is_game_over():
            self.draw()
            return
        legal = list(self.board.legal_moves)
        if not legal:
            return

        if self.mode == "easy":
            move = random.choice(legal)
        else:
            move = max(legal, key=lambda candidate: self.move_score(candidate))

        self.board.push(move)
        self.draw()

    def move_score(self, move):
        values = {chess.PAWN:1, chess.KNIGHT:3, chess.BISHOP:3, chess.ROOK:5, chess.QUEEN:9, chess.KING:100}
        score = 0
        captured = self.board.piece_at(move.to_square)
        if captured:
            score += values[captured.piece_type] * 10
        if self.board.gives_check(move):
            score += 5
        if move.promotion:
            score += values[move.promotion]

        if self.mode == "hard":
            self.board.push(move)
            replies = list(self.board.legal_moves)
            if replies:
                reply = max(replies, key=lambda candidate: values[self.board.piece_type_at(candidate.to_square)] if self.board.piece_at(candidate.to_square) else 0)
                score -= 2 * (values[self.board.piece_type_at(reply.to_square)] if self.board.piece_at(reply.to_square) else 0)
            self.board.pop()
        return score + random.random()

    def ask_again(self):
        if messagebox.askyesno("Play again", "Play another chess game?"):
            ChessGame(self.root, self.mode)

