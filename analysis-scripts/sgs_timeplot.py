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

if len(sys.argv) == 5:
    _, x_adjust, min_limit_iter, max_limit_iter, pretty_str = sys.argv
    select_time = False
    allowed_threads = False
elif len(sys.argv) == 6:
    _, x_adjust, min_limit_iter, max_limit_iter, pretty_str, allowed_threads = sys.argv
    select_time = False
    allowed_threads = ast.literal_eval(allowed_threads)
elif len(sys.argv) == 7:
    _, x_adjust, min_limit_iter, max_limit_iter, pretty_str, allowed_threads, select_time = sys.argv
    allowed_threads = ast.literal_eval(allowed_threads)
else:
    print("Usage: ./12_timeplot.py <x-axis-adj> <limit maximum iteration> <map pretty> [select time period]")
    exit(1)

map_tid2name = None
x_adjust = float(x_adjust)
min_limit_iter = int(min_limit_iter)
max_limit_iter = int(max_limit_iter)
pretty = ast.literal_eval(pretty_str)

filename_dir_s1  = "leveldb-results-search-1000ms"
filename_dir_s2  = "leveldb-results-search-950ms"
filename_dir_s3  = "leveldb-results-search-900ms"
filename_dir_s4  = "leveldb-results-search-850ms"
filename_dir_s5  = "leveldb-results-search-800ms"
filename_dir_s6  = "leveldb-results-search-750ms"
filename_dir_s7  = "leveldb-results-search-700ms"
filename_dir_s8  = "leveldb-results-search-650ms"
filename_dir_s9  = "leveldb-results-search-600ms"
filename_dir_s10 = "leveldb-results-search-550ms"
filename_dir_s11 = "leveldb-results-search-500ms"
filename_dir_s12 = "leveldb-results-search-450ms"
filename_dir_s13 = "leveldb-results-search-400ms"
filename_dir_s14 = "leveldb-results-search-350ms"
filename_dir_s15 = "leveldb-results-search-300ms"
filename_dir_s16 = "leveldb-results-search-250ms"
filename_dir_s17 = "leveldb-results-search-250ms"
filename_dir_s18 = "leveldb-results-search-150ms"
filename_dir_s19 = "leveldb-results-search-100ms"
filename_dir_s20 = "results-cloudsuite-v2"

the_filename = filename_dir_s20

tid2simple_map = {}
tid2name = {}
simple2name = {}
sorted2name = {}



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

def get_pairs(df, select_value):
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

def get_order_thread(df, select_value):
    tmp = df.copy()

    tmp = tmp.groupby(["first_original", "second_original"])[select_value].agg(["mean", "count"]).reset_index()
    tmp = tmp.rename(columns={"mean": select_value})

    tmp = tmp[tmp['count'] > tmp['count'].max() / 10]

    get_pairs(tmp, select_value)
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

    for i, value in enumerate(sharing_groups):
        thread = value[-1]
        order_threads[thread] = i

        new_name = simple2name[thread]
        new_name = pretty[new_name] if new_name in pretty else new_name

        if i not in sorted2name:
            sorted2name[i] = new_name

        thread_group_id[f"{new_name} {thread:>0{3}}"] = tuple(value)

    return tmp, thread_group_id, order_threads

### END define important functions



















filename = glob.glob(f"{the_filename}/*map*.txt")

for file in filename:

    def is_ascii(s):
        return len(s) == len(s.encode())

    with open(file, errors="replace") as f:
        a = f.readline()
        if a.split() == [] or not is_ascii(a) or "/" not in a:
            name = "unknown"
        else:
            name = a.split()[-1]

        thread = file.split("_")[-1].split(".")[0]

        tid2name[int(thread)] = name.split("/")[-1]





all_threads = [k for k, v in tid2name.items() if v in pretty]
all_threads.sort()

for i, tid in enumerate(all_threads):
    tid2simple_map[tid] = i

    tid2simple_map[tid] = i
    simple2name[i] = tid2name[tid]




filename = glob.glob(f"{the_filename}/*short*.csv")
filename.sort()

