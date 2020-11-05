

def calculations(num1, num2):
    return num1 + num2

def time_measure(func):
    def wrapper(*args, **kwargs):


if __name__ == '__main__':
    a = 1
    b = 100
    result = calculations(a, b)
    print(f"Result of calculation: {result}")

# *args = Ein Stern beliebeige Anzahl an Arguments
# **kwargs = beleibiege Anzahl an Keyword Argumants (z.B. alter = 60)
