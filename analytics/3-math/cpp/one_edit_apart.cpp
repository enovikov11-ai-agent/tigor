#include <iostream>
#include <string>

bool one_edit_apart(std::string word1, std::string word2, int max_tries = 1, int pos1 = 0, int pos2 = 0)
{
    if (max_tries == -1)
    {
        return false;
    }

    while (pos1 < word1.length() && pos2 < word2.length())
    {
        if (word1.at(pos1) == word2.at(pos2))
        {
            pos1++;
            pos2++;
        }
        else
        {
            return one_edit_apart(word1, word2, max_tries - 1, pos1 + 1, pos2) ||
                   one_edit_apart(word1, word2, max_tries - 1, pos1, pos2 + 1) ||
                   one_edit_apart(word1, word2, max_tries - 1, pos1 + 1, pos2 + 1);
        }
    }

    return word1.length() + word2.length() - pos1 - pos2 <= max_tries;
}

int main(int argc, char *argv[])
{
    std::string word1, word2;
    std::cin >> word1 >> word2;

    std::cout << (one_edit_apart(word1, word2) ? "true" : "false") << std::endl;

    return 0;
}