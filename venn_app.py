# Updated version of venn_app.py with added features:
# - Font size controls
# - Custom intersection region colors (4-6 sets only)
# - Download exclusive elements for each set

import io
import re
from typing import Dict, Set, List
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
from matplotlib_venn import venn2, venn3
from venn import venn as venn_up_to_6

st.set_page_config(page_title="Multi-Set Venn (up to 6)", layout="wide")

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

    cleaned = [p.strip().lower() if not case_sensitive else p.strip() for p in parts if p.strip()]
    return set(cleaned)

def read_file_to_set(file, split_mode: str, case_sensitive: bool) -> Set[str]:
    try:
        if file.name.lower().endswith((".tsv",)):
            df = pd.read_csv(file, sep="\t")
        else:
            df = pd.read_csv(file)
        flat = df.astype(str).values.ravel().tolist()
        text = "\n".join([x for x in flat if x and x.lower() != "nan"])
        return coerce_items(text, "Newlines (one per line)", case_sensitive)
    except Exception:
        file.seek(0)
        text = file.read().decode("utf-8", errors="ignore")
        return coerce_items(text, split_mode, case_sensitive)

def sets_to_intersections(sets_dict: Dict[str, Set[str]]) -> pd.DataFrame:
    from itertools import combinations
    names = list(sets_dict.keys())
    data = []
    for k in range(1, len(names) + 1):
        for comb in combinations(names, k):
            inter = set.intersection(*(sets_dict[name] for name in comb))
            data.append({
                "Sets": " ∩ ".join(comb),
                "Size": len(inter),
                "Elements": ", ".join(sorted(inter))
            })
    return pd.DataFrame(data).sort_values(["Size", "Sets"], ascending=[False, True])

def draw_venn_2_3(sets_dict: Dict[str, Set[str]], colors: List[str], title: str, title_fontsize: int, label_fontsize: int) -> plt.Figure:
    names = list(sets_dict.keys())
    n = len(names)
    plt.figure(figsize=(7, 6), dpi=180)
    plt.title(title, fontsize=title_fontsize)

    if n == 2:
        v = venn2([sets_dict[names[0]], sets_dict[names[1]]], set_labels=(names[0], names[1]))
    else:
        v = venn3([sets_dict[n] for n in names], set_labels=names)

    # Apply colors
    for i, patch in enumerate(v.patches):
        if patch:
            patch.set_facecolor(colors[i % len(colors)])
            patch.set_alpha(0.5)

    # Apply label sizes
    for label in v.set_labels:
        if label:
            label.set_fontsize(label_fontsize)
    for text in v.subset_labels:
        if text:
            text.set_fontsize(label_fontsize)

    return plt.gcf()


def draw_venn_4_6(sets_dict, colors, title, title_fontsize, label_fontsize):
    import matplotlib.colors as mcolors
    cmap = mcolors.ListedColormap(colors)
    plt.figure(figsize=(10, 8), dpi=180)
    ax = venn_up_to_6(sets_dict, cmap=cmap)
    for text in ax.texts:
        if text:
            text.set_fontsize(label_fontsize)
    plt.title(title, fontsize=title_fontsize)
    return plt.gcf()

def get_exclusive_elements(sets_dict: Dict[str, Set[str]]) -> pd.DataFrame:
    exclusive = {}
    for name, s in sets_dict.items():
        others = set().union(*(v for k, v in sets_dict.items() if k != name))
        exclusive[name] = sorted(s - others)
    return pd.DataFrame({"Set": exclusive.keys(), "Exclusive Elements": exclusive.values()})

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

# === UI ===
st.title("🧬 Venn Diagram Builder (up to 6 sets)")
with st.sidebar:
    mode = st.radio("Input type", ["Upload files", "Paste lists"])
    n_sets = st.slider("Number of sets", 2, 6, 3)
    split_mode = st.selectbox("Split items by", ["Auto", "Newlines (one per line)", "Commas", "Tabs", "Semicolons", "Pipes (|)"])
    case_sensitive = st.checkbox("Case sensitive matching", value=False)
    title = st.text_input("Venn diagram title", value="Venn Diagram")
    title_fontsize = st.slider("Title font size", 10, 30, 16)
    label_fontsize = st.slider("Label font size", 8, 24, 10)
    set_names = [st.text_input(f"Name for Set {i+1}", value=f"Set {i+1}") for i in range(n_sets)]
    set_colors = [st.color_picker(f"Color for Set {i+1}", value=["#4c78a8", "#f58518", "#54a24b", "#e45756", "#72b7b2", "#b279a2"][i]) for i in range(n_sets)]

sets_dict: Dict[str, Set[str]] = {}
if mode == "Upload files":
    files = st.file_uploader("Upload one file per set", type=["txt", "csv", "tsv"], accept_multiple_files=True)
    if files:
        for i, f in enumerate(files[:n_sets]):
            sets_dict[set_names[i]] = read_file_to_set(f, split_mode, case_sensitive)
else:
    for i in range(n_sets):
        txt = st.text_area(f"Paste items for {set_names[i]}", height=120)
        sets_dict[set_names[i]] = coerce_items(txt, split_mode, case_sensitive)

if sets_dict and all(len(s) > 0 for s in sets_dict.values()):
    st.subheader("📦 Set Sizes")
    st.dataframe(pd.DataFrame({"Set": list(sets_dict.keys()), "Size": [len(s) for s in sets_dict.values()]}))

    st.subheader("📊 Venn Diagram")
    if n_sets in (2, 3):
        fig = draw_venn_2_3(sets_dict, set_colors, title, title_fontsize, label_fontsize)
    else:
        fig = draw_venn_4_6(sets_dict, set_colors, title, title_fontsize, label_fontsize)
    st.pyplot(fig, use_container_width=True)
    fig_download_buttons(fig)

    st.subheader("🔄 Intersection Table")
    inter_df = sets_to_intersections(sets_dict)
    st.dataframe(inter_df)
    st.download_button("⬇️ Download Intersection Table (CSV)", inter_df.to_csv(index=False).encode("utf-8"), file_name="intersections.csv")

    st.subheader("🧮 Exclusive Elements")
    excl_df = get_exclusive_elements(sets_dict)
    st.dataframe(excl_df)
    excl_csv = excl_df.to_csv(index=False).encode("utf-8")
    st.download_button("⬇️ Download Exclusive Elements (CSV)", excl_csv, file_name="exclusive_elements.csv")
else:
    st.info("Please provide valid input for each set.")
