"""
RNA‑seq analysis workflow demonstration
--------------------------------------

This script illustrates an end‑to‑end RNA‑seq analysis workflow similar to
the one used in the publication describing unique molecular mechanisms
underlying postharvest senescence.  It combines shell commands for
downloading and processing raw sequencing reads, R code for differential
expression analysis, and Python code for interactive visualisation.

The goal of this script is not to execute the entire pipeline on your
machine but to provide a realistic and reproducible template that you
can adapt to your own datasets.  Each step includes example file names
and directory paths that mirror a typical high‑performance computing
(HPC) environment.  Replace these paths and sample identifiers with
those appropriate for your system.

The pipeline consists of the following stages:

1. **Data retrieval** – download raw FASTQ files from the NCBI Sequence
   Read Archive (SRA) using `prefetch` and `fastq‑dump`.
2. **Quality control** – run FastQC on the raw reads and summarise
   reports using MultiQC.
3. **Trimming** – remove adapters and low‑quality bases with Trim Galore.
4. **Alignment** – build a STAR genome index and align trimmed reads.
5. **Quantification** – count reads per gene using featureCounts.
6. **Differential expression** – perform normalisation and statistical
   testing in R using edgeR/limma.
7. **Visualisation** – explore results interactively in Python with
   Plotly or in a Streamlit app.

To run the shell commands, uncomment the calls to ``run_command``
below.  To execute the R code, copy the string stored in
``R_SCRIPT`` into an R session.  The Python functions at the end can
be run after generating the CSV of differential expression results.

"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path
from typing import Iterable, List

import pandas as pd  # type: ignore
import plotly.express as px  # type: ignore


def run_command(cmd: Iterable[str], workdir: str | Path | None = None) -> None:
    """Run a shell command and stream its output.

    Parameters
    ----------
    cmd:
        The command and its arguments as a list.
    workdir:
        Optional working directory in which to run the command.

    Notes
    -----
    In this demonstration we simply print the command instead of
    executing it.  Uncomment the call to ``subprocess.run`` if you
    want to run the commands on your system.
    """
    print("\n$", " ".join(cmd))
    # Uncomment the line below to actually run the command
    # subprocess.run(cmd, cwd=workdir, check=True)


def main() -> None:
    """Execute the RNA‑seq workflow.

    This function orchestrates the steps of the pipeline.  It sets
    up directories, constructs commands for each stage, and prints
    them.  Adjust the paths and sample identifiers to match your
    experimental design.
    """
    # Define project directories
    project_root = Path("/home/utsab/projects/rnaseq")
    raw_dir = project_root / "raw_data"
    qc_dir = project_root / "qc"
    trimmed_dir = project_root / "trimmed"
    index_dir = project_root / "genome_index"
    align_dir = project_root / "alignment"
    counts_dir = project_root / "counts"
    results_dir = project_root / "results"

    # Example sample accession from SRA
    run_id = "SRR1234567"

    # Create directories (no effect if they already exist)
    for d in [raw_dir, qc_dir, trimmed_dir, index_dir, align_dir, counts_dir, results_dir]:
        d.mkdir(parents=True, exist_ok=True)

    # Step 1: Data retrieval
    run_command(["prefetch", run_id], workdir=raw_dir)
    run_command(["fastq-dump", "--split-files", f"{run_id}.sra", "--gzip"], workdir=raw_dir)

    # Step 2: Quality control
    run_command([
        "fastqc",
        "-o", str(qc_dir),
        str(raw_dir / f"{run_id}_1.fastq.gz"),
        str(raw_dir / f"{run_id}_2.fastq.gz"),
    ])
    run_command(["multiqc", str(qc_dir), "-o", str(qc_dir)])

    # Step 3: Trimming
    run_command([
        "trim_galore",
        "--paired",
        str(raw_dir / f"{run_id}_1.fastq.gz"),
        str(raw_dir / f"{run_id}_2.fastq.gz"),
        "-o", str(trimmed_dir),
    ])

    # Step 4: Build genome index and align
    genome_fasta = Path("/home/utsab/genomes/Brassica_oleracea_genome.fa")
    annotation_gtf = Path("/home/utsab/genomes/Brassica_oleracea_annotation.gtf")
    run_command([
        "STAR",
        "--runThreadN", "8",
        "--runMode", "genomeGenerate",
        "--genomeDir", str(index_dir),
        "--genomeFastaFiles", str(genome_fasta),
        "--sjdbGTFfile", str(annotation_gtf),
    ])
    run_command([
        "STAR",
        "--runThreadN", "8",
        "--genomeDir", str(index_dir),
        "--readFilesIn",
        str(trimmed_dir / f"{run_id}_1_val_1.fq.gz"),
        str(trimmed_dir / f"{run_id}_2_val_2.fq.gz"),
        "--readFilesCommand", "zcat",
        "--outFileNamePrefix", str(align_dir / f"{run_id}_"),
        "--outSAMtype", "BAM", "SortedByCoordinate",
    ])

    # Step 5: Generate gene counts
    run_command([
        "featureCounts",
        "-T", "8",
        "-p",
        "-t", "exon",
        "-g", "gene_id",
        "-a", str(annotation_gtf),
        "-o", str(counts_dir / "gene_counts.txt"),
        str(align_dir / f"{run_id}_Aligned.sortedByCoord.out.bam"),
    ])

    # Step 6: Differential expression (run in R)
    print("\n# The following R script should be executed in an R session:")
    print(R_SCRIPT)

    # Step 7: Visualisation (after generating results CSV)
    # To use this step, replace the path below with the path to your DE results CSV
    results_csv = results_dir / "DE_results_36h_vs_0h.csv"
    if results_csv.exists():
        df = pd.read_csv(results_csv, index_col=0)
        df["significant"] = (df["adj.P.Val"] < 0.05) & (df["logFC"].abs() > 1)
        fig = px.scatter(
            df,
            x="logFC",
            y="P.Value",
            color="significant",
            hover_name=df.index,
            labels={"logFC": "Log2 fold change", "P.Value": "p‑value"},
            title="Interactive Volcano Plot: 36h vs 0h",
        )
        fig.update_yaxes(type="log")
        fig.show()
    else:
        print(f"Results CSV not found at {results_csv}. Generate it first using the R script.")


# R script for differential expression analysis
R_SCRIPT: str = """
library(edgeR)
library(limma)

