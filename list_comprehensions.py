def fib(n):
    assert n >= 0
    if n < 2:
        return n
    return fib(n - 1) + fib(n - 2)


# Construct a list of the fibonacci numbers from 1 to 10 using a loop
fibs = []
for i in range(1, 10):
    fibs.append(fib(i))
print(fibs)

# List comprehension
[fib(i) for i in range(1, 10)]

# Dictionary comprehension
{i: fib(i) for i in range(1, 10)}

# Set comprehension
{fib(i) for i in range(1, 10)}

# Filtering with list comprehensions
data = [fib(i) for i in range(1, 10)]
[x for x in data if x % 2 == 0]


# Write a function to calculate the square of a number
def square(n):
    return n * n


# Write a list comprehension using the square function to calculate the square of the numbers
#   between 20 and 25 inclusive
print([square(n) for n in range(20, 26)])

# Write a function which constructs a list of tuples (a, square(a)) for the numbers 0 to 100 if the square is divisible by 5
print([(a, square(a)) for a in range(0,101) if square(a) % 5 == 0])
