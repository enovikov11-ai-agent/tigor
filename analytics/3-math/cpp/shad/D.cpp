#include <algorithm>
#include <iostream>

int main(int argc, char *argv[])
{
    long long n;
    std::cin >> n;
    long long a[n];
    long long result = 0;
    for (long long i = 0; i < n; i++)
    {
        std::cin >> a[i];
    }

    std::sort(a, a + n);
    long long x;

    for (long long i = 0; i < n - 2; i++)
    {
        x = a[i] + a[n - 2];
        result += x;

        if (x < a[n - 1])
        {
            a[n - 2] = x;
        }
        else
        {
            a[n - 2] = a[n - 1];
            a[n - 1] = x;
        }
    }

    for (long long i = n - 2; i < n; i++)
    {
        if (i >= 0)
        {
            result += a[i];
        }
    }

    std::cout << result << std::endl;
}