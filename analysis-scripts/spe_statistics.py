#!/usr/bin/env python
# coding: utf-8

# # Important Functions

# In[ ]:


import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np
import pandas as pd
import seaborn as sns
import altair as alt
import math

import json
import os
import os.path as ospath
from pprint import pprint
import glob

import itertools


# In[ ]:


hue_order = ['16thr-samenuma', '16thr-diffnuma']


# In[ ]:


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


# In[ ]:


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


# In[ ]:


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


# In[ ]:


CONTEXT = 'talk'
STYLE = 'whitegrid'
PALETTE = 'colorblind'
# ESTIMATOR = np.median
ESTIMATOR_STR = 'median'
# CONFINT = 'sd'

def set_config(width=8, height=6, font_scale=1.15):
    sns.set_theme(
        context=CONTEXT,
        style=STYLE,
        palette=PALETTE,
        font_scale=font_scale,
        rc={
            'figure.figsize':(width,height),
            'pdf.fonttype': 42,
            'pdf.use14corefonts': True,
            'text.usetex': True,
        },
    )


# In[ ]:


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


# In[ ]:


def get_one_per_type_df(df, max_latency, max_count):

    lt_list = ['LD_hit_lt', 'LD_miss_lt', 'ST_lt', 'AT_hit_lt', 'AT_miss_lt', 'AT_ST_lt'] #+ ['total_latency']
    cnt_list = ['LD_hit', 'LD_miss', 'ST', 'AT_hit', 'AT_miss', 'AT_ST'] #+ ['total_count']

    per_type_latency = df.groupby(['benchmark', 'scenario'])[lt_list].sum().reset_index()
    per_type_latency = per_type_latency.melt(
        id_vars=['benchmark', 'scenario'], var_name='type', value_name='latency'
    )

    per_type_count = df.groupby(['benchmark', 'scenario'])[cnt_list].sum().reset_index()
    per_type_count = per_type_count.melt(
        id_vars=['benchmark', 'scenario'], var_name='type', value_name='count'
    )

    per_type = per_type_latency
    per_type['count'] = per_type_count['count']
    per_type['avg_latency'] = per_type['latency'] / per_type['count']
    
    return per_type

def get_per_type_df(df):
    
    return pd.concat([
        get_one_per_type_df(
            df[(df['benchmark'] == bench) & (df['scenario'] == scen)],
            all_latencies[bench][scen],
            all_counts[bench][scen],

        )
        for bench in df['benchmark'].unique() for scen in df['scenario'].unique()
    ])


# In[ ]:


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


# # Create DFs

# In[ ]:


filename_dir1='ldb'
filename_dir2='uaB'
filename_dir3='epC'
filename_dir4='luB'
filename_dir5='ftC'
filename_dir6='spB'
filename_dir7='btB'
filename_dir8='cgB'
filename_dir9='mgC'
filename_dir10='postgresql'
filename_dir11='postgresql100tables'
#filename_dir12='postgresqlTPCCprepare'
#filename_dir10='btBnew'

the_filename = filename_dir11

#the_filename_dir1= f'../obs-{the_filename}-4thr-cachegroup/'
#the_filename_dir2= f'../obs-{the_filename}-4thr-numa/'
the_filename_dir1= f'../observation/obs-{the_filename}-16thr-samenuma/'
the_filename_dir2= f'../observation/obs-{the_filename}-16thr-diffnuma/'


#####################

filename_obs1 = glob.glob(the_filename_dir1 + '/*long.csv')
filename_obs2 = glob.glob(the_filename_dir2 + '/*long.csv')

filename_obs2


# In[ ]:


# Functions for creating the dataset

def records_from_csv_file(csv_path, file_name):
    records_from_file = pd.read_csv(csv_path, sep=';', comment='#')
    
    #file_name = file_name[0].split('/')[1]
    file_name = file_name[0].split('/')[2]
    
    records_from_file['benchmark'] = file_name.split('-')[1]
    records_from_file['scenario'] = '-'.join(file_name.split('-')[2:4])

    return records_from_file

