/*
 * File: CacheGrowth.cpp
 * Project: MemoryMedic
 * Author: Leslie Raya
 *
 * Description:
 * Simulates an application cache by allocating 8 MB every second for
 * 16 seconds. The cache grows to approximately 128 MB and then stops
 * growing while the process continues running.
 *
 * Purpose:
 * Provides another hard-negative example. Cache growth can initially
 * resemble a leak, but a healthy bounded cache eventually reaches a
 * stable plateau. This helps MemoryMedic distinguish bounded growth
 * from continuous pathological growth.
 *
 * Expected dataset label: normal
 */

#include <chrono>
#include <cstddef>
#include <iostream>
#include <thread>
#include <unistd.h>
#include <vector>

int main() {
    // Print the process ID so MemoryMedic can monitor this program.
    std::cout << "CacheGrowth PID: " << getpid() << std::endl;

    constexpr std::size_t CACHE_CHUNK_SIZE =
        8ULL * 1024ULL * 1024ULL;

    constexpr int NUMBER_OF_CHUNKS = 16;

    /*
     * Each inner vector represents one cache entry.
     * Sixteen 8 MB entries create a maximum cache size of 128 MB.
     */
    std::vector<std::vector<unsigned char>> cache;
    cache.reserve(NUMBER_OF_CHUNKS);

    for (int chunk = 0; chunk < NUMBER_OF_CHUNKS; ++chunk) {
        // Add and initialize another 8 MB cache entry.
        cache.emplace_back(CACHE_CHUNK_SIZE, 1);

        std::cout
            << "Cache size: "
            << (chunk + 1) * 8
            << " MB"
            << std::endl;

        // Simulate gradual cache growth.
        std::this_thread::sleep_for(
            std::chrono::seconds(1)
        );
    }

    std::cout
        << "Cache reached its 128 MB limit and is now stable."
        << std::endl;

    /*
     * Keep the program running without allocating more memory.
     * Memory usage should remain at a stable plateau.
     */
    while (true) {
        std::this_thread::sleep_for(
            std::chrono::seconds(1)
        );
    }

    return 0;
}