for one_file in filename:
    print(one_file)

    if select_time and select_time not in one_file:
        continue

    df = records_from_csv_file(one_file)
    df.reset_index(level=0, inplace=True)

    name_file = "-".join(one_file.split("/")[-2].split("-")[1:])
    name_file = name_file.replace(':', '-')
    time_per_loop_ms = 15 * 1000 // df["iteration"].max()

    if time_per_loop_ms == 0:
        time_per_loop_ms = 10 * 15 * 1000 // df["iteration"].max()
        time_per_loop_ms = time_per_loop_ms / 10

    df['iteration'] = df['iteration'] * time_per_loop_ms
    df['iteration'] = df['iteration'].apply(lambda x: round(x))

    values_to_select = ['total_any']

    df["first"] = df["pair_of_threads"].apply(lambda x: int(x.split(" - ")[0]))
    df["second"] = df["pair_of_threads"].apply(lambda x: int(x.split(" - ")[1]))
    df = df.groupby(["first", "second", "iteration"])[values_to_select].sum().reset_index()

    df = df[df["first"].apply(lambda x: True if x in tid2name else False)]
    df = df[df["first"].apply(lambda x: True if tid2name[x] in pretty else False)]

    df = df[df["second"].apply(lambda x: True if x in tid2name else False)]
    df = df[df["second"].apply(lambda x: True if tid2name[x] in pretty else False)]

    filt = df['first'] == df['second']
    for select_value in values_to_select:
        df.loc[filt, select_value] = 0

    df['first_original'] = df['first']
    df['second_original'] = df['second']


    for select_value in values_to_select:
        print("\n")
        tmp, thread_group_id, order_threads = get_order_thread(df, select_value)

        get_other_name = {}
        for tid, simple in tid2simple_map.items():
            if map_tid2name is None:
                get_other_name[simple] = f"{simple}"
            else:
                get_other_name[simple] = f"{map_tid2name[tid]} {simple}"

        def get_name(x):
            if x in get_other_name and x in simple2name and simple2name[x] in pretty:
                return f"{pretty[simple2name[x]]} {get_other_name[x]}"
            return "other"

        df["first"] = df["first"].apply(lambda x: tid2simple_map[x] if x in tid2simple_map else -1)
        df["second"] = df["second"].apply(lambda x: tid2simple_map[x] if x in tid2simple_map else -1)

        df["first"] = df["first"].apply(get_name)
        df["second"] = df["second"].apply(get_name)

        df_f = df
        df_f = df_f[df_f['first'] != 'other']
        df_f = df_f[df_f['second'] != 'other']

        min_iter = df_f['iteration'].min()
        max_iter = df_f['iteration'].max()

        # Make sure that all thread have same start/end iterations
        my_map = {
            'first': [],
            'second': [],
            'iteration': [],
            'total_any': [],
        }

        for tid in df_f['first'].unique():
            for iteration in range(min_iter, max_iter + 1, round(time_per_loop_ms)):
                my_map['first'].append(tid)
                my_map['second'].append(tid)
                my_map['iteration'].append(iteration)
                my_map['total_any'].append(0.0)
            for second in df_f['second'].unique():
                my_map['first'].append(tid)
                my_map['second'].append(second)
                my_map['iteration'].append(min_iter)
                my_map['total_any'].append(0.0)

        #df_ff = df_f
        df_ff = pd.concat([df_f, pd.DataFrame.from_dict(my_map)])
        df_ff = df_ff.groupby(['first', 'second', 'iteration'])['total_any'].sum().reset_index()

        print(tid2simple_map)

        for i, first_thr in enumerate(df_f['first'].unique()):
            set_config(20, 20, font_scale=2.0)

            print(first_thr)

            if allowed_threads != False and i not in allowed_threads:
                continue

            tmp = df_ff[df_ff["first"] == first_thr]

            tmp = tmp[tmp['iteration'] > min_limit_iter]
            tmp = tmp[tmp['iteration'] < max_limit_iter]

            df_pivot = tmp.pivot_table(
                index="second",
                columns="iteration",
                values=select_value,
            )

            def label2num(x):
                return int(x.split(' ')[-1])

            def get_int(x):
                return [label2num(a) for a in x]

            df_pivot.sort_index(axis=0, inplace=True, key=get_int)
            df_pivot.sort_index(axis=1, inplace=True)

            plt.clf()

            splot = sns.heatmap(
                data=df_pivot,
                vmin=0,
                square=False,
                cbar=True,
                linewidths=0,
                cmap="mako_r",
                #yticklabels=1,
            )

            cmap_ticks = splot.collections[0].colorbar.get_ticks()[:-1]
            if select_value not in ['total', 'total_latency']:
                cmap_ticklabels = [f"{x:.1f}" + r"\%" for x in cmap_ticks]
            else:
                cmap_ticklabels = [f"{x:.1f}" for x in cmap_ticks]
            splot.collections[0].colorbar.set_ticks(cmap_ticks, labels=cmap_ticklabels)

            labels = splot.get_yticklabels()

            x0 = label2num(labels[0].get_text())
            f0 = labels[0]._y

            xm = label2num(labels[-1].get_text())
            fm = labels[-1]._y

            y_place = f0 + label2num(first_thr) * (fm - f0) / xm

            plt.axhline(y=y_place, color='red', linewidth=10)

            cur_labels, add_text = change_labels(splot.get_yticklabels(), pinned_x=splot.get_xticks()[0])
            splot.set_yticklabels(cur_labels)

            for a in add_text:
                splot.text(
                    x=a._x,
                    y=a._y,
                    s=a.get_text(),
                    verticalalignment="center",
                    rotation="vertical",
                    fontsize="medium" if not (a._y > 20 and a.get_text() == 'Postgres') else "xx-small",
                )

            ############################
            splot.set_title(f"Data Sharing for (Tred, Tb) over time - {time_per_loop_ms} ms")
            splot.set_xlabel("Time (ms)")
            splot.set_ylabel("Thread Tb")

            splot.yaxis.set_label_coords(-0.15, 0.5)
            splot.xaxis.set_label_coords(0.5, -0.15)

            plt.savefig(
                f"out/{name_file}_{time_per_loop_ms}_{select_value}_for_thread_{first_thr.replace(' ', '-')}.pdf",
                bbox_inches="tight",
                transparent=False,
                facecolor="white",
            )
