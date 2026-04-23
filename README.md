# cs32fp
#Computer Science Final Project: Two-Server Hangman Game 

Project Overview:
For the final project, we will create a Hangman game that uses a two-server idea. The game will allow users to play Hangman by guessing letters in a hidden word. The program will sort words by difficulty level and randomly choose a word based on the level the player selects.

The game will include three difficulty levels: Easy, Medium, Hard. When the user picks a level, the program will ask open.ai to randomly select a word from that category meeting the following conditions.

Difficulty Rules:
Easy - Randomly give me a word that is less than 4 letters and starts and ends with a consonant.
Medium - Randomly give me a word that is between 5 and 8 letters and has at least one vowel. 
Hard - Randomly give me a word that is more than 9 letters and has no double letters.

Game Flow:
The program welcomes the player to CS32 Hangman.
The user chooses a difficulty level: easy, medium, or hard.
The program randomly selects a word from the correct difficulty category, meeting conditions.
The game first prints the number of blanks to show how many letters are in the word.
The player guesses one letter at a time. If you guess the same letter twice, it will tell you.
After each guess, the program updates and displays:
the correctly guessed letters in the blanks
the incorrect letters guessed so far
If the player guesses all the letters before the drawing is complete, they win.
If the player makes too many incorrect guesses, they lose.
At the end of the game, the user is asked if they want to play again.
If they choose yes, the program automatically restarts.

When the player has only one guess remaining, the program will prompt them with the option to receive a hint. If the user selects yes, the program randomly selects one letter from the word that has not already been guessed. That letter is revealed in the correct position(s) in the word

Two-Server Idea:
The project uses a two-server structure. One server is responsible for storing or managing the word bank and selecting words based on difficulty. The other server handles the gameplay, such as receiving guesses, updating the board, tracking incorrect attempts, and displaying results. This setup separates the data side from the game logic side.

FUTURE EDITS: Ascii Art to display hangman image 
We used Claude AI and https://developers.openai.com/api/docs/guides/text?utm_source=chatgpt.com

