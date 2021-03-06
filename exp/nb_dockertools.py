
#################################################
### THIS FILE WAS AUTOGENERATED! DO NOT EDIT! ###
#################################################
# file to edit: dev_nb/dockertools.ipynb

import os
import sys
sys.path.append(os.path.join(os.getcwd(),'exp'))

import time
import docker
import logging
import datetime
import numpy as np
from pathlib import Path

from nb_locker import check_gpu_access, check_gpu_usage

from config import cfg

def init_volume(local_path, docker_path, mode):
    v = {local_path:{'bind':docker_path, 'mode':mode}}
    return v

def run(docker_cfg):
    client = docker.from_env()
    cont = client.containers.run(**docker_cfg)
    return cont

def init_folders(run_root):
    timestamp = '{:%b_%d_%H_%M_%S_%f}'.format(datetime.datetime.now())
    if run_root is None:
        root=Path(cfg.DOCKER.RUN_PATH)
        run_root = (root/f'run_{timestamp}').absolute()

    out = run_root/'output'
    os.makedirs(out, exist_ok=True)
    conf = run_root/'configs'
    os.makedirs(conf, exist_ok=True)
    return out, conf, timestamp

def docker_callback(output_mount):
    logs_files = list(output_mount.rglob('log.txt'))
    try:
        log_file = logs_files[0]
        val_acc = read_log(log_file)
        return val_acc.max()
    except Exception as e:
        print(e)
        return 0

def read_log(log_fn):
    with open(log_fn, 'r') as f:
        data = f.read()

    val_acc = []
    for l in data.split('\n'):
        if l:
            d,g,v,va = l.split(',')
            g, v, va = int(g), float(v), float(va)
            val_acc.append(va)
    return np.array(val_acc)

def main(run_root=None, gpus='0'):
    check_gpu_access(Path(cfg.GPUS.LOCK), gpus)
    check_gpu_usage(gpus, delay=.2)

    logging.info(f'\n\tStarting docker container {run_root} @ gpu {gpus}\n')

    output_mount, configs_mount, timestamp = init_folders(run_root)
    input_mount = '/home/sokolov/work/etc/crsch/input/data_encoded_l4/'
    resources_mount = '/tmp'

    docker_run = {
        'image':'sokolov/crsch:v01',
        'name':f'{cfg.OWNER}{cfg.DOCKER.CONTAINER_PREFIX}{timestamp}',
        'volumes':{**init_volume(input_mount, '/mnt/input', 'ro'),
                   **init_volume(output_mount, '/mnt/output', 'rw'),
                   **init_volume(configs_mount, '/mnt/configs', 'ro'),
                   **init_volume(resources_mount, '/mnt/resources', 'ro')
                  },
        #'command':'touch /mnt/output/t.txt',
        'detach':False,
        'remove':True,
        'runtime':'nvidia',
        'environment':[f"CUDA_VISIBLE_DEVICES={gpus}"]
        }

    container = run(docker_run)
    result = docker_callback(output_mount)
    return result

if __name__ == '__main__':
    #print(main())
    print('No actual test here!')