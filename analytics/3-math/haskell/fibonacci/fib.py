import sys

sys.set_int_max_str_digits(10000000)

a, b, n = 1, 1, int(input())

if (n <= 2):
    print(1)
    exit()

for _ in range(n // 2 - 1):
    a += b
    b += a

if n % 2 == 0:
    print(b)
else:
    a += b
    print(a)
