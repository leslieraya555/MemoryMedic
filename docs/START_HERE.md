# Applying the MemoryMedic documentation update

<!-- File: START_HERE.md | Prepared for: Leslie Raya | Updated: October 26, 2026 -->

**Author: Leslie Raya**

The prepared Markdown files provide complete replacements for three existing documents and this update guide. They describe the implemented code and the results already verified. The reviewed source code and CI workflow are from commit `d71ad06`.

## 1. Put each document in its correct location

Copy each complete Markdown block from the supplied instructions into the corresponding VS Code file. The same contents are also available in `MemoryMedic-Final-Documentation.zip`.

| Prepared file | Existing destination on your Mac |
| --- | --- |
| `README.md` | `/Users/leslieitzel/Desktop/MemoryMedic/README.md` |
| `docs/interview_guide.md` | `/Users/leslieitzel/Desktop/MemoryMedic/docs/interview_guide.md` |
| `docs/evaluation_report.md` | `/Users/leslieitzel/Desktop/MemoryMedic/docs/evaluation_report.md` |
| `START_HERE.md` | `/Users/leslieitzel/Desktop/MemoryMedic/START_HERE.md` |

For each row:

1. Use the Copy button on the complete Markdown block for that file.
2. Open the destination file in your MemoryMedic project. Create `START_HERE.md` at the repository root if it does not exist.
3. Check the folder breadcrumb above the editor.
4. Press **Command+A**, then **Command+V** to replace the document contents.
5. Press **Command+S** to save.

The main README and this guide belong at the repository root. Your existing `data/README.md` remains the dataset guide.

Markdown document contents belong in the VS Code editor. The fenced Bash blocks in the following steps are terminal commands. Copy complete command blocks, including line breaks.

## 2. Review the saved documents

Open the root README and use VS Code's Markdown preview with **Command+Shift+V**. Review the headings, tables, commands, and image reference.

The prepared documents include:

- Author attribution to Leslie Raya.
- Correct component responsibilities and the distinction between C++ heuristic scoring and Python inference.
- A fresh-setup collection command with five runs per workload, matching the trainer's minimum.
- Commands and instructions for the 21 Python regression tests.
- The three GitHub Actions jobs and the successful October 23 verification run.
- The saved benchmark's exact run/row split and confusion counts.
- Strict rejection of invalid raw telemetry and causal per-run feature behavior.
- An interview guide based on implemented behavior and clearly identified future work.
- Separate descriptions of historical model evaluation and later functional checks.

The existing historical image at `docs/images/memorymedic-build-test-training-results.png` is referenced by the root README and evaluation report. The newer CI evidence is linked directly to the successful Actions run.

## 3. Check the documentation changes on your Mac

Open the VS Code terminal. The prompt should be your **Mac** prompt, such as `leslieitzel@Leslies-MacBook-Pro`, for these Git commands.

If you are inside Ubuntu, enter `exit` to return to the Mac terminal first.

```bash
cd /Users/leslieitzel/Desktop/MemoryMedic
git status
git diff --check -- README.md docs/interview_guide.md docs/evaluation_report.md START_HERE.md
git diff --stat -- README.md docs/interview_guide.md docs/evaluation_report.md START_HERE.md
```

Check that you are on `main` and that the diff shows the intended documents. Other local changes should be reviewed separately. A successful `git diff --check` produces no output.

If it reports trailing whitespace, open the named file, press **Command+Shift+P**, select **Trim Trailing Whitespace**, save, and repeat the check. The prepared files contain no trailing whitespace.

If there are no differences for a file, compare the editor contents with the prepared version and confirm it was saved at the destination path. Identical saved content legitimately produces no Git difference.

## 4. Stage and check the four documents

In the same Mac terminal:

```bash
git add -- README.md docs/interview_guide.md docs/evaluation_report.md START_HERE.md
git diff --cached --check -- README.md docs/interview_guide.md docs/evaluation_report.md START_HERE.md
git diff --cached --stat -- README.md docs/interview_guide.md docs/evaluation_report.md START_HERE.md
```

Review the file summary. Continue once the whitespace check passes and the files contain the intended updates.

## 5. Commit and push the documentation

```bash
git commit --only -m "Document verified tests and evaluation results" -- README.md docs/interview_guide.md docs/evaluation_report.md START_HERE.md
git push origin main
```

