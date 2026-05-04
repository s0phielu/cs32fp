"""
CS32 Hangman - server.py
Two-server architecture:
  - Word Server  (PORT 65432): selects a word via OpenAI based on difficulty
  - Game Server  (PORT 65433): manages all gameplay logic
Run this file first, then run client.py.
"""

import socket
import threading
import json
import random
import os
from openai import OpenAI

# ── OpenAI client ────────────────────────────────────────────────────────────
openai_client = OpenAI(api_key="sk-your-actual-key-here")

WORD_SERVER_HOST = "127.0.0.1"
WORD_SERVER_PORT = 65432

GAME_SERVER_HOST = "127.0.0.1"
GAME_SERVER_PORT = 65433

MAX_WRONG = 6          # classic hangman: 6 wrong guesses allowed

HANGMAN_STAGES = [
    # 0 wrong
    """
  +---+
  |   |
      |
      |
      |
      |
=========""",
    # 1 wrong
    """
  +---+
  |   |
  O   |
      |
      |
      |
=========""",
    # 2 wrong
    """
  +---+
  |   |
  O   |
  |   |
      |
      |
=========""",
    # 3 wrong
    """
  +---+
  |   |
  O   |
 /|   |
      |
      |
=========""",
    # 4 wrong
    """
  +---+
  |   |
  O   |
 /|\\  |
      |
      |
=========""",
    # 5 wrong
    """
  +---+
  |   |
  O   |
 /|\  |
 /    |
      |
=========""",
    # 6 wrong – game over
    """
  +---+
  |   |
  O   |
 /|\  |
 / \  |
      |
=========""",
]


# ═══════════════════════════════════════════════════════════════════════════════
# WORD SERVER  –  selects a word from OpenAI based on difficulty
# ═══════════════════════════════════════════════════════════════════════════════

DIFFICULTY_PROMPTS = {
    "easy": (
        "Give me exactly one English word that is fewer than 4 letters long, "
        "starts with a consonant, and ends with a consonant. "
        "Reply with ONLY the single lowercase word, nothing else."
    ),
    "medium": (
        "Give me exactly one English word that is between 5 and 8 letters long "
        "and contains at least one vowel. "
        "Reply with ONLY the single lowercase word, nothing else."
    ),
    "hard": (
        "Give me exactly one English word that is more than 9 letters long "
        "and has no repeated (double) letters anywhere in it. "
        "Reply with ONLY the single lowercase word, nothing else."
    ),
}


def fetch_word_from_openai(difficulty: str) -> str:
    """Ask OpenAI for a word matching the difficulty rules. Returns lowercase word."""
    prompt = DIFFICULTY_PROMPTS.get(difficulty.lower())
    if not prompt:
        raise ValueError(f"Unknown difficulty: {difficulty}")

    response = openai_client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=20,
        temperature=1.0,
    )
    word = response.choices[0].message.content.strip().lower()
    # Strip punctuation just in case the model adds a period, etc.
    word = "".join(ch for ch in word if ch.isalpha())
    return word


def handle_word_client(conn, addr):
    """Handle one request to the Word Server."""
    try:
        data = conn.recv(1024).decode().strip()
        if not data:
            return
        difficulty = data.lower()
        print(f"[Word Server] Request for difficulty='{difficulty}' from {addr}")
        word = fetch_word_from_openai(difficulty)
        print(f"[Word Server] Returning word='{word}'")
        conn.sendall((word + "\n").encode())
    except Exception as e:
        print(f"[Word Server] Error: {e}")
        conn.sendall(("ERROR:" + str(e) + "\n").encode())
    finally:
        conn.close()


def run_word_server():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((WORD_SERVER_HOST, WORD_SERVER_PORT))
        s.listen()
        print(f"[Word Server] Listening on {WORD_SERVER_HOST}:{WORD_SERVER_PORT}")
        while True:
            conn, addr = s.accept()
            threading.Thread(target=handle_word_client, args=(conn, addr), daemon=True).start()


# ═══════════════════════════════════════════════════════════════════════════════
# GAME SERVER  –  manages full game sessions
# ═══════════════════════════════════════════════════════════════════════════════

