class A:
    __slots__ = ['a', 'b']
    def __init__(self):
        self.a = 10


if __name__ == '__main__':
    toy = A()
    print(toy.a)

    toy.b = 20

    print(toy.b)
