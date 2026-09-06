/*
 * File: ProcReader.hpp
 * Project: MemoryMedic
 * Author: Leslie Raya
 *
 * Description:
 * Declares the ProcReader class. ProcReader collects memory, thread, and
 * page-fault information for a Linux process by reading its files under
 * /proc/<pid>.
 *
 * Important:
 * This component requires Linux. It will be compiled and executed inside
 * the Ubuntu Multipass environment.
 */

#pragma once

#include "memorymedic/ProcessSample.hpp"

#include <string>
#include <utility>

namespace memorymedic {

class ProcReader {
public:
    /*
     * Creates a process reader for the supplied Linux process ID.
     */
    explicit ProcReader(int pid);

    /*
     * Reads and returns the latest process-memory measurement.
     */
    ProcessSample readSample() const;

    /*
     * Reads the process name from /proc/<pid>/comm.
     */
    std::string getProcessName() const;

    /*
     * Returns true while the process directory still exists.
     */
    bool processExists() const;

    /*
     * Returns the monitored process ID.
     */
    int getPid() const;

private:
    // Linux process ID monitored by this reader.
    int pid_;

    /*
     * Reads a numeric entry from /proc/<pid>/status.
     *
     * Examples include VmRSS, VmSize, VmHWM, and Threads.
     */
    long readStatusLong(const std::string& key) const;

    /*
     * Reads the cumulative minor and major page-fault counts from
     * /proc/<pid>/stat.
     */
    std::pair<long, long> readFaultCounts() const;
};

} // namespace memorymedic