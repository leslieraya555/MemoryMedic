/*
 * File: RiskAssessment.hpp
 * Project: MemoryMedic
 * Author: Leslie Raya
 *
 * Description:
 * Defines the result produced by MemoryAnalyzer. A risk assessment contains
 * a risk category, numerical score, memory-growth rate, stability score,
 * and a readable explanation.
 */

#pragma once

#include <string>

namespace memorymedic {

/*
 * Represents the four memory-leak risk categories used by MemoryMedic.
 */
enum class RiskLevel {
    Low,
    Moderate,
    High,
    Critical
};

/*
 * Contains the complete result of one memory-risk analysis.
 */
struct RiskAssessment {
    // Human-readable risk category.
    RiskLevel level = RiskLevel::Low;

    // Numerical risk score from 0 through 100.
    double score = 0.0;

    // Estimated long-term RSS growth rate.
    double growthRateKbPerSecond = 0.0;

    /*
     * Indicates how consistent the memory growth is.
     * 0.0 represents unstable growth.
     * 1.0 represents highly consistent growth.
     */
    double stability = 0.0;

    // Explanation of the result.
    std::string explanation;
};

/*
 * Converts a RiskLevel value into text for Terminal and CSV output.
 */
std::string toString(RiskLevel level);

} // namespace memorymedic