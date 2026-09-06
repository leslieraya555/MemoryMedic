/*
 * File: LinearLeak.cpp
 * Project: MemoryMedic
 * Author: Leslie Raya
 *
 * Description:
 * Intentionally allocates 1 MB of memory every 500 milliseconds without
 * releasing it. Each allocation is touched so that Linux commits the
 * memory to physical pages. The process grows by approximately 2 MB
 * every second.
 *
 * Purpose:
 * Creates a controlled and predictable memory leak that MemoryMedic can
 * use as positive training data. The steady increase helps the detector
 * learn the difference between unbounded memory growth and normal usage.
 *
 * Expected dataset label: leak
 *
 * Safety:
 * This is an intentional test workload. Run it only for controlled
 * experiments and stop it after data collection.
 */

#include <chrono>
#include <cstddef>
#include <iostream>
#include <thread>
#include <unistd.h>
#include <vector>

int main() {
    // Print the process ID so MemoryMedic can monitor this program.
    std::cout << "LinearLeak PID: " << getpid() << std::endl;

    constexpr std::size_t CHUNK_SIZE =
        1ULL * 1024ULL * 1024ULL;

    /*
     * Store every allocated pointer so the program continues holding
     * the allocated memory. The blocks are intentionally not deleted.
     */
    std::vector<unsigned char*> leakedBlocks;

    while (true) {
        // Intentionally allocate another 1 MB block.
        unsigned char* block = new unsigned char[CHUNK_SIZE];

        /*
         * Touch one byte from every 4 KB page so the allocation affects
         * resident physical memory instead of only virtual memory.
         */
        for (std::size_t index = 0;
             index < CHUNK_SIZE;
             index += 4096) {
            block[index] = 1;
        }

        // Keep the pointer so the memory remains allocated.
        leakedBlocks.push_back(block);

        // Allocate approximately 2 MB per second.
        std::this_thread::sleep_for(
            std::chrono::milliseconds(500)
        );
    }

    return 0;
}