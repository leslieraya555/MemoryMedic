/*
 * File: ProcReader.cpp
 * Project: MemoryMedic
 * Author: Leslie Raya
 *
 * Description:
 * This file reads memory and process information from the Linux /proc
 * filesystem. It collects resident memory, virtual memory, peak memory,
 * thread count, and page-fault counts for a selected process.
 *
 * What must be added:
 * ProcReader.hpp and ProcessSample.hpp must exist in
 * include/memorymedic. This file must be run on Linux because macOS does
 * not provide the Linux /proc process filesystem.
 */

#include "memorymedic/ProcReader.hpp"

#include <chrono>
#include <filesystem>
#include <fstream>
#include <sstream>
#include <stdexcept>
#include <string>
#include <utility>
#include <vector>

namespace memorymedic {

namespace {

/*
 * Returns the current Unix timestamp in milliseconds.
 */
std::int64_t currentTimestampMilliseconds() {
    const auto now = std::chrono::system_clock::now();
    const auto duration = now.time_since_epoch();

    return std::chrono::duration_cast<std::chrono::milliseconds>(
        duration
    ).count();
}

} // namespace

ProcReader::ProcReader(int pid)
    : pid_(pid) {
    if (pid_ <= 0) {
        throw std::invalid_argument(
            "ProcReader requires a positive process ID."
        );
    }
}

int ProcReader::getPid() const {
    return pid_;
}

bool ProcReader::processExists() const {
    const std::filesystem::path processDirectory =
        std::filesystem::path("/proc") / std::to_string(pid_);

    return std::filesystem::exists(processDirectory);
}

/*
 * Reads one numeric value from /proc/<pid>/status.
 *
 * Examples of keys in that file include:
 *   VmRSS:
 *   VmSize:
 *   VmPeak:
 *   Threads:
 */
long ProcReader::readStatusLong(const std::string& key) const {
    const std::string statusPath =
        "/proc/" + std::to_string(pid_) + "/status";

    std::ifstream statusFile(statusPath);

    if (!statusFile.is_open()) {
        throw std::runtime_error(
            "Unable to open process status file: " + statusPath
        );
    }

    std::string line;

    while (std::getline(statusFile, line)) {
        if (line.rfind(key, 0) != 0) {
            continue;
        }

        std::istringstream lineStream(line);
        std::string fieldName;
        long value = 0;

        lineStream >> fieldName >> value;
        return value;
    }

    /*
     * Some fields may be unavailable for a particular process.
     */
    return 0;
}

/*
 * Reads cumulative minor and major page faults from /proc/<pid>/stat.
 *
 * The second field in /proc/<pid>/stat is surrounded by parentheses and
 * may contain spaces, so it is removed before parsing the remaining fields.
 */
std::pair<long, long> ProcReader::readFaultCounts() const {
    const std::string statPath =
        "/proc/" + std::to_string(pid_) + "/stat";

    std::ifstream statFile(statPath);

    if (!statFile.is_open()) {
        throw std::runtime_error(
            "Unable to open process stat file: " + statPath
        );
    }

    std::string line;
    std::getline(statFile, line);

    /*
     * Find the closing parenthesis around the process name.
     */
    const std::size_t closingParenthesis = line.rfind(')');

    if (closingParenthesis == std::string::npos ||
        closingParenthesis + 2 >= line.size()) {
        throw std::runtime_error(
            "The process stat file has an unexpected format."
        );
    }

    /*
     * Everything after ") " begins with stat field 3: process state.
     */
    const std::string remainingFields =
        line.substr(closingParenthesis + 2);

    std::istringstream fieldStream(remainingFields);
    std::vector<std::string> fields;
    std::string field;

    while (fieldStream >> field) {
        fields.push_back(field);
    }

    /*
     * Original stat positions:
     *   Field 10: minor faults
     *   Field 12: major faults
     *
     * Because the vector begins with field 3, their zero-based vector
     * positions are 7 and 9.
     */
    constexpr std::size_t minorFaultIndex = 7;
    constexpr std::size_t majorFaultIndex = 9;

    if (fields.size() <= majorFaultIndex) {
        throw std::runtime_error(
            "The process stat file does not contain enough fields."
        );
    }

    const long minorFaults = std::stol(fields[minorFaultIndex]);
    const long majorFaults = std::stol(fields[majorFaultIndex]);

    return {minorFaults, majorFaults};
}

std::string ProcReader::getProcessName() const {
    const std::string commandPath =
        "/proc/" + std::to_string(pid_) + "/comm";

    std::ifstream commandFile(commandPath);

    if (!commandFile.is_open()) {
        return "unknown";
    }

    std::string processName;
    std::getline(commandFile, processName);

    if (processName.empty()) {
        return "unknown";
    }

    return processName;
}

ProcessSample ProcReader::readSample() const {
    if (!processExists()) {
        throw std::runtime_error(
            "Process " + std::to_string(pid_) + " does not exist."
        );
    }

    ProcessSample sample;

    sample.timestampMs = currentTimestampMilliseconds();
    sample.rssKb = readStatusLong("VmRSS:");
    sample.virtualMemoryKb = readStatusLong("VmSize:");
    sample.peakRssKb = readStatusLong("VmHWM:");
    sample.threadCount = readStatusLong("Threads:");

    const auto [minorFaults, majorFaults] = readFaultCounts();

    sample.minorPageFaults = minorFaults;
    sample.majorPageFaults = majorFaults;

    return sample;
}

} // namespace memorymedic