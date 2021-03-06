
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
from collections import OrderedDict

import nb_dockertools as docker_tools
from nb_cycle import get_dist, Cycler
from nb_bo import Bo
from nb_helpers import dict_merge, dump_state
from config import cfg

def make_root():
    root = Path(cfg.DAG.RUNS)
    root = root.absolute()
    os.makedirs(root, exist_ok=True)
    return root

def init_run():
    root = make_root()
    timestamp = '{:%Y_%b_%d_%H_%M_%S_%f}'.format(datetime.datetime.now())
    run_dir = root/f'run_{timestamp}'
    conf_dir = run_dir/'configs'
    os.makedirs(conf_dir, exist_ok=True)
    return run_dir, conf_dir

def init_aux_configs(aux_cfg_files, configs_path):
    if aux_cfg_files is not None:
        for cfg_file in aux_cfg_files:
            file_name = os.path.basename(cfg_file)
            copyfile(cfg_file, configs_path/file_name)
    else:
        aux_cfg_files=[]
    return aux_cfg_files

def run(new_state, inner_state, aux_cfg_files=None, name='cfg', gpus='0', **kwargs):
    logging.info(f'\n\tNew state for {name}:\n {json.dumps(new_state, indent=4)}\n')

    run_path, configs_path = init_run()
    aux_cfg_files = init_aux_configs(aux_cfg_files, configs_path)

    run_cfg_file = dump_state(new_state, configs_path, name)
    if kwargs.get('hp_points',None):
        dump_state(kwargs['hp_points'], configs_path, 'hp', is_config=False, yaml_dump=False)


    docker_result = docker_tools.main(run_path, gpus=gpus)
    results = {
        'configs':[run_cfg_file] + aux_cfg_files,
        'docker_results':{'metric':docker_result},
        'state':inner_state
    }
    return results

p_mut = {'name':'genom|mutate_chance',
      'sampling':'random',
      'arr':get_dist(start=0, end=0.05, num=500, space='lin'),
      'default':None,
      'type':float}

p_com = {'name':'genom|combine_chance',
      'arr':get_dist(start=0, end=1, num=500, space='lin'),
      'sampling':'random',
      'default':None,
      'type':float}

p_cr = {'name':'genom|crossover_chance',
      'arr':get_dist(start=0, end=1, num=500, space='lin'),
      'sampling':'random',
      'default':None,
      'type':float}

p_e = {'name':'post|exp_power', 'arr':[4,6,8], 'sampling':'sequential', 'default':None, 'type':int}
p_g = {'name':'generations', 'default':5}

cycler_all = Cycler( [p_mut, p_com, p_cr, p_e, p_g])
cycler_exp = Cycler( [p_e, p_g])
cycler_mut = Cycler( [p_mut, p_g])
cycler_com = Cycler( [p_com, p_g])
cycler_cr = Cycler( [p_cr, p_g])

def cycle_all(**kwargs):
    inner_state, new_state=cycler_all.create_state(kwargs['seq_id'])
    return run(new_state=new_state, inner_state=inner_state, **kwargs)

def cycle_exp(**kwargs):
    inner_state, new_state=cycler_exp.create_state(kwargs['seq_id'])
    return run(new_state=new_state, inner_state=inner_state, **kwargs)

def cycle_combine(**kwargs):
    inner_state, new_state=cycler_com.create_state()
    return run(new_state=new_state, inner_state=inner_state, **kwargs)

def cycle_mutate(**kwargs):
    inner_state, new_state=cycler_mut.create_state()
    return run(new_state=new_state, inner_state=inner_state, **kwargs)

def cycle_crossover(**kwargs):
    inner_state, new_state=cycler_cr.create_state([p3])
    return run(new_state=new_state, inner_state=inner_state, **kwargs)


n_parallel_processes = len(cfg.GPUS.IDS)
warm_list = ['/home/sokolov/work/cycler/dHPO/2020_May_21_18_34_23_hp.json']

params_static = [
            {'name':'generations', 'default':200},
]
params_genom = [
            {'name':'genom|mutate_chance', 'bounds':(0,.05), 'type':float, 'prior':'uniform', 'default':None},
            {'name':'genom|crossover_chance', 'bounds':(0,1), 'type':float, 'prior':'uniform', 'default':None},
            {'name':'genom|combine_chance', 'bounds':(0,1), 'type':float, 'prior':'uniform', 'default':None},
]
params_post =[
            {'name':'post|exp_power','bounds':(1,15), 'type':int, 'prior':'uniform', 'default':None}
]

p_all = [*params_static, *params_genom, *params_post]
bopt_all = Bo(n=n_parallel_processes, params=p_all, warm_list=warm_list)

bopt_post = Bo(n=n_parallel_processes, params=params_post, warm_list=warm_list)


def bo_all(**kwargs):
    inner_state, new_state=bopt_all.create_state(points=kwargs['hp_points'], idx=kwargs['idx'])
    return run(new_state=new_state, inner_state=inner_state, **kwargs)

def bo_exp(**kwargs):
    inner_state, new_state=bopt_post.create_state(points=kwargs['hp_points'], idx=kwargs['idx'])
    return run(new_state=new_state, inner_state=inner_state, **kwargs)

if __name__ == '__main__':
    r1 = cycle_exp(seq_id=0, gpu=0)
    print(r1)
    r2 = cycle_mut(aux_cfg_files=r1['configs'], gpu=0)
    print(r2)
    print('all good!')