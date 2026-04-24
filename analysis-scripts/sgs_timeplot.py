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

x_adjust, y_adjust, pretty, map_tid2name, select_time, allowed_threads, min_limit_iter, max_limit_iter = get_cmdline_timeplot(sys.argv)

filename_dir_s1 = "results-mysql-lseek_fcntl_17_0"

the_filename = filename_dir_s1

tid2simple_map = {}
tid2name = {}
simple2name = {}
sorted2name = {}






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
