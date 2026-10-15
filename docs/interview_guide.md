# MemoryMedic — Interview Guide

## 1. Project Overview

### What is MemoryMedic?

MemoryMedic is a Linux memory-behavior monitoring and anomaly-detection
system.

It collects process-level memory telemetry, analyzes how memory changes
over time, and uses machine-learning models to distinguish potentially
abnormal memory growth from normal application behavior.

The main goal is not simply to detect high memory usage. The goal is to
detect suspicious memory behavior while reducing false positives caused
by legitimate behavior such as caching or temporary allocation spikes.


## 2. What Problem Does It Solve?

Traditional memory monitoring can tell us that a process is using a lot
of memory, but high memory usage does not automatically mean that a
program has a memory leak.

For example:

- A database may intentionally use RAM for caching.
- An ML application may load a large model into memory.
- A program may temporarily allocate memory and later release it.
- A genuine leak may slowly increase memory consumption for hours.

MemoryMedic looks at behavior over time rather than relying on one
memory measurement.


## 3. System Architecture

The basic pipeline is:

Linux Process
     |
     v
/proc/<pid>
     |
     v
ProcReader
     |
     v
ProcessSample
     |
     v
MemoryAnalyzer
     |
     +----------------+
     |                |
     v                v
RiskAssessment   TelemetryLogger
                      |
                      v
                  CSV Dataset
                      |
                      v
              Feature Engineering
                      |
                      v
                ML Classifier


## 4. What Does Each Major Class Do?

### ProcessSample

Represents one snapshot of a Linux process.

Examples of information stored:

- RSS
- virtual memory
- peak RSS
- thread count
- minor page faults
- major page faults
- timestamp


### ProcReader

Reads process information from Linux `/proc`.

For example:

/proc/<pid>/status
/proc/<pid>/stat

It converts the operating-system information into ProcessSample objects.


### MemoryAnalyzer

Analyzes multiple ProcessSample objects over time.

It calculates features such as:

- RSS growth rate
- memory slope
- page-fault rate
- sustained memory growth

It produces a RiskAssessment.


### TelemetryLogger

Stores process measurements and calculated features in CSV files.

Those files can later become training data for the ML system.


### MemoryMedic

Coordinates the monitoring system.

It connects:

ProcReader
    ->
MemoryAnalyzer
    ->
TelemetryLogger


## 5. Important Operating-System Concepts

### What is virtual memory?

Virtual memory is the address space that a process can access.

A process can have a large virtual address space without all of that
memory currently existing in physical RAM.


### What is RSS?

RSS stands for Resident Set Size.

It represents memory pages belonging to the process that are currently
resident in physical memory.

Therefore:

Virtual memory != physical memory currently resident in RAM.


### What is a page fault?

A page fault occurs when a process accesses a virtual-memory page that
cannot immediately be satisfied by the current page-table mapping.

A page fault does not automatically mean something went wrong.


### Minor vs. major page faults

A minor page fault can usually be resolved without reading the page from
disk.

A major page fault requires substantially more expensive I/O to obtain
the needed page.


## 6. Why Use /proc?

I used /proc for the first implementation because Linux exposes useful
per-process statistics through it.

Advantages:

- relatively simple
- widely available on Linux
- easy to prototype
- no kernel module required
- appropriate for periodic process-level monitoring

A limitation is that /proc provides snapshots.

If I need much more detailed event-level information, eBPF becomes an
interesting extension.


## 7. Why eBPF?

I would not add eBPF simply because it sounds more advanced.

The reason to introduce eBPF would be to collect event-driven kernel
telemetry that periodic /proc polling cannot provide efficiently or
precisely enough.

I would compare the additional information against:

- implementation complexity
- CPU overhead
- memory overhead
- detection improvement

If eBPF does not materially improve the system, the simpler collector
may be the better engineering decision.


## 8. How Did You Collect Training Data?

I created controlled workloads representing different memory behaviors.

Examples:

NormalWorkload
    Stable/normal memory behavior

LinearLeak
    Intentionally retains allocations to produce persistent growth

BurstWorkload
    Allocates a large amount of memory temporarily and releases it

CacheGrowth
    Intentionally grows memory before stabilizing

MemoryMedic monitors these processes and records telemetry.

Because I control the workload, I know the approximate ground-truth
behavior associated with each experimental run.


## 9. Why Create Multiple Workloads?

One of the biggest problems with anomaly detection is false positives.

A simplistic detector might conclude:

memory increasing = memory leak

That is incorrect.

CacheGrowth and BurstWorkload intentionally create situations where
memory increases without representing the same behavior as a persistent
leak.

These workloads make the classification problem more realistic.


## 10. Why Machine Learning?

A rule such as:

RSS > threshold

isn't enough because applications have very different memory behavior.

Instead, ML can consider several signals simultaneously, including:

- RSS growth
- growth duration
- page-fault behavior
- virtual-memory changes
- memory trend
- thread count

The model can learn combinations of signals associated with suspicious
behavior.


## 11. Why Not Deep Learning?

This problem begins as relatively small structured/tabular telemetry.

A neural network would add complexity without automatically producing a
better system.

