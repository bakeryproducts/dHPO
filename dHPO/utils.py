# ---
# jupyter:
#   jupytext:
#     formats: notebooks//ipynb,dHPO//py:percent
#     text_representation:
#       extension: .py
#       format_name: percent
#       format_version: '1.3'
#       jupytext_version: 1.7.1
#   kernelspec:
#     display_name: Python 3
#     language: python
#     name: python3
# ---

# %% [markdown]
# # Imports

# %%
import os
import json
import yaml
import datetime
from pathlib import Path
from collections import defaultdict, MutableMapping, Mapping


# %% tags=["active-ipynb"]
# import numpy as np
# import pandas as pd
# import matplotlib.pyplot as plt
# %matplotlib inline

# %% [markdown]
# # Code

# %%
class UnknownGpuDevice(Exception):pass
class CantDoThatMuch(Exception):pass

class GpuLockedTimeout(Exception):pass
class GpuUsageTimeout(Exception):pass


# %%
def flatten(d, parent_key='', sep='_'):
    items = []
    for k, v in d.items():
        new_key = parent_key + sep + k if parent_key else k
        if isinstance(v, MutableMapping):
            items.extend(flatten(v, new_key, sep=sep).items())
        else:
            items.append((new_key, v))
    return dict(items)

def load_txt_log(path, types=None, read_header=False, delimiter=','):
    with open(path, 'r') as f:
        raw_logs = f.read()
    logs = raw_logs.split('\n')

    header=None
    if read_header:
        header, *logs = logs
        header = header.split(delimeter)

    parsed_logs = []
    for line in logs:
        line = line.split(delimiter)
        if types is not None:
            line = [t(l) for t,l in zip(types,line)]
        parsed_logs.append(line)

    return header, parsed_logs


def dump_state(state, path, name, is_config=True, yaml_dump=True):
    timestamp = '{:%Y_%b_%d_%H_%M_%S}'.format(datetime.datetime.now())
    prefix = 'config_' if is_config else ''
    if yaml_dump:
        dump = yaml.safe_dump
        postfix = '.yaml'
    else:
        dump = json.dumps
        postfix = '.json'
    
    p = path/f'{prefix}{timestamp}_{name}{postfix}'
    with open(p, 'w') as f:
        f.write(dump(state, indent=4))
    return p



# %%
def dict_merge(dct, merge_dct):
    for k, v in merge_dct.items():
        if (k in dct and isinstance(dct[k], dict)
                and isinstance(merge_dct[k], Mapping)):
            dict_merge(dct[k], merge_dct[k])
        else:
            dct[k] = merge_dct[k]

def create_nested(k, v, sep='|'):
    d = defaultdict(dict)
    nested = d
    for i in k.split(sep)[:-1]:
        nested.setdefault(i, {})
        nested = nested[i]
    nested[k.split('|')[-1]] = v
    return d


# %%
colors = {
    "RED":'\033[0;31m',
    "GREEN":'\033[0;32m',
    "BROWN":'\033[0;33m',
    "BLUE":'\033[0;34m',
    "NC":'\033[0m' 
}

def clrd(s, clr):
    return colors[clr] + s + colors['NC']

def log(*args, c='NC', **kwargs):
    print(clrd(*args, **kwargs, clr=c))

# %%

# %%