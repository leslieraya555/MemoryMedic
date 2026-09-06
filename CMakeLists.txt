# File: CMakeLists.txt
# Project: MemoryMedic
# Author: Leslie Raya
#
# Description:
# Configures the MemoryMedic C++ project. This file builds the main
# monitoring program, four example workloads, and the automated tests.

cmake_minimum_required(VERSION 3.20)

project(
    MemoryMedic
    VERSION 1.0.0
    DESCRIPTION "Linux process memory monitoring and leak detection"
    LANGUAGES CXX
)

# MemoryMedic requires C++17 for filesystem support and other features.
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

# Export compilation information for VS Code and other development tools.
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)

# Enable standard CMake testing support.
include(CTest)

# Find the platform thread library used by std::thread.
find_package(Threads REQUIRED)

# ------------------------------------------------------------
# MemoryMedic core library
# ------------------------------------------------------------

add_library(
    memorymedic_core
    src/ProcReader.cpp
    src/MemoryAnalyzer.cpp
    src/RiskAssessment.cpp
    src/TelemetryLogger.cpp
    src/MemoryMedic.cpp
)

# Allow source files to include headers using:
# #include "memorymedic/HeaderName.hpp"
target_include_directories(
    memorymedic_core
    PUBLIC
        ${PROJECT_SOURCE_DIR}/include
)

target_link_libraries(
    memorymedic_core
    PUBLIC
        Threads::Threads
)

# Enable useful compiler warnings.
if(MSVC)
    target_compile_options(
        memorymedic_core
        PRIVATE
            /W4
    )
else()
    target_compile_options(
        memorymedic_core
        PRIVATE
            -Wall
            -Wextra
            -Wpedantic
    )
endif()

# ------------------------------------------------------------
# Main MemoryMedic command-line application
# ------------------------------------------------------------

add_executable(
    memorymedic
    src/main.cpp
)

target_link_libraries(
    memorymedic
    PRIVATE
        memorymedic_core
)

# ------------------------------------------------------------
# Example process workloads
# ------------------------------------------------------------

add_executable(
    normal_workload
    workloads/NormalWorkload.cpp
)

add_executable(
    linear_leak
    workloads/LinearLeak.cpp
)

add_executable(
    burst_workload
    workloads/BurstWorkload.cpp
)

add_executable(
    cache_growth
    workloads/CacheGrowth.cpp
)

target_link_libraries(
    normal_workload
    PRIVATE
        Threads::Threads
)

target_link_libraries(
    linear_leak
    PRIVATE
        Threads::Threads
)

target_link_libraries(
    burst_workload
    PRIVATE
        Threads::Threads
)

target_link_libraries(
    cache_growth
    PRIVATE
        Threads::Threads
)

# Apply compiler warnings to the example workloads.
if(MSVC)
    target_compile_options(normal_workload PRIVATE /W4)
    target_compile_options(linear_leak PRIVATE /W4)
    target_compile_options(burst_workload PRIVATE /W4)
    target_compile_options(cache_growth PRIVATE /W4)
else()
    target_compile_options(
        normal_workload
        PRIVATE -Wall -Wextra -Wpedantic
    )

    target_compile_options(
        linear_leak
        PRIVATE -Wall -Wextra -Wpedantic
    )

    target_compile_options(
        burst_workload
        PRIVATE -Wall -Wextra -Wpedantic
    )

    target_compile_options(
        cache_growth
        PRIVATE -Wall -Wextra -Wpedantic
    )
endif()

# ------------------------------------------------------------
# Automated tests
# ------------------------------------------------------------

if(BUILD_TESTING)
    add_executable(
        test_memory_analyzer
        tests/test_memory_analyzer.cpp
    )

    target_link_libraries(
        test_memory_analyzer
        PRIVATE
            memorymedic_core
    )

    if(MSVC)
        target_compile_options(
            test_memory_analyzer
            PRIVATE /W4
        )
    else()
        target_compile_options(
            test_memory_analyzer
            PRIVATE -Wall -Wextra -Wpedantic
        )
    endif()

    add_test(
        NAME MemoryAnalyzerTests
        COMMAND test_memory_analyzer
    )
endif()

# ------------------------------------------------------------
# Installation
# ------------------------------------------------------------

install(
    TARGETS memorymedic
    RUNTIME DESTINATION bin
)