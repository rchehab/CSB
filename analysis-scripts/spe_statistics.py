#!/usr/bin/env python
# coding: utf-8
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
from utils.observation import *

filename_dir_s1 = "results-mysql-lseek_fcntl_17_0"

the_filename = filename_dir_s1

filename = glob.glob(f"{the_filename}/*long*.csv")
filename.sort()


for one_file in filename:
    print(one_file)

    name_file = "-".join(one_file.split("/")[-2].split("-")[1:])
    name_file = name_file.replace(':', '-')

    df = records_from_csv_file(one_file)
    df.reset_index(level=0, inplace=True)

    # Initial manipulation of data frame

    df['simple_pcs'] = df['pcs'].apply(no_thread)
    df = df[df['simple_pcs'] != '-1']
        
    df['total_count'] = df['counts'].apply(total_count)
    df['total_latency'] = df['latencies'].apply(total_count)

    all_counts = df['total_count'].sum()
    all_latencies = df['total_latency'].sum()
    normalize_cnt = all_counts / 500000

    df['total_count'] = df['total_count'] / normalize_cnt
    df['total_latency'] = df['total_latency'] / normalize_cnt

    lt_list = [x for x in df.columns if 'latency' in x and x != 'total_latency']
    cnt_list = [x.split(' latency')[0] for x in lt_list]
    for lt in lt_list:
        cnt = lt.split(' latency')[0]
        df[lt] = df[lt] / normalize_cnt
        df[cnt] = df[cnt] / normalize_cnt

    all_counts = df['total_count'].sum()
    all_latencies = df['total_latency'].sum()

    df = df.drop(columns=[
        'index',
        'pcs',
        'counts',
        'node',
        'nb_pcs',
        'latencies',
    ])
    df_simple = df.drop(columns=lt_list + cnt_list)

    calculate_bucket(df)

    # Get precise dataframes for use

    df_isol = df[df['nb_threads'] == 1]
    df_share = df[df['nb_threads'] != 1]

    isolated = get_one_per_type_df(df_isol)
    isolated['memory'] = 'isolated'
    shared = get_one_per_type_df(df_share)
    shared['memory'] = 'shared'

    op_types = pd.concat([isolated, shared])

    print(op_types.sort_values(by=['type', 'memory']))

    # Print latency histograms
    get_latency_histogram([df], filename=f'out/{name_file}-cumul-latency.pdf', name='general')
    df_buc = get_latency_histogram([df], filename=f'out/{name_file}-nb-threads-latency.pdf', name='per_region', x_axis = 'nb_threads')
    get_latency_histogram([df_share], filename=f'out/{name_file}-shared-latency.pdf', name='shared_only')
    get_latency_histogram([df_isol], filename=f'out/{name_file}-isolated-latency.pdf', name='isolated_only')
    xxxxxxxxxxx


# In[ ]:



# In[ ]:




# # Check types of operations

# In[ ]:


plot_bar(
    op_types,
    ['count', 'latency', 'avg_latency'],
    name='barplot_all',
    print_all=True,
)


# In[ ]:


plot_bar(
    op_types,
    ['count', 'latency', 'avg_latency'],
    name='barplot_simple',
)


# In[ ]:


plot_bar(
    op_types1,
    ['count', 'latency', 'avg_latency'],
    name='barplot_diff',
    print_all=True,
)


# In[ ]:


# random stuff


# In[ ]:


def info_avg_lt(df):
    set_config(20, 10, font_scale=0.8)

    memories = df['memory'].unique()
    types = df['type'].unique()
    plot, axes = plt.subplots(len(memories), len(types))
    
    bench = df['benchmark'].unique()[0]

    for i, memory in enumerate(memories):
        for j, stype in enumerate(types):
            df_f = df[(df['memory'] == memory) & (df['type'] == stype)]
            
            splot = sns.barplot(
                data=df_f,

                x='type',
                y='avg_latency',
                hue='scenario',
                hue_order=hue_order,

                ax = axes[i][j],
            )
            splot.set_title(f"{bench} -- {memory}")

    l_handles, l_labels = axes[0][0].get_legend_handles_labels()

    for i in range(0, len(memories)):
        for j in range(0, len(types)):
            axes[i][j].get_legend().remove()

    plot.legend(
        l_handles,
        l_labels,
        ncols=4,
        loc='lower center',
        bbox_to_anchor=(0.5, -0.15),
        title_fontsize='large',
        fontsize='large',
    )

    plot.tight_layout(h_pad=1, w_pad=0.2)
    
    plt.savefig(f'{bench}_latency.pdf', bbox_inches='tight')
    
info_avg_lt(op_types)


# # Random manual tests

# In[ ]:


isolated


# In[ ]:


shared


# In[ ]:


show = [
    #'pa',
    #'pcs',
    #'nb_threads',
    'iteration',
    'total_latency',
    'threads',
    'benchmark',
    'scenario',
    'cacheline',
    'avg_latency',
    
    'LD_hit',
    'LD_hit_lt',
    #'ST',
    #'ST_lt',
]


# In[ ]:


#df_f = df[df['ST_lt'] > 0]
df_f = df[df['LD_hit_lt'] > 0]
df_f = df_f[df_f['nb_threads'] == 1]
df_f = df_f[df_f['iteration'] >= 6]
df_f = df_f[df_f['iteration'] <= 8]

df_ff = df_f.sort_values(by=[
    #'ST_lt',
    'LD_hit_lt',
], ascending=False)[show]

df_ff


# In[ ]:


df_cch = df_ff.groupby([
    'iteration',
    'threads',
    'cacheline',
    'benchmark',
    'scenario']
)[
    #['ST', 'ST_lt']
    ['LD_hit', 'LD_hit_lt']
].sum().reset_index()


#df_cch['avg_latency'] = df_cch['ST_lt'] / df_cch['ST']
df_cch['avg_latency'] = df_cch['LD_hit_lt'] / df_cch['LD_hit']
df_cch.sort_values(by=[
    #'ST_lt',
    'LD_hit_lt',
], ascending=False)


# In[ ]:


pd.set_option('display.max_rows', 200)


# In[ ]:


df_g = df_ff.groupby([
    'iteration',
    #'threads',
    'benchmark',
    'scenario'
])[
    #['ST', 'ST_lt']
    ['LD_hit', 'LD_hit_lt']
].sum().reset_index()

#df_g['avg_latency'] = df_g['ST_lt'] / df_g['ST']
df_g['avg_latency'] = df_g['LD_hit_lt'] / df_g['LD_hit']

#df_g.sort_values(by=[
#    #'ST_lt',
#    'LD_hit_lt',
#], ascending=False)

df_g


# In[ ]:




