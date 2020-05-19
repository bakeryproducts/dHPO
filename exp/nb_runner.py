
#################################################
### THIS FILE WAS AUTOGENERATED! DO NOT EDIT! ###
#################################################
# file to edit: dev_nb/runner.ipynb

import os
import sys
sys.path.append(os.path.join(os.getcwd(),'exp'))

import time
import json
import logging
import datetime
import numpy as np
from pathlib import Path
from shutil import copyfile

import nb_dockertools as docker_tools
from nb_cycle import get_dist, dump_state, init_params, BaseConfigCycler, Param
from nb_bo import BaseConfigBo
from config import cfg

def run(new_state, inner_state, aux_cfg_files=None, name='cfg', gpus='0', **kwargs):
    logging.info(f'\n\tNew state for {name}:\n {json.dumps(new_state, indent=4)}\n')

    root = Path(cfg.DAG.RUNS)
    root = root.absolute()
    os.makedirs(root, exist_ok=True)

    run_path, configs_path = init_run(root)
    if aux_cfg_files is not None:
        for cfg_file in aux_cfg_files:
            file_name = os.path.basename(cfg_file)
            copyfile(cfg_file, configs_path/file_name)
    else:
        aux_cfg_files=[]
    run_cfg_file = dump_state(new_state, configs_path, name)
    if kwargs.get('hp_points',None):
        dump_state(kwargs['hp_points'], configs_path, 'hp', is_config=False, yaml_dump=False)

    docker_result = docker_tools.main(run_path, gpus=gpus)
    results = {'configs':[run_cfg_file] + aux_cfg_files}
    results['docker_results'] = {
        'metric':docker_result
    }
    results['state'] = inner_state
    return results

def init_run(root):
    timestamp = '{:%Y_%b_%d_%H_%M_%S_%f}'.format(datetime.datetime.now())
    run_dir = root/f'run_{timestamp}'
    conf_dir = run_dir/'configs'
    os.makedirs(conf_dir, exist_ok=True)
    return run_dir, conf_dir

class Cycler(BaseConfigCycler):
    def init_map(self):
        return {
            'g':('generations', int, 2),
            'e':('exp_power', int, np.NaN),
            'f0':('dec_f0', int, np.NaN),
            'f1':('dec_f1', int, np.NaN),
            'f2':('dec_f2', int, np.NaN),
            'f3':('dec_f3', int, np.NaN),
            'mc':('mutate_chance', float, np.NaN),
            'cr':('crossover_chance', float, np.NaN),
            'co':('combine_chance', float, np.NaN)
        }

cycler = Cycler()
p9 = {'name':'co', 'sampling':'random', 'arr':get_dist(start=.01, end=.99, num=500, space='lin')}
p7 = {'name':'e', 'sampling':'sequential', 'arr':[1,5,10,15,25,50]}
p1 = {'name':'mc', 'sampling':'random', 'arr':get_dist(start=5e-4, end=5e-3, num=500, space='lin')}
p3 = {'name':'cr', 'sampling':'random', 'arr':get_dist(start=.01, end=.99,   num=500, space='lin')}

p2 = {'name':'f0', 'sampling':'random', 'arr':get_dist(start=2, end=20,   num=500, space='lin', to_int=True)}
p4 = {'name':'f1', 'sampling':'random', 'arr':get_dist(start=2, end=30,   num=500, space='lin', to_int=True)}
p6 = {'name':'f2', 'sampling':'random', 'arr':get_dist(start=2, end=30,   num=500, space='lin', to_int=True)}
p8 = {'name':'f3', 'sampling':'random', 'arr':get_dist(start=2, end=10,   num=500, space='lin', to_int=True)}


#params_dists = {p['name']:init_params([p]) for p in [p1,p3,p7,p9]}

def cycle_all(**kwargs):
    inner_state, new_state=cycler.create_state([p1,p3,p7,p9, p2,p4,p6,p8], kwargs['seq_id'])
    return run(new_state=new_state, inner_state=inner_state, **kwargs)

def cycle_exp(**kwargs):
    inner_state, new_state=cycler.create_state([p7], kwargs['seq_id'])
    return run(new_state=new_state, inner_state=inner_state, **kwargs)

def cycle_combine(**kwargs):
    inner_state, new_state=cycler.create_state([p9])
    return run(new_state=new_state, inner_state=inner_state, **kwargs)

def cycle_mutate(**kwargs):
    inner_state, new_state=cycler.create_state([p1])
    return run(new_state=new_state, inner_state=inner_state, **kwargs)

def cycle_crossover(**kwargs):
    inner_state, new_state=cycler.create_state([p3])
    return run(new_state=new_state, inner_state=inner_state, **kwargs)


class Bo(BaseConfigBo):
    def init_map(self):
        return {
            'g':('generations', int, 200),
            'e':('exp_power', int, 2),
            'f0':('dec_f0', int, np.NaN),
            'f1':('dec_f1', int, np.NaN),
            'f2':('dec_f2', int, np.NaN),
            'f3':('dec_f3', int, np.NaN),
            'mc':('mutate_chance', float, np.NaN),
            'cr':('crossover_chance', float, np.NaN),
            'co':('combine_chance', float, np.NaN)
        }



n_parallel_processes = len(cfg.GPUS.IDS)
bo = Bo(n_parallel_processes)
# bo_p1 = {'name':'e', 'bounds':(1, 15)}
bo_p2 = {'name':'cr', 'bounds':(.01, .99)}
bo_p3 = {'name':'mc', 'bounds':(0, .05)}
bo_p4 = {'name':'co', 'bounds':(.01, .99)}

all_params = [bo_p2, bo_p3, bo_p4]

try:
    p = '/home/sokolov/work/cycler/dHPO/2020_May_19_20_58_39_hp.json'
    with open(p, 'r') as f:
        warm_start = json.load(f)
except Exception as e:
    warm_start = []
    print(e)

def bo_all(**kwargs):
    points = []#warm_start
    if kwargs['hp_points']:
        points.extend(kwargs['hp_points'])

    inner_state, new_state=bo.create_state(points=points, params=all_params, idx=kwargs['idx'])
    return run(new_state=new_state, inner_state=inner_state, **kwargs)

def bo_exp(**kwargs):
    inner_state, new_state=bo.create_state(points=kwargs['hp_points'], params=[bo_p1], idx=kwargs['idx'])
    return run(new_state=new_state, inner_state=inner_state, **kwargs)

def bo_crossover(**kwargs):
    inner_state, new_state=bo.create_state(points=kwargs['hp_points'], params=[bo_p2], idx=kwargs['idx'])
    return run(new_state=new_state, inner_state=inner_state, **kwargs)

if __name__ == '__main__':
    r1 = cycle_exp(seq_id=0, gpu=0)
    print(r1)
    r2 = cycle_mut(aux_cfg_files=r1['configs'], gpu=0)
    print(r2)
    print('all good!')