/*
 * File: TelemetryLogger.hpp
 * Project: MemoryMedic
 * Author: Leslie Raya
 *
 * Description:
 * Declares the TelemetryLogger class. TelemetryLogger writes process-memory
 * measurements, risk assessments, ground-truth labels, and run identifiers
 * into CSV files for later analysis and machine-learning training.
 */

#pragma once

#include "memorymedic/ProcessSample.hpp"
#include "memorymedic/RiskAssessment.hpp"

#include <fstream>
#include <string>

namespace memorymedic {

class TelemetryLogger {
public:
    /*
     * Opens or creates the specified CSV output file.
     */
    explicit TelemetryLogger(const std::string& fileName);

    /*
     * Writes one complete telemetry measurement to the CSV file.
     */
    void log(
        const ProcessSample& sample,
        const RiskAssessment& assessment,
        const std::string& label,
        const std::string& runId
    );

private:
    // File stream used to append rows to the telemetry CSV.
    std::ofstream outputFile_;
};

} // namespace memorymedic