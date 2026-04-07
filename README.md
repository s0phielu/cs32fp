# cs32fp
#For our final project, we would like to create a networked server based game of hangman.
Our user would input guess letters into a server that acts similar to the "dclient" portion of PSET3.
The "smart" server would take the guess and be able to determine if it can be placed into the empty word line.
We could use an external library to queue the word itself.
To make the project more nuanced, we will want the smart server to also spit out a visual of the game as the user plays.

The user, in the beginning can choose levels of difficulty. The word length will be correlated with the difficulty. For example, if the level is easy, than the word will be < 7 letters.

Finally, in order to help the user, once we know that there is only 1 guess available, we can prompt the server to ask "would you like a hint?"


