/*
 * File: main.cpp
 * Project: MemoryMedic
 * Author: Leslie Raya
 *
 * Description:
 * This file is the command-line entry point for MemoryMedic. It reads the
 * arguments supplied by the user, validates them, creates the monitoring
 * configuration, and starts the MemoryMedic application.
 *
 * What must be added:
 * The MemoryMedic.hpp header must exist in include/memorymedic.
 */

#include "memorymedic/MemoryMedic.hpp"

#include <exception>
#include <iostream>
#include <stdexcept>
#include <string>

namespace {

/*
 * Displays instructions explaining how to start MemoryMedic.
 */
void printUsage(const char* programName) {
    std::cout
        << "MemoryMedic - Linux Process Memory Monitor\n\n"
        << "Usage:\n"
        << "  " << programName << " monitor [options]\n\n"
        << "Required option:\n"
        << "  --pid <number>          Process ID to monitor\n\n"
        << "Optional arguments:\n"
        << "  --interval-ms <number>  Sampling interval in milliseconds\n"
        << "  --window <number>       Number of samples in the analysis window\n"
        << "  --out <file>            CSV output file\n"
        << "  --label <value>         Ground-truth label: normal, leak, or unknown\n"
        << "  --run-id <value>        Unique experiment identifier\n"
        << "  --quiet                 Do not print live status information\n"
        << "  --help                  Display this message\n\n"
        << "Example:\n"
        << "  " << programName
        << " monitor --pid 1234 --out data/test.csv "
        << "--label normal --run-id test_01\n";
}

/*
 * Verifies that a label is one of the supported dataset labels.
 */
bool isValidLabel(const std::string& label) {
    return label == "normal" ||
           label == "leak" ||
           label == "unknown";
}

/*
 * Returns the value following a command-line option.
 */
std::string requireValue(
    int& index,
    int argumentCount,
    char* argumentValues[],
    const std::string& option
) {
    if (index + 1 >= argumentCount) {
        throw std::invalid_argument(
            "Missing value after command-line option: " + option
        );
    }

    ++index;
    return argumentValues[index];
}

} // namespace

int main(int argc, char* argv[]) {
    /*
     * MemoryMedic requires at least the "monitor" command.
     */
    if (argc < 2) {
        printUsage(argv[0]);
        return 1;
    }

    const std::string command = argv[1];

    if (command == "--help" || command == "-h") {
        printUsage(argv[0]);
        return 0;
    }

    if (command != "monitor") {
        std::cerr << "Error: Unknown command: " << command << '\n';
        printUsage(argv[0]);
        return 1;
    }

    memorymedic::MonitorConfig config;

    try {
        /*
         * Read every option appearing after the "monitor" command.
         */
        for (int index = 2; index < argc; ++index) {
            const std::string option = argv[index];

            if (option == "--pid") {
                config.pid = std::stoi(
                    requireValue(index, argc, argv, option)
                );
            } else if (option == "--interval-ms") {
                config.intervalMs = std::stoi(
                    requireValue(index, argc, argv, option)
                );
            } else if (option == "--window") {
                config.windowSize = static_cast<std::size_t>(
                    std::stoul(requireValue(index, argc, argv, option))
                );
            } else if (option == "--out") {
                config.outputFile =
                    requireValue(index, argc, argv, option);
            } else if (option == "--label") {
                config.label =
                    requireValue(index, argc, argv, option);
            } else if (option == "--run-id") {
                config.runId =
                    requireValue(index, argc, argv, option);
            } else if (option == "--quiet") {
                config.quiet = true;
            } else if (option == "--help" || option == "-h") {
                printUsage(argv[0]);
                return 0;
            } else {
                throw std::invalid_argument(
                    "Unknown command-line option: " + option
                );
            }
        }

        /*
         * Validate the completed configuration before monitoring begins.
         */
        if (config.pid <= 0) {
            throw std::invalid_argument(
                "A positive process ID is required. Use --pid <number>."
            );
        }

        if (config.intervalMs <= 0) {
            throw std::invalid_argument(
                "The sampling interval must be greater than zero."
            );
        }

        if (config.windowSize < 2) {
            throw std::invalid_argument(
                "The analysis window must contain at least two samples."
            );
        }

        if (config.outputFile.empty()) {
            throw std::invalid_argument(
                "The CSV output filename cannot be empty."
            );
        }

        if (!isValidLabel(config.label)) {
            throw std::invalid_argument(
                "The label must be normal, leak, or unknown."
            );
        }

        /*
         * Start the process-monitoring application.
         */
        memorymedic::MemoryMedic application(config);
        return application.run();

    } catch (const std::exception& error) {
        std::cerr << "MemoryMedic error: " << error.what() << '\n';
        return 1;
    }
}