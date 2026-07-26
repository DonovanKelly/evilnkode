# Evilnkode Project

This README provides instructions for setting up and running the `evilnkode` project using Conda, activating the environment, and executing the provided CLI scripts. It also covers how to access help for command-line options.

## Prerequisites

- **Conda**: Ensure you have Conda installed (Miniconda or Anaconda). Download from [conda.io](https://conda.io).

## Setting Up the Environment

To set up the project environment using the provided `environment.yaml` file, follow these steps:

1. **Install the environment**:
   - Ensure you are in the project root directory where `environment.yaml` is located.
   - Run the following command to create the `evilnkode` environment:
     ```bash
     conda env create -f environment.yaml
     ```
   - This will install all dependencies specified in `environment.yaml`.

## Activating the Environment

To activate the `evilnkode` environment, run:

```bash
conda activate evilnkode
```

Once activated, your terminal prompt should change to include `(evilnkode)`, indicating the environment is active.

## Running CLI Scripts

The project includes CLI scripts for visualizing nKode observations, benchmarking
shuffle strategies, and comparing challenge-subset attacks.

For a plain-language explanation and correctness audit of the tower shuffle,
the current four-icon flow, and the proposed 3-of-6 experiment, see
[`docs/tower-shuffle-and-challenge-subsets.md`](docs/tower-shuffle-and-challenge-subsets.md).

### Running `cli.visualnkode`

To execute the `visualnkode` CLI script:

```bash
python -m cli.visualnkode
```

- This command runs the `visualnkode` module from the `cli` package.
- To view available options and arguments, use the `-help` flag:
  ```bash
  python -m cli.visualnkode -help
  ```

### Running `cli.benchmark_histogram`

To execute the `benchmark_histogram` CLI script:

```bash
python -m cli.benchmark_histogram
```

- This command runs the `benchmark_histogram` module, which may generate output such as benchmark results or histograms. For example, it might produce output like:
  ```
  File exists: output/slidingtowershufflekeypad-6-8-4-5-4-4-10000/benchmark/slidingtowershufflekeypad-6-8-4-5-4-4-10000.pkl
  Bench SlidingTowerShuffle Break 4
  Bench SlidingTowerShuffle Replay 4
  ```
- To view available options and arguments, use the `-help` flag:
  ```bash
  python -m cli.benchmark_histogram -help
  ```

### Comparing 3-of-6 challenge subsets

To compare `RandomShuffleKeypad` with the production-style tower shuffle:

```bash
python -m cli.challenge_subset_benchmark
```

The default experiment runs 10,000 paired trials on a 6-key × 9-icon layout.
Each login selects three distinct positions from a six-icon secret and presents
them in ascending order. The attacker receives three guesses before lockout.

Results are written beneath `output/challenge-subset/` and include:

- a Markdown report;
- JSON and CSV data;
- crack and guaranteed-replay distributions;
- an optimal three-try next-login success curve.

Use a smaller run while iterating:

```bash
python -m cli.challenge_subset_benchmark --run-count 100 --overwrite
```

View all configuration options with:

```bash
python -m cli.challenge_subset_benchmark --help
```

## Using the `-help` Flag

Both CLI scripts (`cli.visualnkode` and `cli.benchmark_histogram`) support a `-help` flag to display available command-line options and their descriptions. Run the following to explore options for each script:

```bash
python -m cli.visualnkode -help
python -m cli.benchmark_histogram -help
```

This will provide detailed information about parameters, flags, and usage for each script.

## Project Structure

Key files and directories in the project:

- `environment.yaml`: Conda environment configuration file.
- `cli/`: Contains CLI scripts (`visualnkode` and `benchmark_histogram`).
- `output/`: Directory where script outputs, such as benchmark results, are stored.
- `src/`: Source code for the project.
- `tests/`: Test scripts for the project.
- `requirements.txt`: Additional dependencies (if needed outside Conda).

For further details, explore the project documentation in the `docs/` directory.
