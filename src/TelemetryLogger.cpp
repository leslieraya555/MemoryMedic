/*
 * File: TelemetryLogger.cpp
 * Project: MemoryMedic
 * Author: Leslie Raya
 *
 * Description:
 * This file writes process measurements and risk-assessment results to a
 * CSV file. The generated files become the dataset used by the MemoryMedic
 * machine-learning scripts.
 *
 * What must be added:
 * TelemetryLogger.hpp, ProcessSample.hpp, and RiskAssessment.hpp must exist
 * in include/memorymedic. The output folder is created automatically when
 * it does not already exist.
 */

#include "memorymedic/TelemetryLogger.hpp"

#include <filesystem>
#include <iomanip>
#include <stdexcept>
#include <string>

namespace memorymedic {

TelemetryLogger::TelemetryLogger(const std::string& fileName) {
    const std::filesystem::path outputPath(fileName);
    const std::filesystem::path parentDirectory =
        outputPath.parent_path();

    /*
     * Create the output directory, such as data/, when necessary.
     */
    if (!parentDirectory.empty()) {
        std::filesystem::create_directories(parentDirectory);
    }

    bool writeHeader = true;

    if (std::filesystem::exists(outputPath) &&
        std::filesystem::is_regular_file(outputPath) &&
        std::filesystem::file_size(outputPath) > 0) {
        writeHeader = false;
    }

    outputFile_.open(
        outputPath,
        std::ios::out | std::ios::app
    );

    if (!outputFile_.is_open()) {
        throw std::runtime_error(
            "Unable to open telemetry output file: " + fileName
        );
    }

    /*
     * Write the CSV column names only when the file is new or empty.
     */
    if (writeHeader) {
        outputFile_
            << "timestamp_ms,"
            << "rss_kb,"
            << "virtual_memory_kb,"
            << "peak_rss_kb,"
            << "threads,"
            << "minor_page_faults,"
            << "major_page_faults,"
            << "rss_growth_kb_s,"
            << "minor_faults_s,"
            << "major_faults_s,"
            << "risk_score,"
            << "risk_level,"
            << "label,"
            << "run_id\n";

        outputFile_.flush();
    }
}

void TelemetryLogger::log(
    const ProcessSample& sample,
    const RiskAssessment& assessment,
    const std::string& label,
    const std::string& runId
) {
    outputFile_
        << sample.timestampMs << ','
        << sample.rssKb << ','
        << sample.virtualMemoryKb << ','
        << sample.peakRssKb << ','
        << sample.threadCount << ','
        << sample.minorPageFaults << ','
        << sample.majorPageFaults << ','
        << std::fixed << std::setprecision(3)
        << sample.rssGrowthKbPerSecond << ','
        << sample.minorFaultsPerSecond << ','
        << sample.majorFaultsPerSecond << ','
        << assessment.score << ','
        << toString(assessment.level) << ','
        << label << ','
        << runId << '\n';

    /*
     * Flush each row so collected data is preserved if monitoring is
     * stopped with Control+C.
     */
    outputFile_.flush();
}

} // namespace memorymedic