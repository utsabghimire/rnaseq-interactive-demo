# RNA‑seq Analysis Workflow Demo

This repository contains an interactive notebook that illustrates the **end‑to‑end analysis of RNA‑seq data**, from raw sequencing files through to differential expression results and visualisation.  

The workflow is based on the analysis performed in our study of unique molecular mechanisms underlying postharvest senescence in broccoli.  It demonstrates how to download raw data, perform quality control and trimming on a high‑performance computing (HPC) cluster, align reads to a reference genome, generate gene counts, and carry out differential expression analysis in R.  Finally, it shows how to visualise and explore the results interactively in Python.

## Repository structure

```
rnaseq_interactive_demo/
├── README.md              # This file
├── rna_seq_workflow.ipynb # Jupyter notebook with step‑by‑step analysis
├── streamlit_app.py       # Simple Streamlit app to explore DE results
├── requirements.txt       # Python dependencies for the notebook/Streamlit
└── LICENSE                # MIT licence
```

### Notebook overview

The notebook walks through the following major steps:

1. **Data retrieval** – download raw FASTQ files from NCBI’s SRA using `prefetch` and `fastq‑dump`.
2. **Quality control** – run FastQC and summarise reports with MultiQC.
3. **Trimming** – remove adapters and low‑quality bases with Trim Galore.
4. **Alignment** – build a reference index and align reads to it using STAR.
5. **Quantification** – count reads per gene with featureCounts.
6. **Differential expression analysis** – import counts into R/edgeR, normalise, build a design matrix, and test contrasts using limma‑voom.
7. **Visualisation and exploration** – create a volcano plot in R and load results into Python for interactive exploration with Plotly and Streamlit.

Throughout the notebook you’ll see realistic file names and HPC paths (e.g. `/home/utsab/projects/rnaseq/raw_data`), so you can adapt the commands to your own environment.  Code cells include both shell commands (for use on an HPC login node) and R/Python code.  Comments explain the purpose of each step.

### Streamlit app

For a lightweight web interface, the repository also includes a minimal `streamlit_app.py`.  After running the notebook and exporting differential expression results to CSV, you can launch the app locally with:

```bash
pip install -r requirements.txt
streamlit run streamlit_app.py
```

The app displays the full DE results table and allows basic filtering and sorting via the Streamlit interface.

### Requirements

To reproduce the Python parts of the analysis (interactive plots and Streamlit app), install the required packages:

```bash
pip install -r requirements.txt
```

For the full pipeline you’ll also need command‑line tools (SRA Toolkit, FastQC, MultiQC, Trim Galore, STAR, Subread) and an R installation with the `edgeR`, `limma` and `ggplot2` packages.  See the notebook for details.

### Licence

This project is licensed under the MIT licence (see the [LICENSE](LICENSE) file for details).
