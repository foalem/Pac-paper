# PaC-Repo Analysis (Pac-paper)

This repository contains tools and data for collecting, enriching, and analyzing GitHub repositories that contain Policy-as-Code (PaC) and related Infrastructure-as-Code (IaC) artifacts. The primary entry point is `main.py`, a command-line tool that orchestrates data collection, enrichment, and extraction tasks.

Key features
- Collect GitHub repositories relevant to PaC and IaC.
- Enrich repository data with metrics, IaC/policy detection, cloud provider signals, and README/policy extraction.
- Clone repositories locally for deeper analysis and scanning.
- Support for multiple policy formats (rego, sentinel, pulumi, kyverno, cedar, custodian, etc.).

Repository layout
- `main.py` - CLI entrypoint that exposes the core workflows (see "Usage" below).
- `data_collection/` - Python modules that implement repository collection, enrichment, scanning, cloning, and extraction.
- `data/` - CSV outputs and intermediate datasets produced by scripts.
- `data_analysis/` - Jupyter notebooks and analysis artifacts. Several notebooks demonstrate data analysis workflows and experiments using large language models (LLMs) to assist with labeling, classification, and exploratory analysis. (See "Notebooks and experiments" below.)
- `output/` - Directory for generated outputs by scripts.
- `config/` - Configuration and constants used by the scripts.
- `progress/` - Progress tracking JSON files used by incremental enrichment routines.
- `policies/` - Extracted policy files and policy-related artifacts.
- `logging_file.log` - Log file used by the scripts.

Notebooks and experiments
Inside the `data_analysis/` folder you will find Jupyter notebooks that perform exploratory data analysis and show examples of using LLMs (for example, for classification, label disambiguation, and README/policy summarization). These notebooks include experiment notes, intermediate outputs, and visualizations used during research.

Requirements and setup
- Python 3.8+ recommended.
- Install dependencies (if a requirements file exists in the project root). If there is no requirements file, install commonly used packages as needed: pandas, openpyxl, requests, PyGithub, and Jupyter.

Example (PowerShell)
To run the main CLI script from the project root:

```powershell
# Collect repositories (DATA)
python main.py -c

# Collect repository metrics (METRICS)
python main.py -m

# Enrich CSV with IaC tool detections (IAC)
python main.py -i

# Process cloud provider repositories (CLOUD)
python main.py -cd

# Search/enrich PaC repositories (PAC)
python main.py -p

# Clone all repositories listed in a CSV (ALL)
python main.py -a

# Scan repositories for PaC usage (USAGE)
python main.py -u

# Save README files from repositories locally (README)
python main.py -r

# Extract and save policy files from repositories (OUTPUT)
python main.py -o
```

Notes about flags
The flags and their meanings are implemented in `main.py` and map to functions inside `data_collection/` modules. See the top of `main.py` for the exact flag names and supported workflows.

Important files produced by the workflows
- `progress/enrich_repos_4.json` - progress tracking file used by incremental enrichment routines.
- `logging_file.log` - append-only logs of runs.
- `data/*.csv` - many CSV outputs containing discovered PaC/IaC artifacts.


Contact / Further notes
This README provides a quick orientation based on the `main.py` entrypoint and the repository layout. For deeper understanding, open the notebooks in `data_analysis/`, inspect `data_collection/` modules, and run the CLI flags you need to reproduce parts of the analysis.


