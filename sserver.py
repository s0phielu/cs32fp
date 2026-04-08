from socket32 import create_new_socket

HOST = '127.0.0.1'
PORT = 65432
import socket
import random

WORDS = {
    "easy": ["planet", "garden", "silver", "window"],
    "medium": ["computer", "painting", "elephant", "notebook"],
    "hard": ["algorithm", "networking", "complexity", "programming"]
}


def choose_word(level):
    return random.choice(WORDS[level])


def make_hidden_word(word, guessed_letters):
    hidden = ""
    for letter in word:
        if letter in guessed_letters:
            hidden += letter
        else:
            hidden += "_"
    return hidden


def give_hint(word, guessed_letters):
    # reveal one random letter not guessed yet
    remaining = [l for l in word if l not in guessed_letters]
    if remaining:
        return random.choice(remaining)
    return None


server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind((HOST, PORT))
server.listen()

print("Server is running...")

client, address = server.accept()
print("Connected to", address)

client.send("Welcome to Hangman!\n".encode())
client.send("Choose a level: easy, medium, or hard\n".encode())

level = client.recv(1024).decode().strip().lower()

if level not in WORDS:
    client.send("Invalid level. Closing game.\n".encode())
    client.close()
else:
    secret_word = choose_word(level)
    guessed_letters = []
    guess_count = 0
    hint_used = False

    client.send(f"You picked {level} mode.\n".encode())
    client.send(f"Word: {make_hidden_word(secret_word, guessed_letters)}\n".encode())

    while True:
        client.send("Guess one letter:\n".encode())
        guess = client.recv(1024).decode().strip().lower()

        if len(guess) != 1:
            client.send("Please enter only one letter.\n".encode())
            continue

        if guess not in guessed_letters:
            guessed_letters.append(guess)
            guess_count += 1

        # hint prompt if less than 2 guesses and hint not used
        if guess_count < 2 and not hint_used:
            client.send("Do you want a hint? (yes/no)\n".encode())
            answer = client.recv(1024).decode().strip().lower()

            if answer == "yes":
                hint_letter = give_hint(secret_word, guessed_letters)
                if hint_letter:
                    guessed_letters.append(hint_letter)
                    client.send(f"Hint: the letter '{hint_letter}' is in the word!\n".encode())
                hint_used = True

        current_word = make_hidden_word(secret_word, guessed_letters)
        client.send(f"Word: {current_word}\n".encode())

        if current_word == secret_word:
            client.send("You won!\n".encode())
            break

    client.close()
