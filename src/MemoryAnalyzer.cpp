/*
 * File: MemoryAnalyzer.cpp
 * Project: MemoryMedic
 * Author: Leslie Raya
 *
 * Description:
 * This file analyzes a window of process-memory samples. It calculates the
 * rate of RSS memory growth using linear regression and determines how
 * consistent that growth is. The resulting measurements are converted into
 * a risk score and risk level.
 *
 * What must be added:
 * MemoryAnalyzer.hpp, ProcessSample.hpp, and RiskAssessment.hpp must exist
 * in include/memorymedic.
 */

#include "memorymedic/MemoryAnalyzer.hpp"

#include <algorithm>
#include <cmath>
#include <numeric>
#include <string>
#include <vector>

namespace memorymedic {

MemoryAnalyzer::MemoryAnalyzer(std::size_t windowSize)
    : windowSize_(std::max<std::size_t>(windowSize, 2)) {
}

/*
 * Calculates a best-fit line through the memory samples.
 *
 * The result is returned in kilobytes per second.
 */
double MemoryAnalyzer::calculateLinearSlopeKbPerSecond(
    const std::vector<ProcessSample>& samples
) const {
    if (samples.size() < 2) {
        return 0.0;
    }

    const double firstTimestamp =
        static_cast<double>(samples.front().timestampMs);

    double sumX = 0.0;
    double sumY = 0.0;
    double sumXY = 0.0;
    double sumXX = 0.0;

    for (const ProcessSample& sample : samples) {
        /*
         * Convert elapsed milliseconds into seconds.
         */
        const double timeSeconds =
            (static_cast<double>(sample.timestampMs) - firstTimestamp) /
            1000.0;

        const double rssKilobytes =
            static_cast<double>(sample.rssKb);

        sumX += timeSeconds;
        sumY += rssKilobytes;
        sumXY += timeSeconds * rssKilobytes;
        sumXX += timeSeconds * timeSeconds;
    }

    const double sampleCount =
        static_cast<double>(samples.size());

    const double denominator =
        (sampleCount * sumXX) - (sumX * sumX);

    if (std::abs(denominator) < 0.000001) {
        return 0.0;
    }

    return (
        (sampleCount * sumXY) - (sumX * sumY)
    ) / denominator;
}

/*
 * Measures how consistent the individual memory-growth rates are.
 *
 * A result near 1.0 represents consistent growth.
 * A result near 0.0 represents unstable or bursty growth.
 */
double MemoryAnalyzer::calculateStability(
    const std::vector<ProcessSample>& samples
) const {
    if (samples.size() < 3) {
        return 0.0;
    }

    std::vector<double> growthRates;
    growthRates.reserve(samples.size() - 1);

    for (std::size_t index = 1; index < samples.size(); ++index) {
        const ProcessSample& previous = samples[index - 1];
        const ProcessSample& current = samples[index];

        const double elapsedSeconds =
            static_cast<double>(
                current.timestampMs - previous.timestampMs
            ) / 1000.0;

        if (elapsedSeconds <= 0.0) {
            continue;
        }

        const double memoryDifference =
            static_cast<double>(current.rssKb - previous.rssKb);

        growthRates.push_back(memoryDifference / elapsedSeconds);
    }

    if (growthRates.empty()) {
        return 0.0;
    }

    const double meanGrowth =
        std::accumulate(
            growthRates.begin(),
            growthRates.end(),
            0.0
        ) / static_cast<double>(growthRates.size());

    /*
     * Near-zero growth is considered stable normal behavior.
     */
    if (std::abs(meanGrowth) < 1.0) {
        return 1.0;
    }

    double squaredDifferenceSum = 0.0;

    for (const double growthRate : growthRates) {
        const double difference = growthRate - meanGrowth;
        squaredDifferenceSum += difference * difference;
    }

    const double variance =
        squaredDifferenceSum /
        static_cast<double>(growthRates.size());

    const double standardDeviation = std::sqrt(variance);

    /*
     * The coefficient of variation compares the deviation with the
     * magnitude of the mean growth rate.
     */
    const double coefficientOfVariation =
        standardDeviation / std::abs(meanGrowth);

    return std::clamp(
        1.0 - coefficientOfVariation,
        0.0,
        1.0
    );
}

RiskAssessment MemoryAnalyzer::analyze(
    const std::vector<ProcessSample>& samples
) const {
    RiskAssessment assessment;

    if (samples.size() < 2) {
        assessment.level = RiskLevel::Low;
        assessment.score = 0.0;
        assessment.growthRateKbPerSecond = 0.0;
        assessment.stability = 0.0;
        assessment.explanation =
            "Collecting additional samples before evaluating memory growth.";

        return assessment;
    }

    /*
     * Analyze only the most recent configured number of samples.
     */
    const std::size_t firstSampleIndex =
        samples.size() > windowSize_
            ? samples.size() - windowSize_
            : 0;

    const std::vector<ProcessSample> analysisWindow(
        samples.begin() + static_cast<std::ptrdiff_t>(firstSampleIndex),
        samples.end()
    );

    const double growthRate =
        calculateLinearSlopeKbPerSecond(analysisWindow);

    const double stability =
        calculateStability(analysisWindow);

    double riskScore = 0.0;
    RiskLevel riskLevel = RiskLevel::Low;
    std::string explanation;

    /*
     * Convert the measured growth rate into an initial risk score.
     *
     * These thresholds can be adjusted later after evaluating real
     * MemoryMedic datasets.
     */
    if (growthRate < 100.0) {
        riskScore = 10.0;
        riskLevel = RiskLevel::Low;
        explanation =
            "Memory usage is stable or growing very slowly.";
    } else if (growthRate < 500.0) {
        riskScore = 35.0;
        riskLevel = RiskLevel::Moderate;
        explanation =
            "Memory usage is increasing and should be observed.";
    } else if (growthRate < 2000.0) {
        riskScore = 70.0;
        riskLevel = RiskLevel::High;
        explanation =
            "Memory usage shows sustained high growth.";
    } else {
        riskScore = 95.0;
        riskLevel = RiskLevel::Critical;
        explanation =
            "Memory usage shows extremely rapid sustained growth.";
    }

    /*
     * Consistent growth is more characteristic of a leak than a temporary
     * burst. Unstable growth receives a slightly lower risk score.
     */
    const double stabilityMultiplier =
        0.75 + (0.25 * stability);

    riskScore *= stabilityMultiplier;
    riskScore = std::clamp(riskScore, 0.0, 100.0);

    /*
     * Recalculate the final category after the stability adjustment.
     */
    if (riskScore < 25.0) {
        riskLevel = RiskLevel::Low;
    } else if (riskScore < 50.0) {
        riskLevel = RiskLevel::Moderate;
    } else if (riskScore < 80.0) {
        riskLevel = RiskLevel::High;
    } else {
        riskLevel = RiskLevel::Critical;
    }

    assessment.level = riskLevel;
    assessment.score = riskScore;
    assessment.growthRateKbPerSecond = growthRate;
    assessment.stability = stability;
    assessment.explanation = explanation;

    return assessment;
}

} // namespace memorymedic