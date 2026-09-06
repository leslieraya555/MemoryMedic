/*
 * File: MemoryMedic.cpp
 * Project: MemoryMedic
 * Author: Leslie Raya
 *
 * Description:
 * This file controls the main monitoring loop. It repeatedly reads process
 * telemetry, calculates memory and page-fault rates, runs the risk analyzer,
 * writes a CSV row, and displays live information in the Terminal.
 *
 * What must be added:
 * MemoryMedic.hpp, ProcReader.hpp, MemoryAnalyzer.hpp, TelemetryLogger.hpp,
 * ProcessSample.hpp, and RiskAssessment.hpp must exist in
 * include/memorymedic.
 */

#include "memorymedic/MemoryMedic.hpp"

#include <algorithm>
#include <chrono>
#include <iomanip>
#include <iostream>
#include <thread>
#include <utility>

namespace memorymedic {

MemoryMedic::MemoryMedic(MonitorConfig configuration)
    : config_(std::move(configuration)),
      reader_(config_.pid),
      analyzer_(config_.windowSize),
      logger_(config_.outputFile) {
}

/*
 * Calculates rates by comparing the current sample with the previous sample.
 */
void MemoryMedic::enrichRates(ProcessSample& currentSample) const {
    if (history_.empty()) {
        currentSample.rssGrowthKbPerSecond = 0.0;
        currentSample.minorFaultsPerSecond = 0.0;
        currentSample.majorFaultsPerSecond = 0.0;
        return;
    }

    const ProcessSample& previousSample = history_.back();

    const double elapsedSeconds =
        static_cast<double>(
            currentSample.timestampMs - previousSample.timestampMs
        ) / 1000.0;

    if (elapsedSeconds <= 0.0) {
        currentSample.rssGrowthKbPerSecond = 0.0;
        currentSample.minorFaultsPerSecond = 0.0;
        currentSample.majorFaultsPerSecond = 0.0;
        return;
    }

    currentSample.rssGrowthKbPerSecond =
        static_cast<double>(
            currentSample.rssKb - previousSample.rssKb
        ) / elapsedSeconds;

    currentSample.minorFaultsPerSecond =
        static_cast<double>(
            currentSample.minorPageFaults -
            previousSample.minorPageFaults
        ) / elapsedSeconds;

    currentSample.majorFaultsPerSecond =
        static_cast<double>(
            currentSample.majorPageFaults -
            previousSample.majorPageFaults
        ) / elapsedSeconds;
}

/*
 * Prints one live status line unless the --quiet option was supplied.
 */
void MemoryMedic::displayStatus(
    const ProcessSample& sample,
    const RiskAssessment& assessment
) const {
    if (config_.quiet) {
        return;
    }

    std::cout
        << "PID " << config_.pid
        << " | RSS: " << sample.rssKb << " KB"
        << " | Growth: "
        << std::fixed << std::setprecision(2)
        << assessment.growthRateKbPerSecond << " KB/s"
        << " | Stability: "
        << assessment.stability
        << " | Risk: "
        << toString(assessment.level)
        << " (" << assessment.score << "/100)"
        << " | " << assessment.explanation
        << '\n';
}

int MemoryMedic::run() {
    if (!reader_.processExists()) {
        std::cerr
            << "Error: Process " << config_.pid
            << " does not exist.\n";

        return 1;
    }

    if (!config_.quiet) {
        std::cout
            << "MemoryMedic is monitoring process "
            << reader_.getProcessName()
            << " with PID " << config_.pid << ".\n"
            << "Telemetry will be saved to: "
            << config_.outputFile << '\n'
            << "Press Control+C to stop monitoring.\n\n";
    }

    /*
     * Continue until the selected process exits.
     */
    while (reader_.processExists()) {
        const auto iterationStart =
            std::chrono::steady_clock::now();

        try {
            /*
             * Collect raw Linux process information.
             */
            ProcessSample sample = reader_.readSample();

            /*
             * Calculate instantaneous rates from the previous sample.
             */
            enrichRates(sample);

            /*
             * Add the sample to the monitoring history.
             */
            history_.push_back(sample);

            /*
             * Keep enough history for the analyzer without allowing the
             * vector to grow forever during long monitoring sessions.
             */
            const std::size_t maximumHistorySize =
                std::max<std::size_t>(
                    config_.windowSize * 4,
                    120
                );

            if (history_.size() > maximumHistorySize) {
                const std::size_t numberToRemove =
                    history_.size() - maximumHistorySize;

                history_.erase(
                    history_.begin(),
                    history_.begin() +
                        static_cast<std::ptrdiff_t>(numberToRemove)
                );
            }

            /*
             * Analyze the recent memory history.
             */
            const RiskAssessment assessment =
                analyzer_.analyze(history_);

            /*
             * Store the analyzer's regression-based growth rate in the
             * telemetry row.
             */
            sample.rssGrowthKbPerSecond =
                assessment.growthRateKbPerSecond;

            logger_.log(
                sample,
                assessment,
                config_.label,
                config_.runId
            );

            displayStatus(sample, assessment);

        } catch (const std::exception& error) {
            /*
             * A process can disappear between processExists() and
             * readSample(). Treat that condition as a clean stop.
             */
            if (!reader_.processExists()) {
                break;
            }

            std::cerr
                << "Monitoring error: "
                << error.what() << '\n';

            return 1;
        }

        /*
         * Wait until the configured interval has elapsed. Subtracting the
         * processing time prevents each interval from becoming longer than
         * requested.
         */
        const auto nextIteration =
            iterationStart +
            std::chrono::milliseconds(config_.intervalMs);

        std::this_thread::sleep_until(nextIteration);
    }

    if (!config_.quiet) {
        std::cout
            << "\nProcess " << config_.pid
            << " has exited. Monitoring complete.\n";
    }

    return 0;
}

} // namespace memorymedic