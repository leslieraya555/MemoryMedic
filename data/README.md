# MemoryMedic Dataset

**Project:** MemoryMedic
**Author:** Leslie Raya

## Description

This directory stores process-memory telemetry collected by MemoryMedic.

The CSV files in this directory are used to train and evaluate the
MemoryMedic machine-learning model. Each CSV file represents one independent
monitoring experiment.

The measurements should be generated automatically by MemoryMedic. Do not
manually type measurements into the CSV files.

## Dataset categories

### Normal workload

Files beginning with `normal_` contain processes with stable memory usage.

Examples:

- `normal_01.csv`
- `normal_02.csv`
- `normal_03.csv`

The machine-learning label for these files is:

```text
normal