#include <iostream>
#include <unordered_map>

int main(int argc, char *argv[])
{
    long n;
    std::cin >> n;

    std::unordered_map<long, long> usagesCount;
    long maxKey;
    long maxUsages;
    long current;
    for (long i = 0; i < n; i++)
    {
        std::cin >> current;
        if (usagesCount.find(current) == usagesCount.end())
        {
            usagesCount[current] = 1;
        }
        else
        {
            usagesCount[current]++;
        }

        if (i == 0 || usagesCount[current] > maxUsages || (usagesCount[current] == maxUsages && current > maxKey))
        {
            maxKey = current;
            maxUsages = usagesCount[current];
        }
    }

    std::cout << maxKey << std::endl;

    return 0;
}