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

from utils import *

filename_dir_s1 = "results-mysql-lseek_fcntl_17_0"
filename_dir_s2 = "results-mysql-lseek_fcntl_17_0-v2"

the_filename = filename_dir_s2

x_adjust, y_adjust, pretty, map_tid2name = get_cmdline(sys.argv)

tid2simple_map = {}
tid2name = {}
simple2name = {}
get_other_name = {}


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
    simple2name[i] = tid2name[tid]




filename = glob.glob(f"{the_filename}/*short*.csv")
filename.sort()

print(tid2name)

for one_file in filename:
    print(one_file)

    df = records_from_csv_file(one_file)
    df.reset_index(level=0, inplace=True)

    name_file = "-".join(one_file.split("/")[-2].split("-")[1:])
    name_file = name_file.replace(':', '-')
    time_per_loop_ms = 15 * 1000 // df["iteration"].max()

    values_to_select = [x for x in df.columns if 'total' in x]

    print(values_to_select)

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

    for option in ["mean"]:
        print("\n\n\n")
        for select_value in values_to_select:
            print("\n")

            get_other_name = {}
            for tid, simple in tid2simple_map.items():
                if map_tid2name is None:
                    get_other_name[simple] = f"{simple}"
                else:
                    get_other_name[simple] = f"{map_tid2name[tid]} {simple}"

            tmp, thread_group_id, order_threads = get_order_thread(df, option, select_value, tid2simple_map, simple2name, get_other_name, pretty)

            tmp["first"] = tmp["first"].apply(lambda x: f"{pretty[simple2name[x]]} {get_other_name[x]}")
            tmp["second"] = tmp["second"].apply(lambda x: f"{pretty[simple2name[x]]} {get_other_name[x]}")

            print(tmp.sort_values(by=select_value, ascending=False).head(7))

            threads = tmp['first'].unique()
            threads.sort()

            def in_my_order(x):
                return [thread_group_id[a] if a in thread_group_id else (-1, -1) for a in x]

            set_config(26, 20, font_scale=3.5)

            #tmp.loc[tmp[select_value] > 5.0, select_value] = 5.0

            df_pivot = tmp.pivot_table(
                index="first",
                columns="second",
                values=select_value,
            )

            df_pivot.sort_index(axis=0, inplace=True, key=in_my_order)
            df_pivot.sort_index(axis=1, inplace=True, key=in_my_order)

            plt.clf()

            df_annot = df_pivot.copy()


            for i, index in enumerate(df_annot.index):
                for j, column in enumerate(df_annot.columns):
                    df_annot[column] = df_annot[column].astype(str)
                    if i % 2 == 1 or j % 2 == 1:
                        df_annot.loc[index, column] = ''
                    else:
                        df_annot.loc[index, column] = str(round(float(df_annot.loc[index, column]), 1))

            splot = sns.heatmap(
                data=df_pivot,
                vmin=0,
                square=True,
                cbar=True,
                linewidths=0,
                cmap="mako_r",
                xticklabels=1,
                yticklabels=1,

                annot=df_annot,
                #annot=False,
                fmt="s",
                annot_kws={"size": 70},
            )

            cmap_ticks = splot.collections[0].colorbar.get_ticks()[:-1]
            if select_value not in ['total', 'total_latency']:
                cmap_ticklabels = [f"{x:.1f}" + r"\%" for x in cmap_ticks]
            else:
                cmap_ticklabels = [f"{x:.1f}" for x in cmap_ticks]
            splot.collections[0].colorbar.set_ticks(cmap_ticks, labels=cmap_ticklabels)

            cur_labels, add_text = change_labels(splot.get_xticklabels(), x_adjust, y_adjust, pinned_y=splot.get_yticks()[-1])
            splot.set_xticklabels(cur_labels)

            for a in add_text:
                splot.text(
                    x=a._x,
                    y=a._y,
                    s=a.get_text(),
                    horizontalalignment="center",
                    fontsize="medium" if not (a._x > 20 and a.get_text() == 'Postgres') else "xx-small",
                )

            cur_labels, add_text = change_labels(splot.get_yticklabels(), x_adjust, y_adjust, pinned_x=splot.get_xticks()[0])
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

            def prettify(select_value):
                my_map = {
                    "total_any_or_0": "accesses (in \%, PA can be 0)",
                    "total_any": "accesses (in \%)",
                    "total_no_miss": "stores and load misses (in \%)",
                    "total": "accesses (ops)",

                    "total_any_or_0_latency": "latency (in \%, PA can be 0)",
                    "total_any_latency": "latency (in \%)",
                    "total_no_miss_latency": "latency of stores and load misses (in \%)",
                    "total_latency": "latency (ops)",
                }
                return my_map[select_value]

            splot.set_title(f"{prettify(select_value)} for pair (Ta, Tb) - {time_per_loop_ms} ms")
            splot.set_xlabel("Thread Ta")
            splot.set_ylabel("Thread Tb")

            splot.yaxis.set_label_coords(-0.15, 0.5)
            splot.xaxis.set_label_coords(0.5, -0.15)

            plt.savefig(
                f"out/{name_file}_{option}_sharing_coefficient_{time_per_loop_ms}_{select_value}.pdf",
                bbox_inches="tight",
                transparent=False,
                facecolor="white",
            )