df1 = pd.concat([records_from_csv_file(p, filename_obs1) for p in filename_obs1])
df1.reset_index(level=0, inplace=True)
df2 = pd.concat([records_from_csv_file(p, filename_obs2) for p in filename_obs2])
df2.reset_index(level=0, inplace=True)

df = pd.concat([df1, df2])
#df = df2


# In[ ]:


def get_diff(df):
    
    for i, scen in enumerate(df['scenario'].unique()):
        if i == 0:
            res = pd.concat([df[df['scenario'] == scen]])
        else:
            res['latency'] = res['latency'] - df.loc[df['scenario'] == scen, 'latency']
            res['count'] = res['count'] - df.loc[df['scenario'] == scen, 'count']
            res['avg_latency'] = res['avg_latency'] - df.loc[df['scenario'] == scen, 'avg_latency']
            res['scenario'] = df.loc[df['scenario'] == scen, 'scenario'] + ' to ' + res['scenario']
    
    return res


# # Configure DFs

# In[ ]:


df['simple_pcs'] = df['pcs'].apply(no_thread)
df = df[df['simple_pcs'] != '-1']
    
df['total_count'] = df['counts'].apply(total_count)


# In[ ]:


all_counts = df.groupby(['benchmark', 'scenario'])['total_count'].sum()
all_latencies = df.groupby(['benchmark', 'scenario'])['total_latency'].sum()

normalize_cnt = all_counts / 500000
normalize_cnt


# In[ ]:


for bench in df['benchmark'].unique():
    for scen in df['scenario'].unique():
        filt = (df['scenario'] == scen) & (df['benchmark'] == bench)
        df.loc[filt, 'total_count'] = df.loc[filt, 'total_count'] / normalize_cnt[bench][scen]
        df.loc[filt, 'total_latency'] = df.loc[filt, 'total_latency'] / normalize_cnt[bench][scen]

        lt_list = ['LD_hit_lt', 'LD_miss_lt', 'ST_lt', 'AT_hit_lt', 'AT_miss_lt', 'AT_ST_lt']
        cnt_list = ['LD_hit', 'LD_miss', 'ST', 'AT_hit', 'AT_miss', 'AT_ST']
        
        for lt in lt_list:
            df.loc[filt, lt] = df.loc[filt, lt] / normalize_cnt[bench][scen]
        
        for cnt in cnt_list:
            df.loc[filt, cnt] = df.loc[filt, cnt] / normalize_cnt[bench][scen]


# In[ ]:


all_counts = df.groupby(['benchmark', 'scenario'])['total_count'].sum()
all_latencies = df.groupby(['benchmark', 'scenario'])['total_latency'].sum()

all_counts


# In[ ]:


df['cacheline'] = df['pa'].apply(change_to_cache)
df['page'] = df['pa'].apply(change_to_page)

calculate_bucket(df)


# In[ ]:


df_page = df.groupby(['page', 'iteration', 'benchmark', 'scenario'])
df_page = df_page.agg({'nb_threads' : 'max', 'total_latency': 'sum', 'total_count': 'sum'}).reset_index()


df_cache = df.groupby(['cacheline', 'iteration', 'benchmark', 'scenario'])
df_cache = df_cache.agg({'nb_threads' : 'max', 'total_latency': 'sum', 'total_count': 'sum'}).reset_index()


# In[ ]:


df_isol = df[df['nb_threads'] == 1]
df_share = df[df['nb_threads'] != 1]


# In[ ]:


isolated = get_per_type_df(df_isol)
isolated['memory'] = 'isolated'
shared = get_per_type_df(df_share)
shared['memory'] = 'shared'

op_types = pd.concat([isolated, shared])


# In[ ]:


isol1 = get_diff(isolated)
shar1 = get_diff(shared)

op_types1 = pd.concat([isol1, shar1])


# # Show Cumulative Graphs

# In[ ]:


get_latency_histogram([df], name='general')


# In[ ]:


df_buc = get_latency_histogram([df, df_cache, df_page], name='per_region', x_axis = 'nb_threads')


# In[ ]:


get_latency_histogram([df_share], name='shared_only')


# In[ ]:


get_latency_histogram([df_isol], name='isolated_only')


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




