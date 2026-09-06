/*
 * File: MemoryAnalyzer.hpp
 * Project: MemoryMedic
 * Author: Leslie Raya
 *
 * Description:
 * Declares the MemoryAnalyzer class. MemoryAnalyzer examines recent
 * process-memory measurements, estimates the rate of memory growth, measures
 * the stability of that growth, and returns a risk assessment.
 */

#pragma once

#include "memorymedic/ProcessSample.hpp"
#include "memorymedic/RiskAssessment.hpp"

#include <cstddef>
#include <vector>

namespace memorymedic {

class MemoryAnalyzer {
public:
    /*
     * Creates an analyzer that examines the most recent windowSize samples.
     */
    explicit MemoryAnalyzer(std::size_t windowSize = 30);

    /*
     * Analyzes recent memory measurements and returns the estimated
     * memory-leak risk.
     */
    RiskAssessment analyze(
        const std::vector<ProcessSample>& samples
    ) const;

private:
    // Maximum number of recent measurements used in one analysis.
    std::size_t windowSize_;

    /*
     * Uses linear regression to calculate the overall resident-memory
     * growth rate in kilobytes per second.
     */
    double calculateLinearSlopeKbPerSecond(
        const std::vector<ProcessSample>& samples
    ) const;

    /*
     * Measures whether the process is growing consistently or experiencing
     * temporary, irregular memory spikes.
     */
    double calculateStability(
        const std::vector<ProcessSample>& samples
    ) const;
};

} // namespace memorymedic