import io
import re
from typing import Dict, List, Set, Tuple
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt

from matplotlib_venn import venn2, venn3
from venn import venn as venn_up_to_6

st.set_page_config(page_title="Multi-Set Venn (up to 6)", layout="wide")

# -----------------------------
# Helpers
# -----------------------------
def coerce_items(text: str, split_mode: str, case_sensitive: bool) -> Set[str]:
    if not text:
        return set()
    if split_mode == "Auto":
        parts = re.split(r"[\n,\t;|]+", text)
    elif split_mode == "Newlines (one per line)":
        parts = re.split(r"\n+", text)
    elif split_mode == "Commas":
        parts = re.split(r",+", text)
    elif split_mode == "Tabs":
        parts = re.split(r"\t+", text)
    elif split_mode == "Semicolons":
        parts = re.split(r";+", text)
    elif split_mode == "Pipes (|)":
        parts = re.split(r"\|+", text)
    else:
        parts = [text]

    cleaned = []
    for p in parts:
        s = p.strip()
        if not case_sensitive:
            s = s.lower()
        if s:
            cleaned.append(s)
    return set(cleaned)

def read_file_to_set(file, split_mode: str, case_sensitive: bool) -> Set[str]:
    try:
        if file.name.lower().endswith((".tsv",)):
            df = pd.read_csv(file, sep="\t")
        else:
            df = pd.read_csv(file)
        if df.shape[1] == 1:
            col = df.columns[0]
            series = df[col].dropna().astype(str).tolist()
            text = "\n".join(series)
            return coerce_items(text, "Newlines (one per line)", case_sensitive)
        else:
            flat = df.astype(str).values.ravel().tolist()
            text = "\n".join([x for x in flat if x and x.lower() != "nan"])
            return coerce_items(text, "Newlines (one per line)", case_sensitive)
    except Exception:
        file.seek(0)
        text = file.read().decode("utf-8", errors="ignore")
        return coerce_items(text, split_mode, case_sensitive)

def sets_to_intersections(sets_dict: Dict[str, Set[str]]) -> Tuple[pd.DataFrame, Dict[str, Set[str]]]:
    from itertools import combinations
    names = list(sets_dict.keys())
    data = []
    inter_dict = {}
    for k in range(1, len(names) + 1):
        for comb in combinations(names, k):
            inter = set.intersection(*(sets_dict[name] for name in comb))
            comb_key = " ∩ ".join(comb)
            data.append({"Sets": comb_key, "Size": len(inter)})
            inter_dict[comb_key] = inter
    df = pd.DataFrame(data).sort_values(["Size", "Sets"], ascending=[False, True])
    return df, inter_dict

def draw_venn_2_3(sets_dict: Dict[str, Set[str]], colors: List[str], venn_title: str, title_fontsize: int, label_fontsize: int, label_fontstyle: str):
    names = list(sets_dict.keys())
    n = len(names)
    plt.figure(figsize=(7, 6), dpi=180)
    if n == 2:
        a, b = sets_dict[names[0]], sets_dict[names[1]]
        v = venn2([a, b], set_labels=(names[0], names[1]))
    else:
        a, b, c = [sets_dict[n] for n in names]
        v = venn3([a, b, c], set_labels=(names[0], names[1], names[2]))

    for label in v.set_labels:
        if label:
            label.set_fontsize(label_fontsize)
            label.set_fontstyle(label_fontstyle)
    for label in v.subset_labels:
        if label:
            label.set_fontsize(label_fontsize)
            label.set_fontstyle(label_fontstyle)

    plt.title(venn_title, fontsize=title_fontsize)
    st.pyplot(plt.gcf(), use_container_width=True)
    return plt.gcf()

def draw_venn_4_6(sets_dict: Dict[str, Set[str]], colors: List[str], venn_title: str, title_fontsize: int, label_fontsize: int):
    import matplotlib.colors as mcolors
    cmap = mcolors.ListedColormap(colors)
    plt.figure(figsize=(9, 8), dpi=180)
    ax = venn_up_to_6(sets_dict, cmap=cmap)
    for text in ax.texts:
        text.set_fontsize(label_fontsize)
    plt.title(venn_title, fontsize=title_fontsize)
    st.pyplot(plt.gcf(), use_container_width=True)
    return plt.gcf()

