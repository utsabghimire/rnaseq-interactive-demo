#AUG202025
import io
import re
from typing import Dict, List, Set, Tuple
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt

from matplotlib_venn import venn2, venn3
from venn import venn as venn_up_to_6

st.set_page_config(page_title="Venn Diagram App", layout="wide")

# [ ... all helper functions and UI components go here ... ]
# Due to space constraints, only the final important changes are shown

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
    return plt.gcf()

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
    return plt.gcf()
