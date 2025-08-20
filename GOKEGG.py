import streamlit as st
import pandas as pd
import re
import matplotlib.pyplot as plt
import seaborn as sns
import io

st.set_page_config(page_title="GO/KEGG Enrichment Visualizer", layout="wide")

st.title("🧬 GO/KEGG Enrichment Analysis")

# --- Sidebar Settings ---
with st.sidebar:
    st.header("⚙️ Display Settings")
    font_size = st.slider("Font Size", 8, 30, 14)
    title_font_size = st.slider("Title Font Size", 10, 40, 20)
    top_n = st.slider("Show Top N Terms", 5, 50, 20)
    orientation = st.radio("Plot Orientation", ["Horizontal", "Vertical"])
    sort_by = st.radio("Sort by", ["p-value", "gene count"])

    st.markdown("---")
    st.header("🎨 Color Settings")
    color_palette = st.selectbox("Color Palette", ["viridis", "plasma", "coolwarm", "magma", "Set2"])

# --- Gene List Input ---
st.header("🔍 Input Gene List")
input_method = st.radio("Input method:", ["Paste gene list", "Upload gene list file"])

if input_method == "Paste gene list":
    input_gene_text = st.text_area("Paste gene IDs (comma, newline, tab, or space separated):", height=200)
    gene_list = list({g.strip() for g in re.split(r'[\n,;\t ]+', input_gene_text) if g.strip()})
else:
    gene_file = st.file_uploader("Upload gene list file (.txt or .csv)", type=["txt", "csv"])
    gene_list = []
    if gene_file is not None:
        df = pd.read_csv(gene_file, header=None)
        gene_list = list(df.iloc[:, 0].dropna().astype(str).unique())

if not gene_list:
    st.warning("⚠️ No valid gene IDs provided.")
    st.stop()

st.success(f"✅ {len(gene_list)} unique gene IDs received.")

# --- Annotation Upload ---
st.header("📚 Upload GO/KEGG Annotation File")
annotation_file = st.file_uploader("Upload full background annotation file (GO/KEGG with columns: Term, GeneID, p-value)", type=["csv", "tsv"])

if annotation_file is not None:
    if annotation_file.name.endswith(".tsv"):
        ann_df = pd.read_csv(annotation_file, sep="\t")
    else:
        ann_df = pd.read_csv(annotation_file)

    if not all(col in ann_df.columns for col in ["Term", "GeneID"]):
        st.error("❌ Annotation file must have columns: Term, GeneID")
        st.stop()

    # Filter annotation for selected genes
    ann_df["GeneID"] = ann_df["GeneID"].astype(str)
    filtered_df = ann_df[ann_df["GeneID"].isin(gene_list)]

    if filtered_df.empty:
        st.warning("⚠️ No matching genes found in annotation.")
        st.stop()

    term_stats = (
        filtered_df.groupby("Term")
        .agg(gene_count=("GeneID", "count"))
        .reset_index()
    )

    # Merge with p-values if provided
    if "p-value" in ann_df.columns:
        pval_df = ann_df[["Term", "p-value"]].drop_duplicates()
        term_stats = pd.merge(term_stats, pval_df, on="Term", how="left")
    else:
        term_stats["p-value"] = 1.0

    # Sort and limit
    term_stats = term_stats.sort_values(
        "p-value" if sort_by == "p-value" else "gene_count",
        ascending=(sort_by == "p-value")
    ).head(top_n)

    st.subheader("📈 Enrichment Plot")
    fig, ax = plt.subplots(figsize=(10, 6))

    if orientation == "Horizontal":
        sns.barplot(
            data=term_stats,
            x="gene_count",
            y="Term",
            palette=color_palette,
            ax=ax
        )
        ax.set_xlabel("Gene Count", fontsize=font_size)
        ax.set_ylabel("GO/KEGG Term", fontsize=font_size)
    else:
        sns.barplot(
            data=term_stats,
            x="Term",
            y="gene_count",
            palette=color_palette,
            ax=ax
        )
        ax.set_ylabel("Gene Count", fontsize=font_size)
        ax.set_xlabel("GO/KEGG Term", fontsize=font_size)
        ax.tick_params(axis='x', rotation=45)

    ax.set_title("Top Enriched GO/KEGG Terms", fontsize=title_font_size)
    plt.tight_layout()
    st.pyplot(fig)

    # Downloads
    st.subheader("⬇️ Downloads")
    out_csv = term_stats.to_csv(index=False).encode("utf-8")
    st.download_button("📥 Download Table (CSV)", out_csv, "enrichment_results.csv", "text/csv")

    buf = io.BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight", dpi=300)
    st.download_button("📥 Download Plot (PNG)", buf.getvalue(), "enrichment_plot.png", "image/png")

else:
    st.info("Upload annotation file to proceed.")

# --- Example Dataset ---
with st.expander("📎 Example Gene List (for testing)"):
    st.markdown("Example IDs (copy-paste):")
    st.code("AT1G01010\nAT1G01020\nAT1G01030\nAT1G01040\nAT1G01050")
