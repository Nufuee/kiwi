import random

intro_text = """
Hi there!
I've generated a random 4 digit number for you.
Let's play a bulls and cows game.
"""

end_text = """
Correct, you've guessed the right number in {} guesse(s)!
That's {}!
"""


def generate_number(num_length):
    """Computer generatet 4-digit number with different digits."""
    assert num_length <= 10

    numbers = list(range(10))

    while numbers[0] == 0:
        random.shuffle(numbers)

    return "".join(str(number) for number in numbers[:num_length])


def check_numbers(user_number, secret_number):
    """Check user guess"""
    bulls = 0
    cows = 0

    for i, number in enumerate(user_number):
        # matching digit is in the right position
        if number == secret_number[i]:
            bulls += 1
        # matching digit is in different position
        elif number in secret_number:
            cows += 1

    if bulls == 4:
        return True

    print("{} bulls, {} cows".format(bulls, cows))


def check_status(guesses):
    if guesses < 4:
        status = "pretty amazing"
    elif 4 <= guesses < 7:
        status = "right on the average of human being"
    elif 7 <= guesses < 10:
        status = "not bad but you can be better"
    else:
        status = "sort of bad"

    return status


if __name__ == "__main__":

    user_number = None
    guesses = 0

    secret_number = generate_number(4)
    print(intro_text)

    # user guess
    while user_number != secret_number:
        user_number = input('Enter a number:')
        if len(user_number) == 4 and user_number.isdigit():
            check_numbers(user_number, secret_number)
            guesses += 1
        else:
            print("Hmmm, that's interesting guess. Try to use a 4-digit number ;)")

    status = check_status(guesses)

    print(end_text.format(guesses, status))
