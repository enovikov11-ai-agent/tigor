#include <iostream>

template <typename T>
T modpow(T base, T exp, T modulus)
{
    base %= modulus;
    T result = 1;
    while (exp > 0)
    {
        if (exp & 1)
            result = (result * base) % modulus;
        base = (base * base) % modulus;
        exp >>= 1;
    }
    return result;
}

int main(int argc, char *argv[])
{
    long n, buffer, a = 0, b = 1, c;
    std::cin >> n;

    for (long i = 0; i < n; i++)
    {
        std::cin >> buffer;
        c = (a + b) * modpow((long)2, buffer, (long)1000000007);
        c %= 1000000007;
        a = b;
        b = c;
    }

    std::cout << (a + b) % (long)1000000007 << std::endl;

    return 0;
}