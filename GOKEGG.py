# go_kegg_app.py
import pandas as pd
import streamlit as st
import scipy.stats as stats
import plotly.express as px
import io

st.set_page_config(layout="wide", page_title="GO/KEGG Enrichment App")
st.title("🧬 GO & KEGG Enrichment Explorer")
st.markdown("Upload gene list and annotation files to compute enrichment, then visualize results.")

# Sidebar options
with st.sidebar:
    st.header("🔧 Settings")
    enrichment_type = st.selectbox("Enrichment Type", ["GO", "KEGG"])
    p_cutoff = st.number_input("P-value Cutoff", 0.0, 1.0, 0.05)
    show_terms = st.slider("Number of Top Terms to Display", 5, 100, 20)
    correction = st.selectbox("Multiple Testing Correction", ["None", "FDR (BH)"])
    font_size = st.slider("Font Size", 8, 24, 12)
    color_scale = st.selectbox("Color Scale", px.colors.named_colorscales())

# File upload
uploaded_gene_file = st.file_uploader("Upload Gene List (one column, no header)", type=["txt", "csv"])
uploaded_annotation_file = st.file_uploader("Upload GO/KEGG Annotation File (2 columns: Gene ID, Term)", type=["csv", "tsv"])
uploaded_background_file = st.file_uploader("(Optional) Upload Background Gene List", type=["txt", "csv"])

def correct_pvals(df, method):
    if method == "FDR (BH)":
        from statsmodels.stats.multitest import multipletests
        df["AdjP"] = multipletests(df["Pval"], method='fdr_bh')[1]
    else:
        df["AdjP"] = df["Pval"]
    return df

if uploaded_gene_file and uploaded_annotation_file:
    gene_list = pd.read_csv(uploaded_gene_file, header=None).iloc[:, 0].dropna().astype(str).tolist()
    ann_sep = "\t" if uploaded_annotation_file.name.endswith("tsv") else ","
    annotation_df = pd.read_csv(uploaded_annotation_file, sep=ann_sep, header=None)
    annotation_df.columns = ["Gene", "Term"]
    
    background_genes = set(annotation_df["Gene"])
    if uploaded_background_file:
        bg_df = pd.read_csv(uploaded_background_file, header=None)
        background_genes = set(bg_df.iloc[:, 0].astype(str))

    # Filter to background
    input_genes = set(gene_list).intersection(background_genes)
    if not input_genes:
        st.error("No overlap between input genes and annotation.")
    else:
        ann_df = annotation_df[annotation_df["Gene"].isin(background_genes)]

        term_map = ann_df.groupby("Term")["Gene"].apply(set).to_dict()
        results = []
        for term, genes_in_term in term_map.items():
            a = len(genes_in_term & input_genes)  # overlap
            b = len(genes_in_term - input_genes)  # in term not input
            c = len(input_genes - genes_in_term)  # input not in term
            d = len(background_genes - genes_in_term - input_genes)  # neither
            table = [[a, b], [c, d]]
            _, pval = stats.fisher_exact(table, alternative='greater')
            results.append({"Term": term, "InputGeneCount": a, "TermGeneCount": len(genes_in_term), "Pval": pval})

        res_df = pd.DataFrame(results)
        res_df = correct_pvals(res_df, correction)
        res_df = res_df[res_df["AdjP"] <= p_cutoff].sort_values("AdjP").head(show_terms)

        st.success(f"{len(res_df)} enriched terms found.")

        st.subheader("📊 Enrichment Results")
        st.dataframe(res_df)
        csv_data = res_df.to_csv(index=False).encode('utf-8')
        st.download_button("⬇️ Download Enrichment CSV", csv_data, file_name="enrichment_results.csv", mime="text/csv")

        st.subheader("🎨 Interactive Plot")
        fig = px.bar(res_df, 
                     x="InputGeneCount", 
                     y="Term", 
                     orientation='h',
                     color="AdjP",
                     color_continuous_scale=color_scale,
                     labels={"AdjP": "Adjusted P-value"},
                     text="InputGeneCount")
        fig.update_layout(font=dict(size=font_size))
        st.plotly_chart(fig, use_container_width=True)
else:
    st.warning("Please upload the required files to proceed.")