I would first establish strong baselines with simpler models.

Only if experiments showed that more complex temporal models produced a
meaningful improvement would I consider deep learning.


## 12. Why Logistic Regression?

Logistic regression provides a useful baseline.

Advantages include:

- fast training
- inexpensive inference
- relatively interpretable
- easy to debug

If a complicated model barely outperforms logistic regression, the
simpler model may be preferable.


## 13. Why Gradient Boosting?

MemoryMedic also evaluates gradient boosting because it can model
nonlinear relationships between telemetry features.

For example, high RSS growth alone may not indicate a problem.

But:

high sustained RSS growth
+
specific fault behavior
+
lack of stabilization

may be considerably more suspicious.

Tree-based boosting can capture interactions like these.


## 14. How Did You Prevent Training/Test Leakage?

Samples from the same monitoring run are highly correlated.

Randomly splitting individual rows could put neighboring samples from
the same experiment into both training and testing.

That would make evaluation look better than it actually is.

Instead, I group samples using run_id and split entire experimental runs
between training and testing.

This creates a more realistic evaluation.


## 15. How Did You Evaluate the Model?

I examine metrics such as:

Precision
Recall
F1 score
ROC-AUC
Average Precision

I would also evaluate system-specific metrics such as:

- false alarms per monitoring hour
- detection latency
- detection lead time
- CPU overhead
- memory overhead


## 16. What Causes False Positives?

Possible causes include:

- legitimate caching
- temporary memory spikes
- application startup
- loading large datasets
- loading ML models
- memory-mapped files
- garbage-collection behavior
- unusual but legitimate workloads

That is why MemoryMedic should analyze temporal behavior instead of
treating high memory usage as automatically abnormal.


## 17. How Do You Measure Monitoring Overhead?

The monitoring system itself consumes resources.

I would benchmark the target workload:

1. Without MemoryMedic running.
2. With MemoryMedic running.
3. At different sampling frequencies.

I would compare:

- CPU utilization
- memory consumption
- runtime
- I/O
- sampling latency

This allows me to quantify the cost introduced by monitoring.


## 18. What Was the Hardest Engineering Problem?

One of the hardest conceptual problems is distinguishing abnormal memory
growth from legitimate growth.

Detecting increasing memory is relatively easy.

Determining whether that growth represents a real problem is much more
difficult.

That is why I designed multiple workloads and analyze behavior over
time.


## 19. What Would You Improve Next?

My next improvements would include:

1. Add an eBPF telemetry collector.
2. Benchmark eBPF against /proc polling.
3. Add native C++ model inference.
4. Expand the workload dataset.
5. Test real open-source applications.
6. Add container-aware monitoring.
7. Measure detection latency and monitoring overhead.
8. Add automated CI testing.
9. Improve model explainability.
10. Investigate online/streaming anomaly detection.


## 20. Biggest Limitation

The initial training data comes from controlled synthetic workloads.

That is useful for developing and validating the architecture, but it
does not prove that the detector generalizes to every real application.

A stronger evaluation would test MemoryMedic against diverse,
real-world applications and known memory-leak bugs.


## 21. 30-Second Interview Explanation

MemoryMedic is a Linux memory-behavior monitoring system I built to
combine operating-systems engineering with machine learning.

It collects process telemetry from Linux, including resident and virtual
memory information and page-fault statistics. Instead of simply
triggering when memory usage becomes high, it analyzes how memory
changes over time.

I built controlled normal, leak, burst, and cache-growth workloads to
generate labeled experiments. I then use those experiments to evaluate
ML classifiers while keeping complete experimental runs separated
between training and testing.

The larger goal is to determine whether behavioral telemetry can detect
abnormal memory growth while minimizing false positives and keeping the
monitoring overhead low.


## 22. Questions I Should Be Ready to Answer

- What exactly is a memory leak?
- What is RSS?
- What is virtual memory?
- What is the difference between RSS and VmSize?
- What causes a page fault?
- What is the difference between minor and major page faults?
- Why did you use Linux /proc?
- Why would you use eBPF?
- Why didn't you start with eBPF?
- How did you generate your dataset?
- How do you know your labels are correct?
- What features does your model use?
- Why did you choose your ML models?
- Why didn't you use deep learning?
- How did you prevent data leakage?
- What causes false positives?
- What causes false negatives?
- How do you measure monitoring overhead?
- How do you evaluate the ML model?
- How would this scale to thousands of processes?
- What happens if a PID disappears while being monitored?
- What are the limitations of your current implementation?
- What would you build next?


** You want to eventually be able to look at something like:

“Why /proc instead of eBPF?”

and explain the tradeoff yourself.

That's exactly what can make this project useful for getting into OS/systems + ML engineering. You're showing that you can discuss memory management, Linux internals, data collection, ML evaluation, performance overhead, experimental design, and engineering tradeoffs in the same project.

And as you actually build MemoryMedic, I'd keep updating this guide. If you run an experiment and discover that your model has a 12% false-positive rate on cache-heavy workloads, for example, that real result belongs in here. Real measurements will make your interview answers much stronger than hypothetical ones.**