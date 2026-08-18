cmake_minimum_required(VERSION 3.10)

project(simple_chess VERSION 0.1)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED True)

add_compile_options(-O3)

find_package(Boost REQUIRED COMPONENTS system filesystem thread)
include_directories(${Boost_INCLUDE_DIR})

target_link_libraries(${PROJECT_NAME} Boost::system Boost::filesystem Boost::thread)

add_executable(${PROJECT_NAME} src/main.cpp)