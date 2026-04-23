"""
CS32 Hangman - client.py
Connects to the Game Server and handles all user interaction.
Run server.py first, then run this file.
"""

import socket
import json

GAME_SERVER_HOST = "127.0.0.1"
GAME_SERVER_PORT = 65433


# ─── Socket helpers ────────────────────────────────────────────────────────────

def send_json(sock, payload: dict):
    sock.sendall((json.dumps(payload) + "\n").encode())


def recv_json(sock) -> dict:
    data = b""
    while True:
        chunk = sock.recv(4096)
        if not chunk:
            break
        data += chunk
        if b"\n" in data:
            break
    return json.loads(data.decode().strip())


# ─── Display helpers ───────────────────────────────────────────────────────────

def print_banner():
    print("\n" + "=" * 50)
    print("      Welcome to CS32 Hangman!")
    print("=" * 50)


def print_state(hangman: str, display: str, wrong_letters: list, wrong_count: int, max_wrong: int):
    print(hangman)
    print(f"\n  Word:  {display}")
    wrong_str = ", ".join(wrong_letters) if wrong_letters else "none"
    print(f"  Wrong guesses ({wrong_count}/{max_wrong}): {wrong_str}\n")


def choose_difficulty() -> str:
    while True:
        print("\nChoose a difficulty level:")
        print("  [1] Easy   – short word (< 4 letters)")
        print("  [2] Medium – medium word (5–8 letters)")
        print("  [3] Hard   – long word (9+ letters, no double letters)")
        choice = input("\nEnter 1, 2, or 3 (or type easy/medium/hard): ").strip().lower()
        mapping = {"1": "easy", "2": "medium", "3": "hard",
                   "easy": "easy", "medium": "medium", "hard": "hard"}
        if choice in mapping:
            return mapping[choice]
        print("  Invalid choice. Please try again.")


# ─── Main game loop ────────────────────────────────────────────────────────────

def play_session(sock):
    """Play one full Hangman game."""
    difficulty = choose_difficulty()

    print(f"\n  Fetching a {difficulty} word from the server...")
    send_json(sock, {"type": "start_game", "difficulty": difficulty})

    # Receive initial state
    msg = recv_json(sock)
    if msg.get("type") == "error":
        print(f"\n  Server error: {msg['message']}")
        return

    max_wrong = msg["max_wrong"]
    print_state(msg["hangman"], msg["blanks"], [], 0, max_wrong)

    # Game loop
    while True:
        guess = input("  Guess a letter: ").strip().lower()

        if not guess:
            continue

        if len(guess) != 1 or not guess.isalpha():
            print("  ⚠  Please enter a single letter.")
            continue

        send_json(sock, {"type": "guess", "guess": guess})
        msg = recv_json(sock)

        mtype = msg.get("type")

        if mtype == "invalid":
            print(f"  ⚠  {msg['message']}")
            continue

        if mtype == "already_guessed":
            print(f"  ⚠  You already guessed '{msg['letter']}'. Try a different letter.")
            continue

        if mtype in ("update", "hint_response"):
            correct = msg.get("correct", True)   # hint_response letters are always correct
            letter = msg.get("hint_letter", guess)

            if mtype == "update":
                if correct:
                    print(f"\n  ✓  '{guess}' is in the word!")
                else:
                    print(f"\n  ✗  '{guess}' is not in the word.")

            print_state(msg["hangman"], msg["display"], msg["wrong_letters"],
                        msg["wrong_count"], max_wrong)

            # Win
            if msg.get("won"):
                print(f"  🎉  Congratulations! You guessed the word: {msg['word'].upper()}")
                return

            # Lose
            if msg.get("lost"):
                print(f"  💀  Game over! The word was: {msg['word'].upper()}")
                return

            # Hint offer (one guess remaining)
            if msg.get("offer_hint"):
                hint_choice = input("  ⚡  You have only 1 guess left! Would you like a hint? (yes/no): ").strip().lower()
                if hint_choice in ("yes", "y"):
                    send_json(sock, {"type": "hint"})
                    hmsg = recv_json(sock)
                    print(f"\n  💡  Hint: The letter '{hmsg['hint_letter'].upper()}' has been revealed!")
                    print_state(hmsg["hangman"], hmsg["display"], hmsg["wrong_letters"],
                                hmsg["wrong_count"], max_wrong)
                    if hmsg.get("won"):
                        print(f"  🎉  You win! The word was: {hmsg['word'].upper()}")
                        return


def main():
    print_banner()
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.connect((GAME_SERVER_HOST, GAME_SERVER_PORT))
            print(f"  Connected to game server at {GAME_SERVER_HOST}:{GAME_SERVER_PORT}")

            while True:
                play_session(sock)

                # Play again?
                again = input("\n  Would you like to play again? (yes/no): ").strip().lower()
                if again not in ("yes", "y"):
                    send_json(sock, {"type": "quit"})
                    print("\n  Thanks for playing CS32 Hangman! Goodbye!\n")
                    break

    except ConnectionRefusedError:
        print(f"\n  ERROR: Could not connect to the game server.")
        print(f"  Make sure server.py is running first.\n")


if __name__ == "__main__":
    main()
