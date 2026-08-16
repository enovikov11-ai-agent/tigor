#include <iostream>
#include <filesystem>
#include <string>
#include <vector>

#include "flags.h"

namespace fs = std::filesystem;

void index(std::string root_path, bool &ctrl_c_awaits)
{
    std::vector<std::string> paths = {root_path};
    std::vector<std::string> nextPaths;

    int level = 0;

    while (!paths.empty())
    {
        std::cout << "Level: " << level << ", paths: " << paths.size() << std::endl;

        for (std::string &path : paths)
        {
            if (ctrl_c_awaits)
            {
                ctrl_c_awaits = false;
                std::cout << "Current: " << path << std::endl;
            }

            try
            {
                if (fs::is_symlink(path))
                    continue;

                if (fs::is_directory(path))
                {
                    for (auto &entry : fs::directory_iterator(path))
                        nextPaths.push_back(entry.path());
                }
                else if (fs::is_regular_file(path))
                {
                    auto file_size = fs::file_size(path);

                    auto ftime = fs::last_write_time(path);
                    auto sctp = std::chrono::time_point_cast<std::chrono::system_clock::duration>(
                        ftime - fs::file_time_type::clock::now() + std::chrono::system_clock::now());
                    time_t file_last_modified = std::chrono::system_clock::to_time_t(sctp);

                    if (DD_LOG)
                        std::cout << path << " " << file_size << " " << file_last_modified << std::endl;
                }
            }
            catch (const fs::filesystem_error &e)
            {
                if (DD_DEBUG)
                    std::cerr << e.what() << std::endl;
            }
        }

        paths = nextPaths;
        nextPaths = {};
        level++;
    }
}