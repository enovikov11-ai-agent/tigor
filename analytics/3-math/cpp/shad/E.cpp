#include <iostream>
#include <vector>

struct point
{
    int x;
    int y;
};

void init(std::string *lines, int visits[][], int n, int m)
{
    for (int i = 0; i < 2 * n + 1; i++)
    {
        std::cin >> lines[i];
    }

    for (int i = 0; i < n; i++)
    {
        for (int j = 0; j < m; j++)
        {
            visits[i][j] = 0;
        }
    }
}

int main(int argc, char *argv[])
{
    int n, m;
    std::cin >> n >> m;
    int visits[n][m];
    std::string lines[2 * n + 1];

    init(lines, visits, n, m);

    // std::vector<point> points;
    // int unvisitedCount = n * m;
    // point current;

    // current.x = 0;
    // current.y = 0;
    // points.push_back(current);

    // print
    for (int i = 0; i < 2 * n + 1; i++)
    {
        std::cout << lines[i] << std::endl;
    }
    return 0;
}