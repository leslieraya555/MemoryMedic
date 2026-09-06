/*
 * File: BurstWorkload.cpp
 * Project: MemoryMedic
 * Author: Leslie Raya
 *
 * Description:
 * Temporarily allocates 256 MB of memory, holds it for four seconds,
 * releases it, and waits four seconds before repeating. Memory usage
 * rises sharply but returns to its earlier level.
 *
 * Purpose:
 * Provides a hard-negative example. A temporary memory spike may look
 * suspicious, but it is not an actual leak because the memory is released.
 * This workload helps reduce false-positive leak detections.
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
    std::cout << "BurstWorkload PID: " << getpid() << std::endl;

    constexpr std::size_t BURST_SIZE =
        256ULL * 1024ULL * 1024ULL;

    while (true) {
        /*
         * The allocation exists only inside this scope.
         * It will be released when the closing brace is reached.
         */
        {
            std::vector<unsigned char> burst(BURST_SIZE, 0);

            /*
             * Touch every 4 KB page so the allocation appears in
             * resident physical memory.
             */
            for (std::size_t index = 0;
                 index < burst.size();
                 index += 4096) {
                burst[index] = 1;
            }

            // Hold the temporary allocation for four seconds.
            std::this_thread::sleep_for(
                std::chrono::seconds(4)
            );
        }

        /*
         * At this point, the vector has been destroyed and its memory
         * has been released. Wait before creating the next burst.
         */
        std::this_thread::sleep_for(
            std::chrono::seconds(4)
        );
    }

    return 0;
}