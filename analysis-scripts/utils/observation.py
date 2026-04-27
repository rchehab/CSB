#!/usr/bin/env python

import ast
import glob
import sys
from typing import Optional

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

import seaborn as sns

from utils import set_config

def no_thread(list_pcs):
    if type(list_pcs) == float:
        print(list_pcs)
        return '-1'
    my_list = list(set([a.split(',')[0] for a in list_pcs.split(' | ')]))
    my_list.sort()
    #return [a.split(',')[0] for a in list_pcs.split(' | ')]
    return ' '.join(my_list)

def total_count(counts):
    
    if isinstance(counts, int):
        return counts
    
    s = counts.split(' | ')
    total_count = 0
    
    for a in s:
        total_count = total_count + int(a)
    
    return total_count

def change_pa(pa, to_what = 'cacheline'):
    if to_what == 'cacheline':
        erase = 7
    elif to_what == 'page':
        erase = 11
    else:
        return
    
    pa = list(pa)
    i = -1
    while (erase >= 4):
        pa[i] = '0'
        i = i - 1
        erase = erase - 4
        
    pa[i] = int(pa[i], 16) 
    j = 1
    while erase:
        pa[i] = pa[i] & (~j)
        j = j * 2
        erase = erase - 1
    pa[i] = str(pa[i])
    
    return ''.join(pa)
    
def change_to_cache(pa):
    return change_pa(pa, to_what = 'cacheline')
    
def change_to_page(pa):
    return change_pa(pa, to_what = 'page')

def calculate_avg_latency(df):
    df['avg_latency'] = df['total_latency'] / df['total_count']
            
def calculate_bucket(df):
    calculate_avg_latency(df)
    df['latency bucket'] = df['avg_latency'].apply(lambda x: round(x / 10) * 10);

def calc_cumul_latency(df):
    df['cumul_total_latency'] = 0.0
    df['cumul_total_count'] = 0.0

    cumul_total_latency = 0.0
    cumul_total_count = 0.0

    for index, row in df.iterrows():
        cumul_total_latency = cumul_total_latency + row['total_latency']
        cumul_total_count = cumul_total_count + row['total_count']
        
        df.loc[index, 'cumul_total_latency'] = cumul_total_latency
        df.loc[index, 'cumul_total_count'] = cumul_total_count

    df['cumul_avg_latency'] = df['cumul_total_latency'] / df['cumul_total_count']

def get_one_per_type_df(df):

    lt_list = [x for x in df.columns if 'latency' in x and '_' not in x]
    cnt_list = [x.split(' latency')[0] for x in lt_list]
    lt_list.append('total_latency')
    cnt_list.append('total_count')

    per_type_latency = df[lt_list].sum().reset_index()
    per_type_latency = per_type_latency.rename(columns={'index': 'type', 0: 'latency'})

    per_type_count = df[cnt_list].sum().reset_index()
    per_type_count = per_type_count.rename(columns={'index': 'type', 0: 'count'})

    per_type_latency['type'] = per_type_latency['type'].apply(lambda x: x if 'total' not in x else 'total')
    per_type_count['type'] = per_type_count['type'].apply(lambda x: x if 'total' not in x else 'total')

    per_type = per_type_latency
    per_type['count'] = per_type_count['count']
    per_type['avg_latency'] = per_type['latency'] / per_type['count']
    
    return per_type















def get_latency_histogram(df_array, name, filename, x_axis = 'latency bucket'):
    set_config(16, 7, font_scale=1.15)
    
    plot, axes = plt.subplots(1, len(df_array))

    for j, df in enumerate(df_array):
        df_buc = df.groupby(x_axis)[['total_latency', 'total_count']].sum().reset_index();
        calc_cumul_latency(df_buc)

        def get_axes(axes, j):
            if len(df_array) == 1:
                return axes
            else:
                return axes[j]

        splot = sns.lineplot(
            data=df_buc,

            x=x_axis,
            y='cumul_total_latency',

            legend='full' if (j == 0) else None,

            errorbar=('ci', 95),
            linewidth = 2,
            ax = get_axes(axes, j)
        )

        x_max = df_buc[x_axis].max()
        y_max = df_buc['cumul_total_latency'].max()
        
        splot.set_xlim([0, x_max * 1.05])
        splot.set_ylim([0, y_max * 1.05])
        splot.set_yticks([
            0.50 * y_max,
            0.75 * y_max,
            0.90 * y_max,
            0.95 * y_max,
            0.99 * y_max])

        axes2 = get_axes(axes, j).secondary_yaxis('right')
        axes2.tick_params(axis="y", length=8)
        axes2.set_yticks([
            0.50 * y_max,
            0.75 * y_max,
            0.90 * y_max,
            0.95 * y_max,
            0.99 * y_max])
        
        axes2.set_yticklabels([
            '50\%',
            '75\%',
            '90\%',
            '95\%',
            '99\%',
        ])

        splot.set_title(f"Cumulative latency over time")
        splot.set_xlabel(f"Sorted by '{x_axis}'")
        splot.set_ylabel("Cumulative Latency")
        get_axes(axes, j).ticklabel_format(style='plain')
    
    l_handles, l_labels = get_axes(axes, 0).get_legend_handles_labels()
    if get_axes(axes, 0).get_legend():
        get_axes(axes, 0).get_legend().remove()

    plot.legend(
        l_handles,
        l_labels,
        ncols=2,
        loc='lower center',
        bbox_to_anchor=(0.5, -0.12),
        title_fontsize='large',
        fontsize='large',
    )

    plot.tight_layout(h_pad=1, w_pad=3)
    
    plt.savefig(filename, bbox_inches='tight')
