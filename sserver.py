import socket
import random

HOST = "127.0.0.1"
PORT = 5555

WORDS = {
    "easy": ["planet", "garden", "silver", "window"],
    "medium": ["computer", "painting", "elephant", "notebook"],
    "hard": ["algorithm", "networking", "complexity", "programming"]
}


def choose_word(level): # function to select a random word based on difficulty level
    return random.choice(WORDS[level]) # select a random word from the list corresponding to the chosen level


def make_hidden_word(word, guessed_letters): # function to create a hidden version of the word, showing guessed letters and hiding others
    hidden = "" # initialize an empty string to build the hidden word
    for letter in word:
        if letter in guessed_letters:
            hidden += letter
        else:
            hidden += "_"
    return hidden # return the constructed hidden word


def give_hint(word, guessed_letters): # function to provide a hint by selecting a random unguessed letter from the word
    remaining = [letter for letter in word if letter not in guessed_letters]
    if remaining:
        return random.choice(remaining)
    return None # return None if there are no unguessed letters left


server = socket.socket(socket.AF_INET, socket.SOCK_STREAM) #
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
    wrong_guesses = 0
    max_wrong_guesses = 6
    wrong_streak = 0
    hint_used = False

    client.send(f"You picked {level} mode.\n".encode())
    client.send(f"Word: {make_hidden_word(secret_word, guessed_letters)}\n".encode())

    while True:
        client.send(f"Wrong guesses: {wrong_guesses}/{max_wrong_guesses}\n".encode())
        client.send("Guess one letter:\n".encode())
        guess = client.recv(1024).decode().strip().lower()

        if len(guess) != 1:
            client.send("Please enter only one letter.\n".encode())
            continue

        if guess not in guessed_letters:
            guessed_letters.append(guess)

            if guess in secret_word:
                client.send("Correct guess!\n".encode())
                wrong_streak = 0
            else:
                client.send("That letter is not in the word.\n".encode())
                wrong_guesses += 1
                wrong_streak += 1  

        # hint after 3 wrong guesses in a row
        if wrong_streak == 3 and not hint_used:
            client.send("You've had 3 incorrect guesses. Want a hint? (yes/no)\n".encode())
            answer = client.recv(1024).decode().strip().lower()

            if answer == "yes":
                hint_letter = give_hint(secret_word, guessed_letters)
                if hint_letter:
                    guessed_letters.append(hint_letter)
                    client.send(f"Hint: the letter '{hint_letter}' is in the word!\n".encode())
                hint_used = True

            wrong_streak = 0  # reset after offering hint

        current_word = make_hidden_word(secret_word, guessed_letters)
        client.send(f"Word: {current_word}\n".encode())

        if current_word == secret_word:
            client.send("You won!\n".encode())
            break

        if wrong_guesses == max_wrong_guesses:
            client.send("The man has been hanged!\n".encode())
            client.send(f"The word was: {secret_word}\n".encode())
            break

    client.close()
    server.close()
