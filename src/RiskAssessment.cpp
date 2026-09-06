/*
 * File: RiskAssessment.cpp
 * Project: MemoryMedic
 * Author: Leslie Raya
 *
 * Description:
 * This file converts MemoryMedic risk-level values into readable text.
 * The text is displayed in the Terminal and written to the telemetry CSV.
 *
 * What must be added:
 * RiskAssessment.hpp must exist in include/memorymedic.
 */

#include "memorymedic/RiskAssessment.hpp"

namespace memorymedic {

std::string toString(RiskLevel level) {
    switch (level) {
        case RiskLevel::Low:
            return "low";

        case RiskLevel::Moderate:
            return "moderate";

        case RiskLevel::High:
            return "high";

        case RiskLevel::Critical:
            return "critical";
    }

    return "unknown";
}

} // namespace memorymedic