/*
 * MemoryMedic - Normal Workload
 *
 * Author: Leslie Raya
 * File: normal_workload.cpp
 * Project: MemoryMedic
 *
 * Description:
 * Generates a stable memory workload for testing MemoryMedic.
 * The program allocates 64 MB of memory and repeatedly accesses
 * each memory page without continuously increasing memory usage.
 */


#include <chrono>
#include <iostream>
#include <thread>
#include <unistd.h>
#include <vector>

/*
 * NormalWorkload
 *
 * Creates a stable 64 MB memory allocation and repeatedly accesses it.
 * The program does not continuously allocate additional memory, so
 * MemoryMedic should classify this behavior as normal.
 */
int main() {
    // Print the process ID so MemoryMedic can monitor this program.
    std::cout << "NormalWorkload PID: " << getpid() << std::endl;

    constexpr std::size_t MEMORY_SIZE =
        64ULL * 1024ULL * 1024ULL;

    // Allocate 64 MB once. The size remains stable.
    std::vector<unsigned char> memory(MEMORY_SIZE, 0);

    while (true) {
        /*
         * Touch one byte on every 4 KB memory page.
         * This keeps the pages active and resident in physical memory.
         */
        for (std::size_t index = 0;
             index < memory.size();
             index += 4096) {
            memory[index] ^= 1;
        }

        // Pause to avoid consuming unnecessary CPU resources.
        std::this_thread::sleep_for(
            std::chrono::milliseconds(500)
        );
    }

    return 0;
}