"""
Streamlit app for exploring differential expression results from the RNA‑seq workflow.

Run this application after completing the notebook and exporting the DE results to
`DE_results_36h_vs_0h.csv`.  The app reads the CSV and provides a searchable,
sortable table along with an interactive scatter plot of log2 fold change vs
p‑value.

Usage:

```
streamlit run streamlit_app.py
```
"""

import streamlit as st
import pandas as pd
import plotly.express as px

# Page configuration
st.set_page_config(page_title="RNA‑seq DE Explorer", layout="wide")

@st.cache_data
def load_data(path: str) -> pd.DataFrame:
    """Load differential expression results from a CSV file."""
    df = pd.read_csv(path, index_col=0)
    return df


def main() -> None:
    st.title("RNA‑seq Differential Expression Explorer")

    st.sidebar.header("Settings")
    uploaded_file = st.sidebar.file_uploader(
        "Upload differential expression results (CSV)", type=["csv"]
    )

    if uploaded_file is not None:
        df = load_data(uploaded_file)
        st.sidebar.success("Loaded {} genes".format(len(df)))

        # Filter options
        pval_threshold = st.sidebar.slider(
            "Adjusted p‑value threshold", min_value=0.0, max_value=0.10, value=0.05, step=0.005
        )
        logfc_threshold = st.sidebar.slider(
            "Absolute log2 fold change threshold", min_value=0.0, max_value=5.0, value=1.0, step=0.1
        )

        # Apply filters
        df["significant"] = (
            (df["adj.P.Val"] < pval_threshold) & (df["logFC"].abs() > logfc_threshold)
        )

        # Main plot
        fig = px.scatter(
            df,
            x="logFC",
            y="P.Value",
            color="significant",
            hover_name=df.index,
            labels={"logFC": "Log2 fold change", "P.Value": "p‑value"},
            title="Volcano plot (interactive)",
        )
        fig.update_yaxes(type="log")
        st.plotly_chart(fig, use_container_width=True)

        st.subheader("Differential expression results")
        st.dataframe(df)
    else:
        st.info("Upload a CSV file with differential expression results to get started.")


if __name__ == "__main__":
    main()
