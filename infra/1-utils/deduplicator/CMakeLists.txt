cmake_minimum_required(VERSION 3.10)
project(Deduplicator)

# Set C++17 as the standard for the project
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED True)

# Client executable
add_executable(client src/client.cpp src/db.cpp src/hash.cpp src/traverse.cpp)

# Server executable
add_executable(server src/server.cpp src/listen.cpp)

# Find Boost with the filesystem component
find_package(Boost 1.75 REQUIRED COMPONENTS filesystem)
include_directories(${Boost_INCLUDE_DIRS})
target_link_libraries(client ${Boost_LIBRARIES})
target_link_libraries(server ${Boost_LIBRARIES})

# Find SQLite3 library
find_library(SQLITE3_LIBRARY NAMES sqlite3)
target_link_libraries(client ${SQLITE3_LIBRARY})
target_link_libraries(server ${SQLITE3_LIBRARY})

# Find OpenSSL and link it
find_package(OpenSSL REQUIRED)
include_directories(${OpenSSL_INCLUDE_DIRS})
target_link_libraries(client ${OpenSSL_LIBRARIES})
target_link_libraries(server ${OpenSSL_LIBRARIES})
