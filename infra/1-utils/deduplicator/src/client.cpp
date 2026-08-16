#include <string>
#include <csignal>
#include <chrono>

#include "db.h"
#include "hash.h"
#include "traverse.h"

long long last_ctrl_c = 0;
bool ctrl_c_awaits = false;

void signalHandler(int signum)
{
    auto now = std::chrono::system_clock::now();
    long long ms = std::chrono::duration_cast<std::chrono::milliseconds>(now.time_since_epoch()).count();

    if (ms - last_ctrl_c > 700)
    {
        last_ctrl_c = ms;
        ctrl_c_awaits = true;
    }
    else
    {
        exit(0);
    }
}

int main()
{
    signal(SIGINT, signalHandler);

    std::string db_path = "./files.db";
    std::string index_path = "/System/";

    init_db(db_path);
    index(index_path, ctrl_c_awaits);

    return 0;
}