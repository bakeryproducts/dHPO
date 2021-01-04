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
#
# # Imports

# %% tags=["active-ipynb"]
# import os
# import sys
# os.chdir('../dHPO')

# %%
import os
import sys

import time
import yaml
import json
import datetime
import numpy as np
from pathlib import Path
from collections import OrderedDict
print(sys.path)

from dHPO.utils import dict_merge, create_nested

# %%
import matplotlib.pyplot as plt
# #%matplotlib inline

# %% [markdown]
# # Code

# %%
def from_range(start, end, num, dist=None):
    if dist is None:
        dist = np.random.random
    lstart, lend = np.log(start), np.log(end)
    ar = np.logspace(lstart, lend, num, base=np.e)
    return ar

def get_dist(start, end, num, space, to_int=False):
    if space == 'log':
        space = np.geomspace
    elif space == 'lin':
        space = np.linspace
    else:
        raise NotImplementedError
    arr = space(start, end, num).astype(np.float32)
    if to_int:
        arr = arr.astype(np.int32)
    return arr


# %%
class Param:
    def __init__(self, name, arr, sampling, **kwargs):
        self.name = name
        self.arr = arr
        self.count = 0
        self.sampling = sampling
        self.type = kwargs['type']
        
    def __len__(self):
        return len(self.arr)
    
    def __getitem__(self, i):
        i = i%self.__len__()
        return self.arr[i]
    
    def get_random(self):
        return self.__getitem__(np.random.choice(self.__len__()))
    
    def safe_get_next(self):
        val = self.__getitem__(self.count)
        self.count = self.count+1 if self.count < self.__len__()-1 else 0
        return val
    
    def get_next(self, **kwargs):
        if self.sampling == 'random':
            v = self.get_random()
        elif self.sampling == 'sequential':
            if kwargs.get('idx', None):
                v = self.__getitem__(kwargs['idx'])
            else:
                v = self.safe_get_next()
        else:
            raise ValueError
        
        return self.type(v)
    
    def reset_count(self):
        self.count=0
    
    def __repr__(self):
        return f'Param : {self.name} | {str(self.arr)}'
    
    def plot(self):
        plt.hist(self.arr, bins=10)
    


# %%
class BaseConfigCycler:        
    def get_values(self, idx):
        values = {}
        for name in self.opt_param_names:
            kwargs = self.params[name]
            p = Param(name=name, **kwargs)
            values[name] = p.get_next(idx=idx)
        return values

    def to_dict(self, params):
        d = {}
        params = sorted(params, key=lambda x:x['name'], reverse=False)
        for p in params:
            d[p['name']] = {n:v for n,v in p.items() if n != 'name'}
        return OrderedDict(d)
    
class Cycler(BaseConfigCycler):
    def __init__(self, params, *args, **kwargs):
        super(Cycler, self).__init__(*args, **kwargs)
        self.params = self.to_dict(params)
        self.opt_param_names = [k for k in self.params if self.params[k]['default'] is None]
        
    def create_state(self, idx=None):
        new_params = self.get_values(idx)

        cfg = {}
        for name, settings in self.params.items():
            new_value = new_params[name] if not settings['default'] else settings['default']
            sub_cfg = create_nested(name, new_value)
            dict_merge(cfg, sub_cfg)
        return new_params, cfg

# %% [markdown]
# # Tests 

# %% tags=["active-ipynb"]
# p1 = {'name':'genom|mutate_chance',
#       'sampling':'random',
#       'arr':get_dist(start=5e-4, end=5e-3, num=500, space='lin'),
#       'default':None,
#       'type':float}
#
# p2 = {'name':'genom|combine_chance', 'arr':[4,5,6], 'sampling':'random', 'default':None, 'type':float}
# p3 = {'name':'dec_f0', 'arr':[33,488,99], 'sampling':'sequential', 'default':None, 'type':float}
# p4 = {'name':'generations', 'default':1}
# pis = [p1,p2, p3, p4]
# c = Cycler(pis)

# %% tags=["active-ipynb"]
# for k,v in c.params.items():
#     print(k)

# %% tags=["active-ipynb"]
# c.create_state()

# %%

# %%