# Load gene counts generated by featureCounts
counts <- read.delim('/home/utsab/projects/rnaseq/counts/gene_counts.txt', comment.char = '#')
rownames(counts) <- counts$Geneid
counts <- counts[, -(1:6)]  # drop annotation columns

# Define sample groups (edit according to your experiment)
group <- factor(c('0h','0h','8h','8h','36h','36h'))
y <- DGEList(counts=counts, group=group)

# Filter lowly expressed genes
keep <- filterByExpr(y)
y <- y[keep,,keep.lib.sizes=FALSE]

# Normalise library sizes
y <- calcNormFactors(y)

# Design matrix for differential expression
design <- model.matrix(~0 + group)
colnames(design) <- levels(group)

# Voom transformation and linear modelling
v <- voom(y, design, plot=FALSE)
fit <- lmFit(v, design)
contrast.matrix <- makeContrasts('36h-0h' = `36h` - `0h`, '8h-0h' = `8h` - `0h`, levels=design)
fit2 <- contrasts.fit(fit, contrast.matrix)
fit2 <- eBayes(fit2)

# Extract results for the 36h vs 0h contrast
res <- topTable(fit2, coef = '36h-0h', number = Inf)

# Save results to CSV for downstream exploration in Python
dir.create('/home/utsab/projects/rnaseq/results', showWarnings = FALSE)
write.csv(res, file='/home/utsab/projects/rnaseq/results/DE_results_36h_vs_0h.csv', row.names=TRUE)

# Volcano plot
library(ggplot2)
res$significant <- res$adj.P.Val < 0.05 & abs(res$logFC) > 1
ggplot(res, aes(x = logFC, y = -log10(P.Value), colour = significant)) +
  geom_point(alpha=0.5) +
  scale_colour_manual(values=c('FALSE'='grey','TRUE'='red')) +
  xlab('Log2 fold change') + ylab('-log10(p‑value)') +
  ggtitle('Volcano Plot: 36h vs 0h') +
  theme_minimal()
"""


if __name__ == "__main__":
    main()
