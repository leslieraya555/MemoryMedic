/*
 * File: ProcessSample.hpp
 * Project: MemoryMedic
 * Author: Leslie Raya
 *
 * Description:
 * Defines the ProcessSample structure used to store one process-memory
 * measurement. ProcReader creates these samples, MemoryAnalyzer analyzes
 * them, and TelemetryLogger writes them to CSV files.
 */

#pragma once

#include <cstdint>

namespace memorymedic {

/*
 * Represents one process measurement collected from the Linux /proc
 * filesystem.
 */
struct ProcessSample {
    // Unix timestamp indicating when the sample was collected.
    std::int64_t timestampMs = 0;

    // Resident Set Size: physical memory currently held in RAM.
    long rssKb = 0;

    // Total virtual address space assigned to the process.
    long virtualMemoryKb = 0;

    // Highest resident-memory measurement observed by the operating system.
    long peakRssKb = 0;

    // Number of threads currently owned by the process.
    long threadCount = 0;

    // Total minor page faults since the process started.
    long minorPageFaults = 0;

    // Total major page faults since the process started.
    long majorPageFaults = 0;

    // Estimated resident-memory growth in kilobytes per second.
    double rssGrowthKbPerSecond = 0.0;

    // Estimated number of minor page faults per second.
    double minorFaultsPerSecond = 0.0;

    // Estimated number of major page faults per second.
    double majorFaultsPerSecond = 0.0;
};

} // namespace memorymedic