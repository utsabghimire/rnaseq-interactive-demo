import io
import re
from typing import Dict, List, Set, Tuple
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt

from matplotlib_venn import venn2, venn3
from venn import venn as venn_up_to_6

st.set_page_config(page_title="Venn Diagram App", layout="wide")

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

def exclusive_to_each_set(sets_dict: Dict[str, Set[str]]) -> Dict[str, Set[str]]:
    exclusives = {}
    for key, target_set in sets_dict.items():
        others = [v for k, v in sets_dict.items() if k != key]
        union_others = set().union(*others)
        exclusives[key] = target_set - union_others
    return exclusives

def draw_venn_2_3(sets_dict, colors, title, title_fontsize, label_fontsize, label_fontstyle, region_colors):
    names = list(sets_dict.keys())
    n = len(names)
    plt.figure(figsize=(7, 6), dpi=180)
    if n == 2:
        v = venn2([sets_dict[names[0]], sets_dict[names[1]]], set_labels=('', ''))
        region_ids = {"10": [names[0]], "01": [names[1]], "11": [names[0], names[1]]}
    else:
        v = venn3([sets_dict[n] for n in names], set_labels=('', '', ''))
        region_ids = {
            "100": [names[0]], "010": [names[1]], "001": [names[2]],
            "110": [names[0], names[1]], "101": [names[0], names[2]],
            "011": [names[1], names[2]], "111": [names[0], names[1], names[2]]
        }
    for rid, combo in region_ids.items():
        patch = v.get_patch_by_id(rid)
        if patch:
            color = region_colors.get(" ∩ ".join(combo), None)
            if color:
                patch.set_color(color)
                patch.set_alpha(0.5)
    for label in v.subset_labels:
        if label:
            label.set_fontsize(label_fontsize)
            label.set_fontstyle(label_fontstyle)
    centers = v.centers
    for i, name in enumerate(names):
        if i < len(centers):
            x, y = list(centers.values())[i]
            plt.annotate(name, xy=(x, y + 0.25), ha='center', fontsize=label_fontsize + 2, fontstyle=label_fontstyle)
    plt.title(title, fontsize=title_fontsize)
    st.pyplot(plt.gcf(), use_container_width=True)

def draw_venn_4_6(sets_dict, colors, title, title_fontsize, label_fontsize, set_names):
    import matplotlib.colors as mcolors
    cmap = mcolors.ListedColormap(colors)
    plt.figure(figsize=(9, 8), dpi=180)
    ax = venn_up_to_6(sets_dict, cmap=cmap)
    for text in ax.texts:
        if text:
            text.set_fontsize(label_fontsize)
    plt.title(title, fontsize=title_fontsize)
    used = set()
    for text in ax.texts:
        label = text.get_label()
        if label and label.isdigit():
            x, y = text.get_position()
            overlap_sets = text.get_label().split('∩')
            if len(overlap_sets) == 1 and overlap_sets[0] not in used:
                used.add(overlap_sets[0])
                plt.annotate(overlap_sets[0], (x, y + 0.2), ha='center', fontsize=label_fontsize + 2, fontweight='bold')
    st.pyplot(plt.gcf(), use_container_width=True)

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
st.title("Venn Diagram Builder (up to 6 sets)")

with st.sidebar:
    st.header("Input Options")
    mode = st.radio("Input mode", ["Upload files", "Paste lists"])
    n_sets = st.slider("Number of sets", 2, 6, 3)
    split_mode = st.selectbox("Split items by", ["Auto", "Newlines (one per line)", "Commas", "Tabs", "Semicolons", "Pipes (|)"])
    case_sensitive = st.checkbox("Case sensitive matching", value=False)
    default_names = [f"Set {i+1}" for i in range(n_sets)]
    set_names, set_colors = [], []
    for i in range(n_sets):
        set_names.append(st.text_input(f"Label for Set {i+1}", default_names[i], key=f"label_{i}"))
        set_colors.append(st.color_picker(f"Color for Set {i+1}", ["#4c78a8", "#f58518", "#54a24b", "#e45756", "#72b7b2", "#b279a2"][i % 6], key=f"color_{i}"))
    title = st.text_input("Venn Title", "Venn Diagram")
    title_fontsize = st.slider("Title font size", 10, 40, 20)
    label_fontsize = st.slider("Label font size", 6, 20, 10)
    label_fontstyle = st.selectbox("Label font style", ["normal", "italic", "oblique"])
    region_colors = {}
    if n_sets <= 3:
        from itertools import combinations
        for k in range(1, n_sets + 1):
            for comb in combinations(set_names, k):
                region_colors[" ∩ ".join(comb)] = st.color_picker(f"Color for {' ∩ '.join(comb)}", "#cccccc", key=f"region_{'_'.join(comb)}")

sets_dict: Dict[str, Set[str]] = {}
if mode == "Upload files":
    files = st.file_uploader("Upload files (TXT/CSV/TSV)", type=["txt", "csv", "tsv"], accept_multiple_files=True)
    if files:
        for i, f in enumerate(files[:n_sets]):
            sets_dict[set_names[i]] = read_file_to_set(f, split_mode, case_sensitive)
elif mode == "Paste lists":
    for i in range(n_sets):
        txt = st.text_area(f"Items for {set_names[i]}", height=120, key=f"paste_{i}")
        sets_dict[set_names[i]] = coerce_items(txt, split_mode, case_sensitive)

if sets_dict and all(len(s) > 0 for s in sets_dict.values()):
    st.markdown(f"### {title}")
    st.subheader("Set Sizes")
    st.dataframe(pd.DataFrame({"Set": list(sets_dict.keys()), "Size": [len(s) for s in sets_dict.values()]}))

    fig = None
    if n_sets in (2, 3):
        fig = draw_venn_2_3(sets_dict, set_colors[:n_sets], title, title_fontsize, label_fontsize, label_fontstyle, region_colors)
    else:
        fig = draw_venn_4_6(sets_dict, set_colors[:n_sets], title, title_fontsize, label_fontsize, set_names)
    if fig:
        fig_download_buttons(fig)

    st.subheader("Intersection Sizes")
    inter_df, inter_dict = sets_to_intersections(sets_dict)
    st.dataframe(inter_df, use_container_width=True)

    for combo, items in inter_dict.items():
        if items:
            txt = "\n".join(sorted(items))
            st.download_button(f"⬇️ Download: {combo} ({len(items)})", txt, file_name=f"intersection_{combo.replace(' ∩ ', '_')}.txt")

    st.subheader("Exclusive Items")
    exclusive_dict = exclusive_to_each_set(sets_dict)
    for name, items in exclusive_dict.items():
        if items:
            txt = "\n".join(sorted(items))
            st.download_button(f"⬇️ Download unique to {name} ({len(items)})", txt, file_name=f"exclusive_{name}.txt")
else:
    st.info("Please provide at least one valid item in each set.")
