# venn_app.py

import io
import re
from typing import Dict, List, Set
from itertools import combinations

import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
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
        parts = re.split(r",+")
    elif split_mode == "Tabs":
        parts = re.split(r"\t+")
    elif split_mode == "Semicolons":
        parts = re.split(r";+")
    elif split_mode == "Pipes (|)":
        parts = re.split(r"\|+")
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
        if file.name.lower().endswith(".tsv"):
            df = pd.read_csv(file, sep="\t")
        else:
            df = pd.read_csv(file)
        if df.shape[1] == 1:
            text = "\n".join(df.iloc[:, 0].dropna().astype(str).tolist())
        else:
            flat = df.astype(str).values.ravel().tolist()
            text = "\n".join([x for x in flat if x.lower() != "nan"])
        return coerce_items(text, "Newlines (one per line)", case_sensitive)
    except Exception:
        file.seek(0)
        text = file.read().decode("utf-8", errors="ignore")
        return coerce_items(text, split_mode, case_sensitive)


def sets_to_intersections(sets_dict: Dict[str, Set[str]]) -> pd.DataFrame:
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
    df = pd.DataFrame(data).sort_values(["Size", "Sets"], ascending=[False, True])
    return df


def sets_to_exclusive(sets_dict: Dict[str, Set[str]]) -> pd.DataFrame:
    names = list(sets_dict.keys())
    data = []
    for name in names:
        exclusive = sets_dict[name] - set.union(*[v for k, v in sets_dict.items() if k != name])
        data.append({
            "Set": name,
            "Exclusive Size": len(exclusive),
            "Elements": ", ".join(sorted(exclusive))
        })
    return pd.DataFrame(data)


def draw_venn_2_3(sets_dict, colors, label_fontsize, number_fontsize, title):
    names = list(sets_dict.keys())
    n = len(names)
    fig, ax = plt.subplots(figsize=(7, 6), dpi=180)
    plt.title(title, fontsize=label_fontsize + 4)
    if n == 2:
        a, b = sets_dict[names[0]], sets_dict[names[1]]
        v = venn2([a, b], set_labels=(names[0], names[1]), ax=ax)
    else:
        a, b, c = [sets_dict[n] for n in names]
        v = venn3([a, b, c], set_labels=(names[0], names[1], names[2]), ax=ax)
    for region in v.subset_labels:
        if region:
            region.set_fontsize(number_fontsize)
    for label in v.set_labels:
        if label:
            label.set_fontsize(label_fontsize)
    return fig


def draw_venn_4_6(sets_dict, colors, title, label_fontsize, number_fontsize):
    fig = plt.figure(figsize=(9, 8), dpi=180)
    plt.title(title, fontsize=label_fontsize + 4)
    cmap = mcolors.ListedColormap(colors)
    ax = venn_up_to_6(sets_dict, cmap=cmap)
    for text in ax.texts:
        text.set_fontsize(number_fontsize)
    return fig


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
st.title("🧬 Venn Diagram Builder (up to 6 sets)")

with st.sidebar:
    st.header("Input Options")
    mode = st.radio("How will you provide sets?", ["Upload files", "Paste lists"], index=0)
    n_sets = st.slider("Number of sets", 2, 6, 3)

    split_mode = st.selectbox("Split items by", ["Auto", "Newlines (one per line)", "Commas", "Tabs", "Semicolons", "Pipes (|)"], index=0)
    case_sensitive = st.checkbox("Case sensitive matching", value=False)

    st.subheader("Venn Diagram Customization")
    venn_title = st.text_input("Main Venn Diagram Title", value="My Venn Diagram")
    label_fontsize = st.slider("Font Size: Set Labels", 8, 24, 12)
    number_fontsize = st.slider("Font Size: Intersection Numbers", 8, 24, 10)

    set_names = []
    set_colors = []
    for i in range(n_sets):
        set_names.append(st.text_input(f"Name for Set {i+1}", value=f"Set {i+1}"))
        set_colors.append(st.color_picker(f"Color for Set {i+1}", value=["#4c78a8", "#f58518", "#54a24b", "#e45756", "#72b7b2", "#b279a2"][i]))

sets_dict = {}
if mode == "Upload files":
    files = st.file_uploader("Upload files (1 per set)", type=["txt", "csv", "tsv"], accept_multiple_files=True)
    if files:
        files = files[:n_sets]
        for i, file in enumerate(files):
            sets_dict[set_names[i]] = read_file_to_set(file, split_mode, case_sensitive)
else:
    for i in range(n_sets):
        txt = st.text_area(f"Items for {set_names[i]}", height=150)
        sets_dict[set_names[i]] = coerce_items(txt, split_mode, case_sensitive)

if sets_dict and all(len(v) > 0 for v in sets_dict.values()):
    st.subheader("Set Sizes")
    size_df = pd.DataFrame({"Set": list(sets_dict.keys()), "Size": [len(s) for s in sets_dict.values()]})
    st.dataframe(size_df, use_container_width=True)

    st.subheader("Venn Diagram")
    try:
        if n_sets <= 3:
            fig = draw_venn_2_3(sets_dict, set_colors, label_fontsize, number_fontsize, venn_title)
        else:
            fig = draw_venn_4_6(sets_dict, set_colors, venn_title, label_fontsize, number_fontsize)
        st.pyplot(fig)
        fig_download_buttons(fig)
    except Exception as e:
        st.error(f"Error drawing Venn diagram: {e}")

    st.subheader("Intersection Table")
    inter_df = sets_to_intersections(sets_dict)
    st.dataframe(inter_df, use_container_width=True)
    st.download_button("⬇️ Download Intersections", inter_df.to_csv(index=False), file_name="intersections.csv", mime="text/csv")

    st.subheader("Exclusive Elements")
    excl_df = sets_to_exclusive(sets_dict)
    st.dataframe(excl_df, use_container_width=True)
    st.download_button("⬇️ Download Exclusive Elements", excl_df.to_csv(index=False), file_name="exclusive_elements.csv", mime="text/csv")

else:
    st.info("Please upload files or paste lists for each set. Each set must have at least one element.")
