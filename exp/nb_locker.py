
#################################################
### THIS FILE WAS AUTOGENERATED! DO NOT EDIT! ###
#################################################
# file to edit: dev_nb/locker.ipynb

import os
import sys
sys.path.append(os.path.join(os.getcwd(),'exp'))
import time
import atexit
import argparse
import datetime
from pathlib import Path
from functools import partial

import numpy  as np
import GPUtil as gu
from nb_helpers import GpuLockedTimeout, GpuUsageTimeout


class Lock:
    def __init__(self, path, data, seconds_delay):
        timedelta = datetime.timedelta(seconds=seconds_delay)
        time_out = datetime.datetime.now() + timedelta
        timestamp = '{:%Y_%b_%d_%H_%M_%S_%f}'.format(time_out)
        lock_name = f'dhpo_{timestamp}.lock'
        self.lock_name = path / lock_name
        self.data = data

    def __enter__(self):
        try:
            print(f'Locking "{self.data}" @ {self.lock_name}')
            with open(self.lock_name, 'w+') as f:
                f.write(self.data)
            os.chmod(self.lock_name, 0o776)
        except Exception as e:
            print(f'Cant get a lock! {self.lock_name} \n', e)
            self.lock_name = None

        return self.lock_name

    def __exit__(self, type, value, traceback):
        try:
            if self.lock_name:
                os.remove(self.lock_name)
        except Exception as e:
            print(f'Cant remove lock! {self.lock_name}\n', e)


def base_exit_handler(lock_name):
    try:
        if lock_name:
            if os.path.exists(lock_name): os.remove(lock_name)
    except Exception as e:
        print(f'Cant remove lock! {lock_name}\n', e)

def lock(gpus, seconds_delay, path='/tmp'):
    gpus = str(gpus).strip('()')
    lock = Lock(path, gpus, seconds_delay)
    with lock as l:
        exit_handler = partial(base_exit_handler, lock_name=l)
        atexit.register(exit_handler)
        time.sleep(seconds_delay)

def check_locks(path):
    g = path.rglob('dhpo_*.lock')
    locked_gpus = set()
    for l in g:
        if is_expired(l):
            print(f'Lock {l} is expired, deleting')
            clean_up(l)
            continue
        locked_gpus.update(read_lock(l))
    return locked_gpus

def list_locks(path):
    g = path.rglob('dhpo_*.lock')
    if g:
        for i, l in enumerate(g):
            print(f'\t{i}. {l.name}')
            with open(l, 'r') as f:
                print(f'\t\tGPUS: {f.read()}')
    else:
        print('\tThere is no locks')

def is_expired(name):
    date = name.name.strip('dhpo_').rstrip('.lock')
    datetime_object = datetime.datetime.strptime(date, '%Y_%b_%d_%H_%M_%S_%f')
    datetime_object, datetime_object > datetime.datetime.now()
    return datetime_object < datetime.datetime.now()

def clean_up(name): os.remove(name)

def read_lock(name):
    with open(name, 'r') as f:
        data = f.read()
    return set([int(i) for i in data if i.isdigit()])

def check_gpu_access(path, gpus):
    print(f'\n\tChecking {path} for locks on gpu {gpus}...')

    target_gpu = set([int(i) for i in gpus if i.isdigit()])
    all_gpus = set((0,1,2,3))

    locked_gpus = check_locks(path)
    avail_gpus = all_gpus - locked_gpus
    if target_gpu.issubset(avail_gpus):
        print(f'\n\tgpu {target_gpu} is avaliable...')
    else:
        print(f'\n\tWaiting, gpu #{target_gpu} is locked. Current gpus under lock: {locked_gpus}')
        raise GpuLockedTimeout

def check_gpu_usage(gpus, threshlod=.2, delay=.1):
    gpus = set([int(i) for i in gpus if i.isdigit()])
    load = get_gpu_load(delay)
    for g in gpus:
        if load[g] > threshlod:
            print(f'Usage on gpu{g} : {load[g]}')
            raise GpuUsageTimeout
    print(f'Gpu usage is acceptable: {load}')

def get_gpu_load(delay=.1):
    load = []
    for i in range(10):
        gpus = gu.getGPUs()
        c_load = [g.load for g in gpus]
        load.append(c_load)
        time.sleep(delay)
    return np.array(load).mean(axis=0)