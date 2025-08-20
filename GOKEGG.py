import io
import pandas as pd
import streamlit as st
import plotly.express as px
from scipy.stats import fisher_exact
from collections import defaultdict

st.set_page_config(page_title="GO/KEGG Enrichment Analyzer", layout="wide")
st.title("🧬 GO and KEGG Enrichment Analysis")

# Sidebar settings
with st.sidebar:
    st.header("Settings")
    mode = st.radio("Species Mode", ["Model Organism (Auto)", "Custom Species"])
    font_title = st.slider("Plot Title Font Size", 10, 40, 20)
    font_label = st.slider("Axis Label Font Size", 8, 24, 14)
    font_tick = st.slider("Tick Font Size", 6, 20, 12)
    max_terms = st.slider("Top N GO Terms to Display", 5, 50, 20)
    color_scale = st.selectbox("Bar Color Scale", px.colors.named_colorscales(), index=px.colors.named_colorscales().index("Viridis"))

# Upload section
st.markdown("### 🗂️ Upload Required Files")
with st.expander("1. Upload Gene List (Query Genes)", expanded=True):
    query_file = st.file_uploader("Upload a file with gene list (1 column)", type=["csv", "txt"])

if mode == "Custom Species":
    with st.expander("2. Upload GO Annotation File", expanded=True):
        go_file = st.file_uploader("Upload GO annotation file (CSV: gene_id, go_term)", type=["csv", "tsv"])
    with st.expander("3. Upload KEGG Mapping File (Optional)"):
        kegg_file = st.file_uploader("Upload KEGG mapping file (CSV: gene_id, kegg_id)", type=["csv", "tsv"])

# Helper functions
def load_gene_list(file) -> set:
    df = pd.read_csv(file, header=None)
    return set(df.iloc[:, 0].dropna().astype(str).unique())

def load_annotation_file(file, sep=",") -> pd.DataFrame:
    df = pd.read_csv(file, sep=sep)
    df.columns = [col.strip().lower() for col in df.columns]
    return df[["gene_id", "go_term"]]

def go_enrichment(go_df, query_genes):
    universe = set(go_df["gene_id"])
    total_universe = len(universe)
    query_set = set(query_genes)

    go_to_genes = defaultdict(set)
    for _, row in go_df.iterrows():
        go_to_genes[row["go_term"]].add(row["gene_id"])

    records = []
    for go_term, term_genes in go_to_genes.items():
        overlap = len(query_set & term_genes)
        term_size = len(term_genes)
        query_size = len(query_set)

        if overlap == 0:
            continue

        table = [
            [overlap, query_size - overlap],
            [term_size - overlap, total_universe - query_size - term_size + overlap],
        ]
        oddsratio, pval = fisher_exact(table, alternative="greater")

        records.append({
            "GO Term": go_term,
            "Gene Count": overlap,
            "Term Size": term_size,
            "p-value": pval,
            "Overlap Genes": ", ".join(sorted(query_set & term_genes)),
        })

    df = pd.DataFrame(records)
    df = df.sort_values("p-value").reset_index(drop=True)
    return df

# Enrichment analysis
if query_file and go_file:
    try:
        query_genes = load_gene_list(query_file)
        go_df = load_annotation_file(go_file, sep="," if go_file.name.endswith("csv") else "\t")

        enriched = go_enrichment(go_df, query_genes)

        if not enriched.empty:
            st.markdown("### 📊 GO Term Enrichment Results")
            st.dataframe(enriched)
            csv = enriched.to_csv(index=False).encode("utf-8")
            st.download_button("⬇️ Download Enrichment Table (CSV)", csv, "go_enrichment.csv", "text/csv")

            # Plot
            st.markdown("### 📈 Enrichment Plot")
            fig = px.bar(
                enriched.head(max_terms),
                x="GO Term",
                y="Gene Count",
                color="p-value",
                color_continuous_scale=color_scale,
                hover_data=["Overlap Genes"],
                title="Top Enriched GO Terms"
            )
            fig.update_layout(
                title_font_size=font_title,
                xaxis_title_font_size=font_label,
                yaxis_title_font_size=font_label,
                xaxis_tickfont_size=font_tick,
                yaxis_tickfont_size=font_tick
            )
            st.plotly_chart(fig, use_container_width=True)

        else:
            st.warning("No significant GO terms found.")
    except Exception as e:
        st.error(f"Error during analysis: {e}")
else:
    st.info("Please upload both a query gene file and GO annotation file.")
