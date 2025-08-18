import random

#  Using Formula 1 team names to play Hangman.
sampleWords = ["Mercedes", "Ferrari", "Red Bull", "Mclaren", "Alpine", "Alphatauri", "Aston Martin", "Haas", "Alfa Romeo", "Williams"]
letters = ['a','b','c','d','e','f','g','h','i','j','k','l','m','n','o','p','q','r','s','t','u','v','w','x','y','z']

#  Variables to set up the minigame.
oneWord = random.choice(sampleWords).replace(" ","").lower()
hangmanWord = []
guessWord = []
original_length = len(oneWord)
default = list(oneWord)
guesses = 10
for i in oneWord:
    hangmanWord.append(i)

j = 0
while j < original_length:
    guessWord.append("")
    j += 1

#  Guess the team.
while guesses > 0:
    print(guessWord)
    
    print("You have ",guesses," guesses left.")
    guess = input("Enter a letter (in small caps): ")
    if guess in hangmanWord and len(guess) == 1:  # Add correct guess/guesses to displayed list.
        k = 0
        while k < original_length:
            if default[k] == guess:
                guessWord[k] = guess
            k += 1
        
        while guess in hangmanWord:
            hangmanWord.remove(guess)

        letters.remove(guess)
        if len(hangmanWord) == 0:
            print(oneWord)
            print("You win!")
            break

    elif guess not in letters:  # Letter might have been guessed already, or there is a typo,
        # so no attempts are deducted.
        continue
      
    else:  # Player makes a wrong guess and loses an attempt.
        guesses -= 1
        letters.remove(guess)
        if guesses == 0:
            print("You lose!")

