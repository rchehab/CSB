#!/usr/bin/env python
# coding: utf-8

import ast
import glob
import sys
from typing import Optional

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

def get_cmdline(argv):
    if len(argv) == 4:
        _, x_adjust, y_adjust, pretty_str = sys.argv
        map_tid2name = None
    elif len(sys.argv) == 5:
        _, x_adjust, y_adjust, pretty_str, map_tid2name = sys.argv
        map_tid2name = ast.literal_eval(map_tid2name)
    else:
        print("Usage: ./11_heatmap.py <x-axis-adj> <y-axis-adj> <map pretty> <map tid2name>")
        exit(1)

    x_adjust = float(x_adjust)
    y_adjust = float(y_adjust)
    pretty = ast.literal_eval(pretty_str)

    return x_adjust, y_adjust, pretty, map_tid2name

def set_config(width=8, height=6, font_scale=1.15):
    sns.set_theme(
        context="talk",
        style="whitegrid",
        palette="colorblind",
        font_scale=font_scale,
        rc={
            "figure.figsize": (width, height),
            "pdf.fonttype": 42,
            "pdf.use14corefonts": True,
            "text.usetex": True,
        },
    )


def records_from_csv_file(csv_path):
    records_from_file = pd.read_csv(csv_path, sep=";", comment="#", low_memory=False)

    return records_from_file

def change_labels(
    labels,
    x_adjust,
    y_adjust,
    pinned_x: Optional[float] = None,
    pinned_y: Optional[float] = None,
):

    if pinned_x is not None:
        pinned_x = pinned_x + x_adjust
    elif pinned_y is not None:
        pinned_y = pinned_y + y_adjust
    else:
        raise ValueError("Needs to pass either pinned_x or _y")

    interval = {
        "name": None,
        "start": None,
        "end": None,
    }

    add_to_label = []

    def setup_text(start, end, name):
        add_to_label.append(
            plt.Text(
                x=pinned_x if pinned_x else (labels[start]._x + labels[end]._x) / 2,
                y=pinned_y if pinned_y else (labels[start]._y + labels[end]._y) / 2,
                text=name,
            )
        )

        add_to_label.append(
            plt.Text(
                x=pinned_x if pinned_x else labels[start]._x,
                y=pinned_y if pinned_y else labels[start]._y,
                text="]" if pinned_x else "[",
            )
        )
        add_to_label.append(
            plt.Text(
                x=pinned_x if pinned_x else labels[end]._x,
                y=pinned_y if pinned_y else labels[end]._y,
                text="[" if pinned_x else "]",
            )
        )

    for i, a in enumerate(labels):
        name = " ".join(a.get_text().split()[:-1])
        tid = a.get_text().split()[-1]

        if name == interval["name"]:
            labels[i].set_text(str(int(tid)))
            labels[i].set_fontsize("small")
        else:
            if interval["start"] != interval["end"]:
                setup_text(interval["start"], interval["end"], interval["name"])
                labels[interval["start"]].set_text(str(int(interval["tid"])))
                labels[interval["start"]].set_fontsize("small")
            else:
                if interval["start"] is not None:
                    labels[interval["start"]].set_text(
                        interval["name"] + " " + str(int(interval["tid"]))
                    )
                    labels[interval["start"]].set_fontsize("small")

                labels[i].set_text(name + " " + str(int(tid)))
                labels[i].set_fontsize("small")

            interval["name"] = name
            interval["start"] = i
            interval["tid"] = tid
        interval["end"] = i

    if interval["start"] != interval["end"]:
        setup_text(interval["start"], interval["end"], interval["name"])
        labels[interval["start"]].set_text(str(int(interval["tid"])))
        labels[interval["start"]].set_fontsize("small")
    else:
        labels[i].set_text(name + " " + str(int(tid)))
        labels[i].set_fontsize("small")

    return labels, add_to_label

### Define important functions
def get_pairs(df, select_value, tid2simple_map):
    df["first"] = df["first_original"].apply(lambda x: tid2simple_map[x])
    df["second"] = df["second_original"].apply(lambda x: tid2simple_map[x])

def init_unionfind(element):
    return [element, 1, -1]

def find(group, element):
    if group[element][0] == element:
        return element

    group[element][0] = find(group, group[element][0])

    return group[element][0]

def join(group, a, b):
    a = find(group, a)
    b = find(group, b)

    if a == b:
        return

    if group[a][1] < group[b][1]:
        group[a][0] = b
        group[a][1] = group[a][1] + group[b][1]
    else:
        group[b][0] = a
        group[a][1] = group[a][1] + group[b][1]

def get_order_thread(df, which, select_value, tid2simple_map, simple2name, get_other_name, pretty):
    tmp = df.copy()
    if which == 'mean':
        tmp = tmp.groupby(["first_original", "second_original"])[select_value].agg(["mean", "count"]).reset_index()
        tmp = tmp.rename(columns={"mean": select_value})
    else:
        tmp = tmp.groupby(["first_original", "second_original"])[select_value].agg(["sum", "count"]).reset_index()
        tmp = tmp.rename(columns={"sum": select_value})
    tmp = tmp[tmp['count'] > tmp['count'].max() / 10]

    get_pairs(tmp, select_value, tid2simple_map)
    tmp = tmp.sort_values(by=select_value, ascending=False)

    threads = list(set(list(tmp["first"].unique()) + list(tmp["second"].unique())))
    threads.sort()

    groups = {
        10: {},
        25: {},
        50: {},
        75: {},
        89: {},
        94: {},
    }

    for thread in threads:
        for key, value in groups.items():
            groups[key][thread] = init_unionfind(thread)

    for i, row in tmp.iterrows():
        first = int(row["first"])
        second = int(row["second"])
        value = row[select_value]

        for key in groups.keys():
            if groups[key][first][2] == -1:
                groups[key][first][2] = value

            if groups[key][second][2] == -1:
                groups[key][second][2] = value

            a = groups[key][first][2]
            b = groups[key][second][2]
            c = value

            if (max(a, b, c) - min(a, b, c)) <= ((key * max(a, b, c)) / 100):
                join(groups[key], first, second)

    keys_ord = list(groups.keys())
    keys_ord.sort(reverse=True)

    sharing_groups = []

    for thread in threads:
        group_level = []
        for key in keys_ord:
            group_level.append(find(groups[key], thread))
        group_level.append(thread)

        sharing_groups.append(tuple(group_level))

    sharing_groups.sort()

    order_threads = {}
    thread_group_id = {}

    sorted2name = {}
    for i, value in enumerate(sharing_groups):
        thread = value[-1]
        order_threads[thread] = i

        new_name = simple2name[thread]
        new_name = pretty[new_name] if new_name in pretty else new_name

        if i not in sorted2name:
            sorted2name[i] = new_name

        thread_group_id[f"{new_name} {get_other_name[thread]}"] = tuple(value)

    #NOTED: sorted2name is never returned
    return tmp, thread_group_id, order_threads

### END define important functions
