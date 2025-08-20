# venn_app.py
import io
import re
from typing import Dict, Set, List
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
from matplotlib_venn import venn2, venn3
from venn import venn as venn_up_to_6
from upsetplot import plot as upset_plot, from_contents

st.set_page_config(page_title="Multi-Set Venn & Upset Plot App", layout="wide")

# ---------- Utilities ----------
def coerce_items(text: str, split_mode: str, case_sensitive: bool) -> Set[str]:
    if not text:
        return set()
    if split_mode == "Auto":
        parts = re.split(r"[\n,\t;|]+", text)
    elif split_mode == "Newlines (one per line)":
        parts = re.split(r"\n+", text)
    elif split_mode == "Commas":
        parts = re.split(r"+,", text)
    elif split_mode == "Tabs":
        parts = re.split(r"\t+", text)
    elif split_mode == "Semicolons":
        parts = re.split(r";+", text)
    elif split_mode == "Pipes (|)":
        parts = re.split(r"\|+", text)
    else:
        parts = [text]
    return {p.strip().lower() if not case_sensitive else p.strip() for p in parts if p.strip()}

def read_file_to_set(file, split_mode: str, case_sensitive: bool) -> Set[str]:
    try:
        if file.name.lower().endswith(".tsv"):
            df = pd.read_csv(file, sep="\t")
        else:
            df = pd.read_csv(file)
        flat = df.astype(str).values.ravel().tolist()
        text = "\n".join([x for x in flat if x and x.lower() != "nan"])
        return coerce_items(text, split_mode, case_sensitive)
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

def exclusive_elements(sets_dict: Dict[str, Set[str]]) -> Dict[str, List[str]]:
    exclusives = {}
    for key in sets_dict:
        others = set().union(*[s for k, s in sets_dict.items() if k != key])
        exclusives[key] = list(sets_dict[key] - others)
    return exclusives

# ---------- Plot Functions ----------
def draw_venn_2_3(sets_dict, colors, title, title_fontsize, label_fontsize):
    names = list(sets_dict.keys())
    plt.figure(figsize=(7, 6), dpi=180)
    plt.title(title, fontsize=title_fontsize)
    if len(names) == 2:
        v = venn2([sets_dict[names[0]], sets_dict[names[1]]], set_labels=(names[0], names[1]))
    else:
        v = venn3([sets_dict[n] for n in names], set_labels=(names[0], names[1], names[2]))
    for region in v.subset_labels:
        if region:
            region.set_fontsize(label_fontsize)
    for i, subset in enumerate(v.patches):
        if subset:
            subset.set_color(colors[i % len(colors)])
            subset.set_alpha(0.5)
    return plt.gcf()

def draw_venn_4_6(sets_dict, colors, title, title_fontsize, label_fontsize):
    import matplotlib.colors as mcolors
    cmap = mcolors.ListedColormap(colors)
    plt.figure(figsize=(9, 8), dpi=180)
    ax = venn_up_to_6(sets_dict, cmap=cmap)
    for text in ax.texts:
        if text:
            text.set_fontsize(label_fontsize)
    plt.title(title, fontsize=title_fontsize)
    return plt.gcf()

def draw_upset(sets_dict):
    contents = {k: list(v) for k, v in sets_dict.items()}
    upset_data = from_contents(contents)
    fig, ax = plt.subplots(figsize=(10, 5))
    upset_plot(upset_data, ax=ax, orientation='horizontal')
    return fig

def fig_download_buttons(fig):
    col1, col2 = st.columns(2)
    with col1:
        png_buf = io.BytesIO()
        fig.savefig(png_buf, format="png", bbox_inches="tight", dpi=300, transparent=True)
        st.download_button("⬇️ Download PNG", png_buf.getvalue(), file_name="venn_or_upset.png", mime="image/png")
    with col2:
        svg_buf = io.BytesIO()
        fig.savefig(svg_buf, format="svg", bbox_inches="tight")
        st.download_button("⬇️ Download SVG", svg_buf.getvalue(), file_name="venn_or_upset.svg", mime="image/svg+xml")

# ---------- UI ----------
st.title("🧬 Venn / Upset Plot App")

with st.sidebar:
    mode = st.radio("Input type", ["Upload files", "Paste lists"])
    n_sets = st.slider("Number of sets", 2, 6, 3)
    plot_type = st.selectbox("Plot type", ["Venn", "Upset"])
    split_mode = st.selectbox("Split items by", ["Auto", "Newlines (one per line)", "Commas", "Tabs", "Semicolons", "Pipes (|)"])
    case_sensitive = st.checkbox("Case sensitive", value=False)
    title = st.text_input("Plot title", value="My Multi-Set Plot")
    title_fontsize = st.slider("Title font size", 10, 30, 16)
    label_fontsize = st.slider("Label font size", 8, 20, 10)
    set_names = [st.text_input(f"Name for Set {i+1}", value=f"Set {i+1}") for i in range(n_sets)]
    set_colors = [st.color_picker(f"Color for Set {i+1}", value=["#4c78a8", "#f58518", "#54a24b", "#e45756", "#72b7b2", "#b279a2"][i % 6]) for i in range(n_sets)]

sets_dict = {}
if mode == "Upload files":
    files = st.file_uploader("Upload files (one per set)", type=["csv", "tsv", "txt"], accept_multiple_files=True)
    for i, file in enumerate(files[:n_sets]):
        sets_dict[set_names[i]] = read_file_to_set(file, split_mode, case_sensitive)
else:
    for i in range(n_sets):
        text = st.text_area(f"Paste items for {set_names[i]}", height=100)
        sets_dict[set_names[i]] = coerce_items(text, split_mode, case_sensitive)

if sets_dict and all(len(s) > 0 for s in sets_dict.values()):
    st.subheader("Set Sizes")
    st.dataframe(pd.DataFrame({"Set": list(sets_dict.keys()), "Size": [len(s) for s in sets_dict.values()]}))

    st.subheader(f"{plot_type} Plot")
    fig = None
    if plot_type == "Venn":
        if n_sets <= 3:
            fig = draw_venn_2_3(sets_dict, set_colors, title, title_fontsize, label_fontsize)
        else:
            fig = draw_venn_4_6(sets_dict, set_colors, title, title_fontsize, label_fontsize)
    else:
        fig = draw_upset(sets_dict)
    st.pyplot(fig)
    fig_download_buttons(fig)

    st.subheader("Intersections")
    inter_df = sets_to_intersections(sets_dict)
    st.dataframe(inter_df)
    st.download_button("⬇️ Download Intersections CSV", inter_df.to_csv(index=False), file_name="intersections.csv")

    st.subheader("Exclusive Elements")
    excl = exclusive_elements(sets_dict)
    for k, v in excl.items():
        st.download_button(f"⬇️ Download Exclusives for {k}", "\n".join(v), file_name=f"exclusive_{k}.txt")
else:
    st.info("Please provide at least two valid sets.")