def get_word_from_word_server(difficulty: str) -> str:
    """Game Server asks Word Server for a word."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((WORD_SERVER_HOST, WORD_SERVER_PORT))
        s.sendall((difficulty + "\n").encode())
        response = b""
        while True:
            chunk = s.recv(1024)
            if not chunk:
                break
            response += chunk
            if b"\n" in response:
                break
    return response.decode().strip()


def build_display(word: str, guessed: set) -> str:
    return " ".join(ch if ch in guessed else "_" for ch in word)


def send_json(conn, payload: dict):
    conn.sendall((json.dumps(payload) + "\n").encode())


def recv_json(conn) -> dict:
    data = b""
    while True:
        chunk = conn.recv(4096)
        if not chunk:
            break
        data += chunk
        if b"\n" in data:
            break
    return json.loads(data.decode().strip())


def play_game(conn, difficulty: str):
    """Run a full game session over the socket."""
    # 1. Get word
    word_or_error = get_word_from_word_server(difficulty)
    if word_or_error.startswith("ERROR:"):
        send_json(conn, {"type": "error", "message": word_or_error})
        return

    word = word_or_error
    guessed_letters: set = set()
    wrong_letters: list = []
    wrong_count = 0
    hint_used = False

    # 2. Send initial state
    send_json(conn, {
        "type": "start",
        "blanks": build_display(word, guessed_letters),
        "word_length": len(word),
        "max_wrong": MAX_WRONG,
        "hangman": HANGMAN_STAGES[0],
    })

    # 3. Game loop
    while True:
        msg = recv_json(conn)

        # ── Hint request ──────────────────────────────────────────────────────
        if msg.get("type") == "hint":
            unguessed = [ch for ch in word if ch not in guessed_letters]
            if unguessed:
                hint_letter = random.choice(unguessed)
                guessed_letters.add(hint_letter)
                hint_used = True
                display = build_display(word, guessed_letters)
                won = "_" not in display
                send_json(conn, {
                    "type": "hint_response",
                    "hint_letter": hint_letter,
                    "display": display,
                    "wrong_letters": wrong_letters,
                    "wrong_count": wrong_count,
                    "hangman": HANGMAN_STAGES[wrong_count],
                    "won": won,
                    "word": word if won else "",
                })
                if won:
                    return
            continue

        # ── Regular guess ─────────────────────────────────────────────────────
        guess = msg.get("guess", "").lower()

        if not guess or not guess.isalpha() or len(guess) != 1:
            send_json(conn, {"type": "invalid", "message": "Please enter a single letter."})
            continue

        if guess in guessed_letters or guess in wrong_letters:
            send_json(conn, {"type": "already_guessed", "letter": guess})
            continue

        if guess in word:
            guessed_letters.add(guess)
        else:
            wrong_letters.append(guess)
            wrong_count += 1

        display = build_display(word, guessed_letters)
        won = "_" not in display
        lost = wrong_count >= MAX_WRONG

        # Offer hint when one guess remaining
        offer_hint = (wrong_count == MAX_WRONG - 1) and not hint_used and not won

        send_json(conn, {
            "type": "update",
            "display": display,
            "wrong_letters": wrong_letters,
            "wrong_count": wrong_count,
            "hangman": HANGMAN_STAGES[wrong_count],
            "correct": guess in word,
            "won": won,
            "lost": lost,
            "word": word if (won or lost) else "",
            "offer_hint": offer_hint,
        })

        if won or lost:
            return


def handle_game_client(conn, addr):
    print(f"[Game Server] New connection from {addr}")
    try:
        while True:
            # Wait for a START message (new game or replay)
            msg = recv_json(conn)
            if msg.get("type") == "start_game":
                difficulty = msg.get("difficulty", "medium").lower()
                print(f"[Game Server] Starting game: difficulty='{difficulty}'")
                play_game(conn, difficulty)
            elif msg.get("type") == "quit":
                print(f"[Game Server] Client {addr} quit.")
                break
            else:
                send_json(conn, {"type": "error", "message": "Unexpected message."})
    except (ConnectionResetError, BrokenPipeError, json.JSONDecodeError):
        print(f"[Game Server] Client {addr} disconnected.")
    finally:
        conn.close()


def run_game_server():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((GAME_SERVER_HOST, GAME_SERVER_PORT))
        s.listen()
        print(f"[Game Server] Listening on {GAME_SERVER_HOST}:{GAME_SERVER_PORT}")
        while True:
            conn, addr = s.accept()
            threading.Thread(target=handle_game_client, args=(conn, addr), daemon=True).start()


# ═══════════════════════════════════════════════════════════════════════════════
# ENTRY POINT
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    # Start Word Server in background thread
    wt = threading.Thread(target=run_word_server, daemon=True)
    wt.start()

    # Run Game Server on main thread
    run_game_server()
