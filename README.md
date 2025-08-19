# RNA‑seq Analysis Workflow Demo

This repository demonstrates a step‑by‑step analysis of **RNA‑seq data**, from raw sequencing files through to differential expression results and visualisation.  The workflow is inspired by our study of unique molecular mechanisms underlying postharvest senescence in broccoli, but it can be adapted to any RNA‑seq experiment.

Unlike a traditional Jupyter notebook, the workflow is encapsulated in a single Python script (`rna_seq_workflow.py`) that combines shell commands, R code and Python code.  This script illustrates each stage of the pipeline, from downloading raw reads on an HPC cluster through to exploring differential expression results interactively.  Realistic file names and directory paths (e.g. `/home/utsab/projects/rnaseq/raw_data`) are used throughout to help you tailor the commands to your own environment.

## Repository structure

```
rnaseq_interactive_demo/
├── README.md             # This file
├── rna_seq_workflow.py   # Python script
``` with step‑by‑step analysis
├── streamlit_app.py      # Streamlit app to explore DE results
├── requirements.txt      # Python dependencies for the workflow and Streamlit
└── LICENSE               # MIT licence
```

### Workflow overview

The `rna_seq_workflow.py` script walks through the following major steps:

1. **Data retrieval** – Use the SRA Toolkit (`prefetch` and `fastq‑dump`) to download raw FASTQ files from the NCBI Sequence Read Archive.  Example directories and file names (e.g. `/home/utsab/projects/rnaseq/raw_data/SRR1234567_1.fastq.gz`) mirror those used in our study.
2. **Quality control** – Run FastQC on the raw reads and summarise reports using MultiQC.
3. **Trimming** – Remove adapters and low‑quality bases with Trim Galore.
4. **Alignment** – Build a STAR genome index and align trimmed reads to a reference genome.
5. **Quantification** – Count reads per gene with featureCounts (part of the Subread package).
6. **Differential expression analysis** – Switch to R (edgeR/limma‑voom) to normalise counts, define your experimental design, and test contrasts.  The script prints a ready‑to‑run R script that you can copy into an R session.
7. **Visualisation and exploration** – Use Python and Plotly to generate an interactive volcano plot and summarise differential expression results.  A Streamlit app is provided for easy browsing of the results.

Each stage includes realistic HPC paths and explanatory comments, allowing you to adapt the workflow to your own system.

### Streamlit app

For a lightweight web interface, the repository includes a minimal `streamlit_app.py`.  After running the workflow and exporting differential expression results to CSV (e.g. `DE_results_36h_vs_0h.csv`), you can launch the app locally with:

```bash
pip install -r requirements.txt
streamlit run streamlit_app.py
```

The app displays an interactive volcano plot and a searchable, sortable table of the differential expression results.

### Requirements

To reproduce the Python parts of the analysis (interactive plots and Streamlit app), install the required packages:

```bash
pip install -r requirements.txt
```

For the full pipeline you’ll also need command‑line tools (SRA Toolkit, FastQC, MultiQC, Trim Galore, STAR, Subread) and an R installation with the `edgeR`, `limma` and `ggplot2` packages.  See the notebook for details.

### Licence

This project is licensed under the MIT licence (see the [LICENSE](LICENSE) file for details).
