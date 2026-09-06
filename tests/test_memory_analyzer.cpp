/*
 * File: test_memory_analyzer.cpp
 * Project: MemoryMedic
 * Author: Leslie Raya
 *
 * Description:
 * This file contains automated tests for the MemoryAnalyzer class.
 * It creates simulated process-memory measurements and confirms that
 * MemoryMedic correctly identifies stable memory, moderate memory growth,
 * severe memory growth, and recently stabilized memory.
 *
 * What must be added:
 * The following files must already contain their code:
 *
 *   include/memorymedic/MemoryAnalyzer.hpp
 *   include/memorymedic/ProcessSample.hpp
 *   include/memorymedic/RiskAssessment.hpp
 *   src/MemoryAnalyzer.cpp
 *   src/RiskAssessment.cpp
 *
 * This test does not require an external testing library. It uses a small
 * custom test system and returns exit code 0 when every test passes.
 */

#include "memorymedic/MemoryAnalyzer.hpp"
#include "memorymedic/ProcessSample.hpp"
#include "memorymedic/RiskAssessment.hpp"

#include <cmath>
#include <cstdint>
#include <iostream>
#include <string>
#include <vector>

namespace {

/*
 * Counts how many tests pass and fail.
 */
int passedTests = 0;
int failedTests = 0;

/*
 * Creates one simulated process-memory measurement.
 */
memorymedic::ProcessSample makeSample(
    std::int64_t timestampMilliseconds,
    long rssKilobytes
) {
    memorymedic::ProcessSample sample{};

    sample.timestampMs = timestampMilliseconds;
    sample.rssKb = rssKilobytes;

    /*
     * These values are included to make the simulated sample resemble
     * a real Linux process sample. MemoryAnalyzer currently focuses
     * primarily on timestampMs and rssKb.
     */
    sample.virtualMemoryKb = rssKilobytes * 2;
    sample.peakRssKb = rssKilobytes;
    sample.threadCount = 1;
    sample.minorPageFaults = 0;
    sample.majorPageFaults = 0;
    sample.rssGrowthKbPerSecond = 0.0;
    sample.minorFaultsPerSecond = 0.0;
    sample.majorFaultsPerSecond = 0.0;

    return sample;
}

/*
 * Reports whether a Boolean test condition passed.
 */
void expectTrue(
    bool condition,
    const std::string& testName
) {
    if (condition) {
        std::cout << "[PASS] " << testName << '\n';
        ++passedTests;
    } else {
        std::cerr << "[FAIL] " << testName << '\n';
        ++failedTests;
    }
}

/*
 * Compares two decimal values while allowing a small rounding difference.
 */
void expectNear(
    double actual,
    double expected,
    double tolerance,
    const std::string& testName
) {
    const bool passed =
        std::abs(actual - expected) <= tolerance;

    if (passed) {
        std::cout
            << "[PASS] " << testName
            << " (actual: " << actual << ")\n";

        ++passedTests;
    } else {
        std::cerr
            << "[FAIL] " << testName
            << " (expected: " << expected
            << ", actual: " << actual << ")\n";

        ++failedTests;
    }
}

/*
 * Test 1:
 * MemoryAnalyzer should wait for more information when it has fewer
 * than two samples.
 */
void testInsufficientSamples() {
    std::cout << "\nTest 1: Insufficient samples\n";

    memorymedic::MemoryAnalyzer analyzer(5);

    const std::vector<memorymedic::ProcessSample> samples = {
        makeSample(1000, 64000)
    };

    const memorymedic::RiskAssessment result =
        analyzer.analyze(samples);

    expectTrue(
        result.level == memorymedic::RiskLevel::Low,
        "One sample produces a low risk level"
    );

    expectNear(
        result.score,
        0.0,
        0.001,
        "One sample produces a zero risk score"
    );

    expectNear(
        result.growthRateKbPerSecond,
        0.0,
        0.001,
        "One sample produces a zero growth rate"
    );
}

/*
 * Test 2:
 * A process whose RSS remains unchanged should be classified as low risk.
 */
void testStableMemory() {
    std::cout << "\nTest 2: Stable memory\n";

    memorymedic::MemoryAnalyzer analyzer(8);
    std::vector<memorymedic::ProcessSample> samples;

    constexpr long stableMemoryKb = 65536;

    for (int index = 0; index < 8; ++index) {
        samples.push_back(
            makeSample(
                static_cast<std::int64_t>(index) * 1000,
                stableMemoryKb
            )
        );
    }

    const memorymedic::RiskAssessment result =
        analyzer.analyze(samples);

    expectTrue(
        result.level == memorymedic::RiskLevel::Low,
        "Stable memory produces a low risk level"
    );

    expectNear(
        result.growthRateKbPerSecond,
        0.0,
        0.001,
        "Stable memory produces a zero growth rate"
    );

    expectNear(
        result.stability,
        1.0,
        0.001,
        "Stable memory produces maximum stability"
    );

    expectTrue(
        result.score < 25.0,
        "Stable memory produces a risk score below 25"
    );
}

/*
 * Test 3:
 * Memory growing by 250 KB every second should produce a moderate risk.
 */
void testModerateMemoryGrowth() {
    std::cout << "\nTest 3: Moderate memory growth\n";

    memorymedic::MemoryAnalyzer analyzer(8);
    std::vector<memorymedic::ProcessSample> samples;

    constexpr long initialMemoryKb = 50000;
    constexpr long growthPerSecondKb = 250;

    for (int index = 0; index < 8; ++index) {
        samples.push_back(
            makeSample(
                static_cast<std::int64_t>(index) * 1000,
                initialMemoryKb +
                    (growthPerSecondKb * index)
            )
        );
    }

    const memorymedic::RiskAssessment result =
        analyzer.analyze(samples);

    expectTrue(
        result.level == memorymedic::RiskLevel::Moderate,
        "250 KB/s growth produces a moderate risk level"
    );

    expectNear(
        result.growthRateKbPerSecond,
        250.0,
        0.001,
        "The calculated growth rate is 250 KB/s"
    );

    expectNear(
        result.stability,
        1.0,
        0.001,
        "Consistent moderate growth has maximum stability"
    );

    expectTrue(
        result.score >= 25.0 && result.score < 50.0,
        "Moderate growth produces a score from 25 through 49"
    );
}

/*
 * Test 4:
 * A process growing by 1,000 KB every second should be classified as
 * high risk.
 */
void testHighMemoryGrowth() {
    std::cout << "\nTest 4: High memory growth\n";

    memorymedic::MemoryAnalyzer analyzer(8);
    std::vector<memorymedic::ProcessSample> samples;

    constexpr long initialMemoryKb = 50000;
    constexpr long growthPerSecondKb = 1000;

    for (int index = 0; index < 8; ++index) {
        samples.push_back(
            makeSample(
                static_cast<std::int64_t>(index) * 1000,
                initialMemoryKb +
                    (growthPerSecondKb * index)
            )
        );
    }

    const memorymedic::RiskAssessment result =
        analyzer.analyze(samples);

    expectTrue(
        result.level == memorymedic::RiskLevel::High,
        "1,000 KB/s growth produces a high risk level"
    );

    expectNear(
        result.growthRateKbPerSecond,
        1000.0,
        0.001,
        "The calculated growth rate is 1,000 KB/s"
    );

    expectTrue(
        result.score >= 50.0 && result.score < 80.0,
        "High growth produces a score from 50 through 79"
    );
}

/*
 * Test 5:
 * A linear memory leak growing by 4 MB each second should be classified
 * as critical.
 */
void testCriticalLinearLeak() {
    std::cout << "\nTest 5: Critical linear memory leak\n";

    memorymedic::MemoryAnalyzer analyzer(10);
    std::vector<memorymedic::ProcessSample> samples;

    constexpr long initialMemoryKb = 50000;
    constexpr long leakGrowthPerSecondKb = 4096;

    for (int index = 0; index < 10; ++index) {
        samples.push_back(
            makeSample(
                static_cast<std::int64_t>(index) * 1000,
                initialMemoryKb +
                    (leakGrowthPerSecondKb * index)
            )
        );
    }

    const memorymedic::RiskAssessment result =
        analyzer.analyze(samples);

    expectTrue(
        result.level == memorymedic::RiskLevel::Critical,
        "A 4 MB/s linear leak produces a critical risk level"
    );

    expectNear(
        result.growthRateKbPerSecond,
        4096.0,
        0.001,
        "The linear leak growth rate is 4,096 KB/s"
    );

    expectNear(
        result.stability,
        1.0,
        0.001,
        "A consistent linear leak has maximum stability"
    );

    expectTrue(
        result.score >= 80.0,
        "A severe linear leak produces a score of at least 80"
    );
}

/*
 * Test 6:
 * Negative memory growth means the process is releasing memory and should
 * therefore be classified as low risk.
 */
void testDecreasingMemory() {
    std::cout << "\nTest 6: Decreasing memory\n";

    memorymedic::MemoryAnalyzer analyzer(8);
    std::vector<memorymedic::ProcessSample> samples;

    constexpr long initialMemoryKb = 80000;
    constexpr long decreasePerSecondKb = 500;

    for (int index = 0; index < 8; ++index) {
        samples.push_back(
            makeSample(
                static_cast<std::int64_t>(index) * 1000,
                initialMemoryKb -
                    (decreasePerSecondKb * index)
            )
        );
    }

    const memorymedic::RiskAssessment result =
        analyzer.analyze(samples);

    expectTrue(
        result.level == memorymedic::RiskLevel::Low,
        "Decreasing memory produces a low risk level"
    );

    expectNear(
        result.growthRateKbPerSecond,
        -500.0,
        0.001,
        "The calculated memory decrease is 500 KB/s"
    );
}

/*
 * Test 7:
 * The analyzer should use only the most recent samples in its configured
 * analysis window. Old growth should not continue causing a high-risk result
 * after recent memory usage becomes stable.
 */
void testRecentAnalysisWindow() {
    std::cout << "\nTest 7: Recent analysis window\n";

    memorymedic::MemoryAnalyzer analyzer(5);
    std::vector<memorymedic::ProcessSample> samples;

    /*
     * Older samples show rapid growth.
     */
    samples.push_back(makeSample(0, 10000));
    samples.push_back(makeSample(1000, 20000));
    samples.push_back(makeSample(2000, 30000));
    samples.push_back(makeSample(3000, 40000));

    /*
     * The five most recent samples are stable.
     */
    samples.push_back(makeSample(4000, 50000));
    samples.push_back(makeSample(5000, 50000));
    samples.push_back(makeSample(6000, 50000));
    samples.push_back(makeSample(7000, 50000));
    samples.push_back(makeSample(8000, 50000));

    const memorymedic::RiskAssessment result =
        analyzer.analyze(samples);

    expectTrue(
        result.level == memorymedic::RiskLevel::Low,
        "Recent stable memory produces a low risk level"
    );

    expectNear(
        result.growthRateKbPerSecond,
        0.0,
        0.001,
        "The analyzer ignores growth outside the recent window"
    );
}

/*
 * Test 8:
 * Each RiskLevel value should be converted to the correct CSV text.
 */
void testRiskLevelText() {
    std::cout << "\nTest 8: Risk-level text\n";

    expectTrue(
        memorymedic::toString(memorymedic::RiskLevel::Low) == "low",
        "Low converts to low"
    );

    expectTrue(
        memorymedic::toString(
            memorymedic::RiskLevel::Moderate
        ) == "moderate",
        "Moderate converts to moderate"
    );

    expectTrue(
        memorymedic::toString(
            memorymedic::RiskLevel::High
        ) == "high",
        "High converts to high"
    );

    expectTrue(
        memorymedic::toString(
            memorymedic::RiskLevel::Critical
        ) == "critical",
        "Critical converts to critical"
    );
}

} // namespace

int main() {
    std::cout << "========================================\n";
    std::cout << "MemoryMedic MemoryAnalyzer Tests\n";
    std::cout << "Author: Leslie Raya\n";
    std::cout << "========================================\n";

    testInsufficientSamples();
    testStableMemory();
    testModerateMemoryGrowth();
    testHighMemoryGrowth();
    testCriticalLinearLeak();
    testDecreasingMemory();
    testRecentAnalysisWindow();
    testRiskLevelText();

    std::cout << "\n========================================\n";
    std::cout << "Test results\n";
    std::cout << "Passed: " << passedTests << '\n';
    std::cout << "Failed: " << failedTests << '\n';
    std::cout << "========================================\n";

    if (failedTests > 0) {
        std::cerr << "Some MemoryMedic tests failed.\n";
        return 1;
    }

    std::cout << "All MemoryMedic tests passed.\n";
    return 0;
}