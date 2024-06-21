# Define a function that takes an integer n and returns the nth number in the Fibonacci
# sequence.
def fibonacci(n: int) -> int:
    """Compute the nth number in the Fibonacci sequence."""
    if n == 0:
        return 0
    elif n == 1:
        return 1
    else:
        return fibonacci(n - 1) + fibonacci(n - 2)


# Use a for loop to generate and print the first 10 numbers in the Fibonacci sequence.
for i in range(10):
    print(fibonacci(i))
