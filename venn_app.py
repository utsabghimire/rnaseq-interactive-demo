# venn_app.py
import io
import re
from typing import Dict, List, Set, Tuple

import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt

# For up to 3 sets (exact Venn)
from matplotlib_venn import venn2, venn3

# For 4–6 sets (approximate Venn)
from venn import venn as venn_up_to_6


st.set_page_config(page_title="Multi-Set Venn (up to 6)", layout="wide")


# -----------------------------
# Helpers
# -----------------------------
def coerce_items(text: str, split_mode: str, case_sensitive: bool) -> Set[str]:
    if not text:
        return set()
    if split_mode == "Auto":
        # split by newline or comma or tab/semicolon/pipe
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
    # Try CSV/TSV with header; fall back to plain text list
    try:
        if file.name.lower().endswith((".tsv",)):
            df = pd.read_csv(file, sep="\t")
        else:
            df = pd.read_csv(file)
        # If there is exactly one column, take it; otherwise ask user to select later (handled below)
        if df.shape[1] == 1:
            col = df.columns[0]
            series = df[col].dropna().astype(str).tolist()
            text = "\n".join(series)
            return coerce_items(text, "Newlines (one per line)", case_sensitive)
        else:
            # If multi-column, flatten all non-empty cells to strings
            flat = df.astype(str).values.ravel().tolist()
            text = "\n".join([x for x in flat if x and x.lower() != "nan"])
            return coerce_items(text, "Newlines (one per line)", case_sensitive)
    except Exception:
        # Plain text
        file.seek(0)
        text = file.read().decode("utf-8", errors="ignore")
        return coerce_items(text, split_mode, case_sensitive)


def sets_to_intersections(sets_dict: Dict[str, Set[str]]) -> pd.DataFrame:
    """Return a table of intersections for all non-empty combinations."""
    names = list(sets_dict.keys())
    data = []
    n = len(names)
    from itertools import combinations
    for k in range(1, n + 1):
        for comb in combinations(names, k):
            inter = set.intersection(*(sets_dict[name] for name in comb))
            # Subtract elements that appear in supersets to report exact regions?
            # For simplicity show raw intersections by combo.
            data.append({
                "Sets": " ∩ ".join(comb),
                "Size": len(inter)
            })
    df = pd.DataFrame(data).sort_values(["Size", "Sets"], ascending=[False, True])
    return df


def draw_venn_2_3(sets_dict: Dict[str, Set[str]], colors: List[str]):
    names = list(sets_dict.keys())
    n = len(names)
    assert n in (2, 3)
    plt.figure(figsize=(7, 6), dpi=180)
    if n == 2:
        a, b = sets_dict[names[0]], sets_dict[names[1]]
        v = venn2([a, b], set_labels=(names[0], names[1]))
        # color each set
        if v.get_patch_by_id("10"): v.get_patch_by_id("10").set_color(colors[0]); v.get_patch_by_id("10").set_alpha(0.5)
        if v.get_patch_by_id("01"): v.get_patch_by_id("01").set_color(colors[1]); v.get_patch_by_id("01").set_alpha(0.5)
        if v.get_patch_by_id("11"): v.get_patch_by_id("11").set_color(colors[0]); v.get_patch_by_id("11").set_alpha(0.3)
    else:
        a, b, c = [sets_dict[n] for n in names]
        v = venn3([a, b, c], set_labels=(names[0], names[1], names[2]))
        # set-specific base colors with alpha; overlaps get blended appearance
        base_ids = {"100": 0, "010": 1, "001": 2}
        for rid, idx in base_ids.items():
            patch = v.get_patch_by_id(rid)
            if patch:
                patch.set_color(colors[idx])
                patch.set_alpha(0.5)
        # overlaps slightly more transparent
        for rid in ("110", "101", "011", "111"):
            patch = v.get_patch_by_id(rid)
            if patch:
                patch.set_alpha(0.35)
    st.pyplot(plt.gcf(), use_container_width=True)
    return plt.gcf()


def draw_venn_4_6(sets_dict: Dict[str, Set[str]], colors: List[str]):
    # The 'venn' package supports up to 6 sets (approximate). It uses a colormap for regions.
    # We’ll build a custom ListedColormap that cycles the chosen set colors for visual consistency.
    import matplotlib.colors as mcolors
    # Create a long colormap from chosen colors; regions > len(colors) will reuse
    cmap = mcolors.ListedColormap(colors)
    plt.figure(figsize=(9, 8), dpi=180)
    ax = venn_up_to_6(sets_dict, cmap=cmap)  # draws on current axes
    # Label style tweaks
    for text in ax.texts:
        text.set_fontsize(10)
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
    n_sets = st.slider("Number of sets", 2, 6, 3, help="Venn diagrams need ≥2 sets")

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
            set_names.append(st.text_input(f"Name for Set {i+1}", value=default_names[i], key=f"name_{i}"))
            set_colors.append(st.color_picker(f"Color for {default_names[i]}", value=["#4c78a8", "#f58518", "#54a24b", "#e45756", "#72b7b2", "#b279a2"][i % 6], key=f"color_{i}"))
    st.caption("Tip: Colors apply per-set for 2–3 set diagrams; 4–6 sets use an approximate layout with a colormap derived from your picks.")

# Collect sets
sets_dict: Dict[str, Set[str]] = {}

if mode == "Upload files":
    files = st.file_uploader(
        f"Upload up to {n_sets} files (TXT/CSV/TSV). Each file represents **one set**.",
        type=["txt", "csv", "tsv"], accept_multiple_files=True
    )
    if files:
        # Use first n_sets files
        files = files[:n_sets]
        for i, f in enumerate(files):
            items = read_file_to_set(f, split_mode, case_sensitive)
            sets_dict[set_names[i]] = items
elif mode == "Paste lists":
    cols = st.columns(min(3, n_sets))
    text_blobs: List[str] = ["" for _ in range(n_sets)]
    for i in range(n_sets):
        text_blobs[i] = st.text_area(f"Items for {set_names[i]} (one per line or separated by your chosen delimiter)",
                                     height=140, key=f"paste_{i}")
    for i in range(n_sets):
        sets_dict[set_names[i]] = coerce_items(text_blobs[i], split_mode, case_sensitive)

# Show sizes and proceed
if sets_dict and all(len(s) > 0 for s in sets_dict.values()):
    st.subheader("Set sizes")
    size_df = pd.DataFrame({"Set": list(sets_dict.keys()), "Size": [len(s) for s in sets_dict.values()]})
    st.dataframe(size_df, use_container_width=True)

    st.subheader("Venn diagram")
    n = len(sets_dict)
    fig = None
    try:
        if n in (2, 3):
            fig = draw_venn_2_3(sets_dict, set_colors[:n])
        else:
            fig = draw_venn_4_6(sets_dict, set_colors[:n])
    except Exception as e:
        st.error(f"Could not draw Venn: {e}")

    if fig:
        fig_download_buttons(fig)

    st.subheader("Intersection sizes")
    inter_df = sets_to_intersections(sets_dict)
    st.dataframe(inter_df, use_container_width=True)

else:
    st.info("Add content for each set (upload files or paste lists). Each set must contain at least one item.")