def fig_download_buttons(fig):
    col1, col2 = st.columns(2)
    with col1:
        png_buf = io.BytesIO()
        fig.savefig(png_buf, format="png", bbox_inches="tight", dpi=300, transparent=True)
        st.download_button("⬇️ Download PNG", png_buf.getvalue(), file_name="venn.png", mime="image/png")
    with col2:
        svg_buf = io.BytesIO()
        fig.savefig(svg_buf, format="svg", bbox_inches="tight")
        st.download_button("⬇️ Download SVG", svg_buf.getvalue(), file_name="venn.svg", mime="image/svg+xml")

# -----------------------------
# UI
# -----------------------------
st.title("Venn Diagram Builder (up to 6 sets)")

with st.sidebar:
    st.header("Input options")
    mode = st.radio("How will you provide sets?", ["Upload files", "Paste lists"], index=0)
    n_sets = st.slider("Number of sets", 2, 6, 3)

    st.subheader("Parsing")
    split_mode = st.selectbox(
        "Split items by",
        ["Auto", "Newlines (one per line)", "Commas", "Tabs", "Semicolons", "Pipes (|)"],
        index=0
    )
    case_sensitive = st.checkbox("Case sensitive matching", value=False)

    st.subheader("Appearance")
    default_names = [f"Set {i+1}" for i in range(n_sets)]
    set_names = []
    set_colors = []
    for i in range(n_sets):
        with st.container():
            set_names.append(
                st.text_input(f"Label for Set {i+1}", value=default_names[i], key=f"name_{i}")
            )
            set_colors.append(
                st.color_picker(f"Color for {default_names[i]}", value=["#4c78a8", "#f58518", "#54a24b", "#e45756", "#72b7b2", "#b279a2"][i % 6], key=f"color_{i}")
            )

    st.markdown("---")
    st.subheader("Venn diagram title & font style")
    venn_title = st.text_input("Main title for the Venn diagram", value="Venn Diagram")
    title_fontsize = st.slider("Title font size", 10, 40, 20)
    label_fontsize = st.slider("Region number font size", 6, 20, 10)
    label_fontstyle = st.selectbox("Region label font style", ["normal", "italic", "oblique"], index=0)

# Collect sets
sets_dict: Dict[str, Set[str]] = {}
if mode == "Upload files":
    files = st.file_uploader("Upload files (TXT/CSV/TSV). One file = one set.", type=["txt", "csv", "tsv"], accept_multiple_files=True)
    if files:
        files = files[:n_sets]
        for i, f in enumerate(files):
            items = read_file_to_set(f, split_mode, case_sensitive)
            sets_dict[set_names[i]] = items
elif mode == "Paste lists":
    cols = st.columns(min(3, n_sets))
    text_blobs: List[str] = ["" for _ in range(n_sets)]
    for i in range(n_sets):
        text_blobs[i] = st.text_area(f"Items for {set_names[i]}", height=140, key=f"paste_{i}")
    for i in range(n_sets):
        sets_dict[set_names[i]] = coerce_items(text_blobs[i], split_mode, case_sensitive)

# Plot and show results
if sets_dict and all(len(s) > 0 for s in sets_dict.values()):
    st.subheader("Set sizes")
    size_df = pd.DataFrame({"Set": list(sets_dict.keys()), "Size": [len(s) for s in sets_dict.values()]})
    st.dataframe(size_df, use_container_width=True)

    st.subheader("Venn diagram")
    fig = None
    try:
        if n_sets in (2, 3):
            fig = draw_venn_2_3(sets_dict, set_colors[:n_sets], venn_title, title_fontsize, label_fontsize, label_fontstyle)
        else:
            fig = draw_venn_4_6(sets_dict, set_colors[:n_sets], venn_title, title_fontsize, label_fontsize)
    except Exception as e:
        st.error(f"Could not draw Venn: {e}")

    if fig:
        fig_download_buttons(fig)

    st.subheader("Intersection sizes and downloads")
    inter_df, inter_dict = sets_to_intersections(sets_dict)
    st.dataframe(inter_df, use_container_width=True)

    for combo, items in inter_dict.items():
        if not items:
            continue
        csv = "\n".join(sorted(items))
        st.download_button(
            label=f"⬇️ Download items in: {combo} ({len(items)} items)",
            data=csv,
            file_name=f"intersection_{combo.replace(' ∩ ', '_')}.txt",
            mime="text/plain"
        )

else:
    st.info("Please upload or paste valid sets (≥1 item each).")
