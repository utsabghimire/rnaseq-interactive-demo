# go_kegg_app.py
import os
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

st.set_page_config(page_title="Gene Enrichment Explorer", layout="wide")
st.title("🧬 GO & KEGG Term Enrichment Explorer")

# Sidebar options
species = st.sidebar.selectbox("Select species", [
    "Arabidopsis thaliana", "Oryza sativa", "Zea mays", "Homo sapiens", "Mus musculus", "Upload custom files"
])

font_size = st.sidebar.slider("Font size for plots", 6, 30, 12)
fig_width = st.sidebar.slider("Figure width", 5, 20, 10)
fig_height = st.sidebar.slider("Figure height", 3, 15, 6)

example_gene_sets = {
    "Arabidopsis thaliana": ["AT1G01010", "AT1G01530", "AT1G01720"],
    "Oryza sativa": ["LOC_Os01g01010", "LOC_Os01g01530"],
    "Homo sapiens": ["BRCA1", "TP53", "EGFR"]
}

st.markdown("### 1️⃣ Upload Your Gene List")
example = example_gene_sets.get(species, [])
example_str = ", ".join(example)
input_gene_text = st.text_area("Paste your gene list (one per line or comma separated)", value="\n".join(example), height=150)
gene_list = list({g.strip() for g in re.split(r'[\n,;\t ]+', input_gene_text) if g.strip()})

if not gene_list:
    st.warning("Please enter a valid gene list to continue.")
    st.stop()

st.markdown("### 2️⃣ Provide GO and KEGG Annotations")

if species != "Upload custom files":
    go_file = f"data/{species.split()[0].lower()}_go.tsv"
    kegg_file = f"data/{species.split()[0].lower()}_kegg.tsv"
    if not os.path.exists(go_file) or not os.path.exists(kegg_file):
        st.error(f"Missing preloaded annotation files for {species}. Please upload manually.")
        st.stop()
    go_df = pd.read_csv(go_file, sep="\t", names=["GeneID", "GO"])
    kegg_df = pd.read_csv(kegg_file, sep="\t", names=["GeneID", "Pathway"])
else:
    go_upload = st.file_uploader("Upload GO annotations (TSV: GeneID TAB GO)", type=["tsv"])
    kegg_upload = st.file_uploader("Upload KEGG annotations (TSV: GeneID TAB Pathway)", type=["tsv"])
    if go_upload and kegg_upload:
        go_df = pd.read_csv(go_upload, sep="\t", names=["GeneID", "GO"])
        kegg_df = pd.read_csv(kegg_upload, sep="\t", names=["GeneID", "Pathway"])
    else:
        st.stop()

# Enrichment function
def enrich(annotations, label):
    bg_total = annotations.shape[0]
    fg_total = len(gene_list)
    filtered = annotations[annotations.GeneID.isin(gene_list)]
    counts = filtered[label].value_counts().reset_index()
    counts.columns = [label, "Count"]
    counts["Total"] = annotations[label].value_counts()
    counts["Enrichment"] = (counts["Count"] / fg_total) / (counts["Total"] / bg_total)
    return counts.sort_values("Enrichment", ascending=False).head(30)

# Plot function
def plot_enrichment(df, label, title):
    plt.figure(figsize=(fig_width, fig_height))
    sns.barplot(data=df, y=label, x="Enrichment", palette="viridis")
    plt.title(title, fontsize=font_size + 4)
    plt.xlabel("Fold Enrichment", fontsize=font_size)
    plt.ylabel(label, fontsize=font_size)
    plt.xticks(fontsize=font_size)
    plt.yticks(fontsize=font_size)
    st.pyplot(plt.gcf())

# Results
st.markdown("### 3️⃣ Results")
go_enriched = enrich(go_df, "GO")
kegg_enriched = enrich(kegg_df, "Pathway")

with st.expander("GO Term Enrichment"):
    plot_enrichment(go_enriched, "GO", "Top GO Terms")
    st.dataframe(go_enriched)
    st.download_button("Download GO Enrichment CSV", go_enriched.to_csv(index=False).encode(), "go_enrichment.csv")

with st.expander("KEGG Pathway Enrichment"):
    plot_enrichment(kegg_enriched, "Pathway", "Top KEGG Pathways")
    st.dataframe(kegg_enriched)
    st.download_button("Download KEGG Enrichment CSV", kegg_enriched.to_csv(index=False).encode(), "kegg_enrichment.csv")
