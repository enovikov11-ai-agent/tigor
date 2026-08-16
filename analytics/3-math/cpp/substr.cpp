#include <iostream>
#include <string>

#define plus(pos)        \
    if (diff[pos] == -1) \
    {                    \
        badCount--;      \
    }                    \
    if (diff[pos] == 0)  \
    {                    \
        badCount++;      \
    }                    \
    diff[pos]++;

#define minus(pos)      \
    if (diff[pos] == 1) \
    {                   \
        badCount--;     \
    }                   \
    if (diff[pos] == 0) \
    {                   \
        badCount++;     \
    }                   \
    diff[pos]--;

int main(int argc, char *argv[])
{
    std::string where;
    std::string what;
    std::cin >> where;
    std::cin >> what;

    if (what.length() > where.length())
    {
        return 0;
    }

    long diff[256];
    long badCount = 0;
    for (int i = 0; i < 256; i++)
    {
        diff[i] = 0;
    }

    for (int i = 0; i < what.length(); i++)
    {
        plus(what.at(i));
        minus(where.at(i));
    }
    if (badCount == 0)
    {
        std::cout << 0 << std::endl;
    }

    for (int i = what.length(); i < where.length(); i++)
    {
        plus(where.at(i - what.length()));
        minus(where.at(i));
        if (badCount == 0)
        {
            std::cout << i - what.length() + 1 << std::endl;
        }
    }

    return 0;
}