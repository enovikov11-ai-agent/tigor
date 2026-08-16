#include <iostream>
#include <unordered_map>
#define MAX_SIZE 500000
#define MOD 1000000007

void calc_divider(long *dividers)
{
    for (int i = 0; i <= MAX_SIZE; i++)
    {
        dividers[i] = 1;
    }

    for (int i = 2; i <= MAX_SIZE; i++)
    {
        if (dividers[i] != 1)
        {
            continue;
        }

        for (int j = i; j <= MAX_SIZE; j += i)
        {
            if (dividers[j] == 1)
            {
                dividers[j] = i;
            }
        }
    }
}

void binominal_modify_interval(int from, int to, std::unordered_map<long, long> *binominal_primes_ptr, long *dividers, long delta)
{
    int i_divisible, i_divider;
    for (int i = from; i <= to; i++)
    {
        i_divisible = i;
        while (i_divisible > 1)
        {
            i_divider = dividers[i_divisible];
            i_divisible = i_divisible / i_divider;
            (*binominal_primes_ptr)[i_divider] = (*binominal_primes_ptr)[i_divider] + delta;
        }
    }
}

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
    long dividers[MAX_SIZE];
    calc_divider(dividers);

    std::unordered_map<long, long> binominal_primes;

    long k, n;
    std::cin >> k >> n;

    if (k > n)
    {
        return 1;
    }

    binominal_modify_interval(n - k + 1, n, &binominal_primes, dividers, 1);
    binominal_modify_interval(1, k, &binominal_primes, dividers, -1);

    long long phi = 1;

    for (auto kv : binominal_primes)
    {
        if (kv.second <= 0)
            continue;
        phi *= ((long long)modpow(kv.first, kv.second - 1, (long)MOD) * ((long long)(kv.first) - 1)) % (long long)MOD;
        phi %= (long long)MOD;
    }

    std::cout << phi << std::endl;

    return 0;
}