The explicit paths limit this commit to the four documentation files. A successful push prints an update ending with `main -> main`.

If a command reports an error, read that error before continuing. If Git says `nothing to commit` and the files already match the repository, no additional commit is necessary for those identical contents. `Everything up-to-date` means there are no new commits to send; it is not evidence that an unsaved editor change was uploaded.

## 6. Check the updated GitHub pages

1. Open [MemoryMedic](https://github.com/leslieraya555/MemoryMedic) and refresh the page.
2. Confirm the latest commit is your documentation update.
3. Check the root README's tables, diagram, historical image, and documentation links.
4. Open the updated interview guide and evaluation report.
5. Open [Actions](https://github.com/leslieraya555/MemoryMedic/actions) and select the run for the new documentation commit.
6. Confirm C++ Build and Tests, Python Validation, and Shell Script Validation all pass.

The October 23 CI result already verifies the regression-test update. Pushing the documents triggers the normal workflow again. A documentation update does not require recollecting the historical dataset or rerunning model training to preserve the recorded benchmark.

## 7. Check the actual submission requirements

The assignment rubric has not been supplied in this review. Check the official requirements for these items before marking the submission complete:

| Requirement to check | Current position | Action if explicitly required |
| --- | --- | --- |
| K-fold cross-validation | The implementation uses one grouped train/validation/test split. | Add grouped cross-validation on development runs while preserving a separate final test set, execute it, and report actual fold results. |
| Demonstration video | A written demonstration narrative is included in the interview guide. | Record the requested format and duration. |
| Raw data or saved model submission | Generated collections and models are excluded from Git. | Package the requested trusted artifacts with their manifests, evaluation, split, and environment records using the submission method specified. |
| Report format or required sections | Markdown reports are prepared. | Match any required PDF, presentation, naming, or section format. |

Changing a description to say “k-fold” does not implement that method. Its code, split records, and reported measurements must exist before making that claim.

## 8. Optional short demonstration recording

If a video is required or useful for your portfolio, a roughly three-to-five-minute recording can show:

1. **Introduction:** What MemoryMedic monitors and why memory growth can be legitimate.
2. **Workloads:** Stable memory, bursts, bounded caching, and retained allocation.
3. **Operation:** A bounded demonstration producing CSV telemetry.
4. **Prediction:** An existing trusted saved model producing recent labels and probabilities.
5. **Evidence:** The grouped benchmark, 21-test result, and successful CI jobs.
6. **Interpretation:** The synthetic-data limitation and one concrete next experiment.

Use the operational commands in the root README. Check that the VM, project path, Python environment, model, and CSVs exist before recording. Keep original benchmark records when showing later demonstrations.

## 9. Optional experiment that would strengthen an interview

The most useful next measurement is monitoring overhead:

1. Record the Linux version, hardware/VM allocation, compiler/build, workload, duration, and sampling settings.
2. Run repeated comparable baseline trials without MemoryMedic.
3. Run repeated comparable monitored trials, varying trial order.
4. Record target runtime or fixed-duration throughput, plus the monitor's CPU time and peak RSS.
5. Compare conditions and report variation across trials.

For a finite workload, runtime overhead is `(monitored_runtime - baseline_runtime) / baseline_runtime * 100%`. For continuous workloads, define a throughput or fixed-duration resource comparison instead. Treat detection latency and false alerts per hour as separate measurements with explicit definitions.

These measurements remain future work until the experiment is run. The prepared reports do not invent performance values.

## 10. Completion checklist

- [ ] Save the four prepared documents in their mapped repository paths.
- [ ] Confirm the documents describe the verified implementation and preserve historical evaluation identity.
- [ ] Pass the scoped Git whitespace checks.
- [ ] Commit and push the intended documentation changes.
- [ ] Check that GitHub renders the documents, diagram, and image correctly.
- [ ] Confirm the CI run for the documentation commit passes.
- [ ] Compare the repository against the actual submission rubric.
- [ ] Complete any explicitly required cross-validation, recording, or artifact submission.

The working monitor, workload scripts, feature engineering, grouped training/evaluation, predictions, 21-test Python suite, and successful CI have already been demonstrated. This update makes the documentation consistent with that evidence. Further feature development can be planned as a separate phase.