#!/usr/bin/env python

import ast
import glob
import sys
from typing import Optional

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

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
    df['bucket'] = df['avg_latency'].apply(lambda x: round(x / 10) * 10);

def calc_cumul_latency(df):
    df['cumul_total_latency'] = 0
    df['cumul_total_count'] = 0

    for bench in df['benchmark'].unique():
        for scen in df['scenario'].unique():
            filt = (df['benchmark'] == bench) & (df['scenario'] == scen)
        
            cumul_total_latency = 0
            cumul_total_count = 0

            for index, row in df[filt].iterrows():
                cumul_total_latency = cumul_total_latency + row['total_latency']
                cumul_total_count = cumul_total_count + row['total_count']
                
                df.loc[index, 'cumul_total_latency'] = cumul_total_latency
                df.loc[index, 'cumul_total_count'] = cumul_total_count

    df['cumul_avg_latency'] = df['cumul_total_latency'] / df['cumul_total_count']

def get_one_per_type_df(df, max_latency, max_count):

    lt_list = [x for x in df.columns if 'latency' in x and x != 'total_latency']
    cnt_list = [x.split(' latency')[0] for x in lt_list]

    per_type_latency = df[lt_list].sum().reset_index()
    print("")
    print(per_type_latency)
    per_type_latency = per_type_latency.melt(
        var_name='type', value_name='latency'
    )
    print("")
    print(per_type_latency)

    per_type_count = df[cnt_list].sum().reset_index()
    per_type_count = per_type_count.melt(
        var_name='type', value_name='count'
    )

    per_type = per_type_latency
    per_type['count'] = per_type_count['count']
    per_type['avg_latency'] = per_type['latency'] / per_type['count']
    
    return per_type















def get_latency_histogram(df_array, name, x_axis = 'bucket'):
    set_config(16, 7, font_scale=1.15)

    scenarios = df_array[0]['scenario'].unique()
    bench = df_array[0]['benchmark'].unique()[0]
    
    plot, axes = plt.subplots(1, len(df_array))

    for j, df in enumerate(df_array):
        df_buc = df.groupby([x_axis, 'benchmark', 'scenario'])[['total_latency', 'total_count']].sum().reset_index();
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
            style='scenario',
            markers=True,
            hue='scenario',
            hue_order=hue_order,

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

        splot.set_title(f"Benchmark {bench}")
        splot.set_xlabel(f"Latency '{x_axis}'")
        splot.set_ylabel("Cumulative Latency")
        get_axes(axes, j).ticklabel_format(style='plain')
    
    l_handles, l_labels = get_axes(axes, 0).get_legend_handles_labels()
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
    
    plt.savefig(f'{bench}_{name}.pdf', bbox_inches='tight')

def plot_bar(df, y_axes, name, print_all=False):
    set_config(16, 9, font_scale=0.8)
    
    bench = df['benchmark'].unique()[0]
    memories = df['memory'].unique()
    
    plot, axes = plt.subplots(len(memories), len(y_axes))

    for i, memory in enumerate(memories):
        add_to_title = memory

        for j, y_axis in enumerate(y_axes):
            
            df_f = df[df['memory'] == memory]

            def get_axes(axes, i, j, size_a, size_b):
                if size_a == 1 and size_b == 1:
                    return axes
                elif size_a == 1:
                    return axes[j]
                elif size_b == 1:
                    return axes[i]
                else:
                    return axes[i][j]

            lt_list = ['LD_miss_lt', 'AT_miss_lt', 'AT_ST_lt']
            
            hue_order = df_f['scenario'].unique()

            splot = sns.barplot(
                data=df_f if print_all is True else df_f[df_f['type'].isin(lt_list)],

                x='type',
                y=y_axis,
                hue='scenario',
                hue_order=hue_order,
                
                ax = get_axes(axes, i, j, len(memories), len(y_axes))
            )

            splot.set_title(f"Benchmark {bench} -- {add_to_title}")
            splot.set_xlabel(f"Different operation types")
            splot.set_ylabel(f"{y_axis}")
            
            get_axes(axes, i, j, len(memories), len(y_axes)).yaxis.set_major_formatter(ticker.ScalarFormatter())
            get_axes(axes, i, j, len(memories), len(y_axes)).ticklabel_format(style='plain', axis='y')


    l_handles, l_labels = get_axes(axes, 0, 0, len(memories), len(y_axes)).get_legend_handles_labels()
    
    for i in range(0, len(memories)):
        for j in range(0, len(y_axes)):
            get_axes(axes, i, j, len(memories), len(y_axes)).get_legend().remove()

    plot.legend(
        l_handles,
        l_labels,
        ncols=2,
        loc='lower center',
        bbox_to_anchor=(0.5, -0.12),
        title_fontsize='large',
        fontsize='large',
    )

    plot.tight_layout(h_pad=1, w_pad=0.2)
    
    plt.savefig(f'{bench}_barplot_{name}.pdf', bbox_inches='tight')

