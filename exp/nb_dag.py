
#################################################
### THIS FILE WAS AUTOGENERATED! DO NOT EDIT! ###
#################################################
# file to edit: dev_nb/dag.ipynb

import os
import sys
from pathlib import Path
p = '/home/sokolov/work/cycler/dHPO/exp/'
sys.path.append(p)
#sys.path.append(os.path.join(os.getcwd(),'exp'))

import time
import json
import numpy as np
from itertools import cycle
from functools import partial
from datetime import timedelta, datetime

from airflow import DAG
from airflow.operators.bash_operator import BashOperator
from airflow.operators.python_operator import PythonOperator
from airflow.utils.dates import days_ago


from nb_runner import cycle_exp, cycle_mutate, \
                      cycle_crossover, cycle_combine, cycle_all,\
                      bo_exp, bo_all, bo_crossover
from config import cfg

d = datetime.now().date()
default_args = {
    'owner': cfg.OWNER,
    'depends_on_past': False,
    'start_date': datetime(d.year, d.month, d.day-1),#days_ago(1),#datetime(2020, 5, 15),
    'email': False,
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 0,# overrided in pythonOperator down below
    'retry_delay': timedelta(minutes=5),# overrided in pythonOperator down below
}

default_pool = cfg.DAG.DEF_POOL
schedule_interval = cfg.DAG.SCHED_INTERVAL if cfg.DAG.SCHED_INTERVAL else None #@daily
description = cfg.DAG.DESC + '\n' + json.dumps(cfg, indent=4)

dag = DAG(  cfg.DAG.NAME,
                default_args=default_args,
                #max_active_runs=1,
                catchup=False,# for disabling backfill!
                description=description,
                schedule_interval=schedule_interval)

def base_task_generator(name, func, dag, pool=default_pool, op_kwargs=None):
    task = PythonOperator(
                    task_id=name,
                    python_callable=func,
                    op_kwargs=op_kwargs,
                    provide_context=True,
                    pool=pool,
                    retries=cfg.DAG.RETRIES,
                    retry_delay=timedelta(minutes=cfg.DAG.RETRY_DELAY),
                    dag=dag,)
    return task

create_task = partial(base_task_generator, dag=dag)

def pull_results(**context):
    results = None
    if context is not None:
        task_ids = context['dag'].task_ids
        results = {task_id:context['ti'].xcom_pull(task_ids=task_id) for task_id in task_ids}
    return results


def upstream_results(**context):
    task = context['task']
    upstream_task_ids = task.upstream_task_ids
    rs = [pull_results(**context)[task_id] for task_id in upstream_task_ids]
    if not rs:
        rs = [{'configs':None, 'docker_results':None}]
    for result in rs:
        yield result

def parse_pool(pool_str):
    pool_str = pool_str.split('_')[-1]
    return ','.join([i for i in pool_str if i.isdigit()])

def chunker_list(seq, size):
    return (seq[i::size] for i in range(size))

def dw_cycle_param(func, **context):
    prev_results = next(upstream_results(**context))
    aux_cfg_files = prev_results['configs']
    gpus = parse_pool(context['ti'].pool)
    return func(aux_cfg_files=aux_cfg_files, gpus=gpus)

def dw_bo_param(func, **context):
    results = pull_results(**context)
    all_hp_points = []
    for task_id, r in results.items():
        if r:
            all_hp_points.append({'points':r['state'], 'target':r['docker_results']['metric']})

    prev_results = next(upstream_results(**context))
    aux_cfg_files = prev_results['configs']
    gpus = parse_pool(context['ti'].pool)
    idx = cfg.GPUS.IDS.index(int(gpus))# wont work with single exp on multiple gpus!
    return func(aux_cfg_files=aux_cfg_files, gpus=gpus, hp_points=all_hp_points, idx=idx)

def dw_pooling(num=1, **context):
    key = 'metric'
    res = {}
    for r in upstream_results(**context):
        res[r['docker_results'][key]] = r['configs']
    res = sorted(res.items(), key=lambda x: x[0], reverse=True)
    res = res[:num]
    best_docker_results = [r[0] for r in res]
    best_configs = [r[1] for r in res]
    print(f'\n\tPooling: best result : {best_docker_results}, {best_configs}\n')
    return [{'configs':best_config} for best_config in best_configs]

def dw_dist(idx=None, **context):
    res = list(upstream_results(**context))[0][idx]
    return res

def distribute(num):
    tasks = []
    for i in range(num):
        task_name = f'distribute_{i}'
        tasks.append(create_task(task_name, dw_dist, op_kwargs={'idx':i}))
    return tasks

def block_optimize(n, name, func, dw_param):
    tasks = []
    gpus_avail = cycle(cfg.GPUS.IDS)

    for i in range(n):
        gpu = next(gpus_avail)
        task_name = f'{name}_{i}'
        pool = cfg.DAG.POOL_PREFIX + str(gpu)

        block_func = partial(func, seq_id=i, name=task_name)
        task = create_task(task_name, dw_param, pool=pool, op_kwargs={'func':block_func})
        tasks.append(task)
    return tasks

#tasks = {'mut':[], 'exp':[], 'cross':[]}

tasks_bo_all = block_optimize(150, 'bo_all', bo_all, dw_bo_param)
#tasks['exp'] = cycle_block(3, 'cycle_e', cycle_exp)

pooling_task1 = create_task(f'pooling1', dw_pooling)
tasks_bo_all >> pooling_task1

#partial(dw_pooling, num=1)
# dist_num = 2
# pooling_task1 = create_task(f'pooling_two_best', partial(dw_pooling, num=dist_num))
# tasks['exp'] >> pooling_task1

# dist_tasks = distribute(dist_num)
# connect(pooling_task1, dist_tasks)

# mut_tasks = block_optimize(7, 'cycle_m', cycle_mutate)
# for dt, mt in zip(dist_tasks, chunker_list(mut_tasks, dist_num)):
#     connect(dt, mt)

from airflow.models import TaskInstance
from datetime import datetime
import json
from pprint import pprint