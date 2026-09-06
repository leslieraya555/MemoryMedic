/*
 * File: MemoryMedic.hpp
 * Project: MemoryMedic
 * Author: Leslie Raya
 *
 * Description:
 * Declares the main MemoryMedic application and its configuration.
 * MemoryMedic coordinates process monitoring, memory analysis, live status
 * output, and CSV telemetry logging.
 */

#pragma once

#include "memorymedic/MemoryAnalyzer.hpp"
#include "memorymedic/ProcReader.hpp"
#include "memorymedic/ProcessSample.hpp"
#include "memorymedic/RiskAssessment.hpp"
#include "memorymedic/TelemetryLogger.hpp"

#include <cstddef>
#include <string>
#include <vector>

namespace memorymedic {

/*
 * Stores the command-line settings used during one monitoring run.
 */
struct MonitorConfig {
    // Linux process ID to monitor.
    int pid = -1;

    // Delay between measurements in milliseconds.
    int intervalMs = 1000;

    // Number of recent samples used by MemoryAnalyzer.
    std::size_t windowSize = 30;

    // CSV file that will receive the telemetry measurements.
    std::string outputFile = "telemetry.csv";

    /*
     * Ground-truth machine-learning label.
     * Supported values are normal, leak, and unknown.
     */
    std::string label = "unknown";

    // Unique name identifying the monitoring experiment.
    std::string runId = "manual";

    // Prevents live status lines from appearing when true.
    bool quiet = false;
};

class MemoryMedic {
public:
    /*
     * Creates the MemoryMedic application using the supplied configuration.
     */
    explicit MemoryMedic(MonitorConfig configuration);

    /*
     * Starts monitoring and continues until the selected process exits.
     *
     * Returns:
     *   0 when monitoring completes successfully.
     *   1 when monitoring cannot start or encounters an error.
     */
    int run();

private:
    // User-selected monitoring options.
    MonitorConfig config_;

    // Reads raw process information from the Linux /proc filesystem.
    ProcReader reader_;

    // Analyzes the recent process-memory history.
    MemoryAnalyzer analyzer_;

    // Writes measurements and analysis results to a CSV file.
    TelemetryLogger logger_;

    // Stores recent process measurements.
    std::vector<ProcessSample> history_;

    /*
     * Calculates RSS growth and page-fault rates by comparing the newest
     * sample with the preceding sample.
     */
    void enrichRates(ProcessSample& currentSample) const;

    /*
     * Displays one live monitoring result unless quiet mode is enabled.
     */
    void displayStatus(
        const ProcessSample& sample,
        const RiskAssessment& assessment
    ) const;
};

} // namespace memorymedic