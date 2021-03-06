
#################################################
### THIS FILE WAS AUTOGENERATED! DO NOT EDIT! ###
#################################################
# file to edit: dev_nb/tools.ipynb

import os
import sys
import atexit
sys.path.append(os.path.join(os.getcwd(),'exp'))

import fire
import docker
from functools import partial
from pathlib import Path

from config import cfg
from nb_locker import check_locks, list_locks, lock as locker
from nb_helpers import CantDoThatMuch, clrd, log

def cycle_c_gen(pat=cfg.DOCKER.CONTAINER_PREFIX, list_all=False):
    containers = (docker.from_env()).containers.list(all=list_all)
    for i, c in enumerate(containers):
        name = clrd(c.name, 'BLUE')
        print(f'{i}. container\t {name} :')
        if pat in c.name: yield c
        else: print(f'\t Skipping {name}, not part of dHPO\n')

def check_gpu(container):
    env_vars = container.attrs['Config']['Env']
    for v in env_vars:
        if v.startswith('CUDA_VISIBLE_DEVICES'):
            gpus = v.split("=")[-1]
            break
    else: raise UnknownGpuDevice
    return set([int(g) for g in gpus.split(',')])

def check_status(c):
    c.reload()
    return c.status

def is_running(c): return check_status(c) == 'running'
def is_paused(c): return check_status(c) == 'paused'

def unpause(c):
    if is_paused(c):
        print(f'\t UNpausing {c.name}...')
        c.unpause()
        return True
    elif is_running(c):
        log(f'\tWARNING {c.name} already running!', c='BROWN')
        return True
    else:
        print(f'\tSomething is wrong with {c.name}, check it manually')
        return False

def pause(c):
    if is_running(c):
        print(f'\t Pausing {c.name}...')
        c.pause()
        return True
    elif is_paused(c):
        log(f'\tWARNING {c.name} already on pause!', c='BROWN')
        return True
    else:
        print(f'\tSomething is wrong with {c.name}, check it manually')
        return False

def switch(gpus, mode):
    usage =''' Usage:
        switch $GPUS $MODE
        switch 0 pause
        switch 0,1 unpause
    '''
    if gpus is None or mode not in ['pause', 'unpause']:
        log(usage, c='RED')
        return

    if not isinstance(gpus, tuple): gpus = gpus,
    do = pause if mode == 'pause' else unpause

    for c in cycle_c_gen():
        c_gpus = check_gpu(c)
        if c_gpus.intersection(gpus):
            print(f'\t{c.name} is using GPUS{c_gpus}, trying to set on "{mode}"')
            do(c)
        else:
            print(f'\tSkipping {c.name}, on GPU{c_gpus}')

def forced(func):
    def force(force_arg, *args, **kwargs):
        if force_arg == 'force':
            return func(*args, **kwargs)
        else:
            log('Specify force arg: dhpoctl kill | clean  force', c='BROWN')
    return force

def status():
    print(f'  *{cfg.DOCKER.CONTAINER_PREFIX}* containers: ')
    for c in cycle_c_gen():
        gpu = str(check_gpu(c)).strip('{}')
        color = 'GREEN' if c.status == 'running' else 'BROWN'
        print(clrd(f'\t GPU# {gpu} {c.status}', color))
    print(f'Active locks @ {cfg.GPUS.LOCK}:')
    list_locks(Path(cfg.GPUS.LOCK))

@forced
def clean():
    ''' Cleans up exited dhpo containers '''
    for c in cycle_c_gen(list_all=True):
        if c.status == 'exited': c.remove()
        else: print(f'\tSkipping, status:{c.status}')

@forced
def kill(gpus):
    '''
    Kills dhpo containers on specified gpu(s)
    Args:
        gpus: int or tuple | 0 | 0,1 | 2,3,6
    '''
    if not isinstance(gpus, tuple): gpus = gpus,

    for c in cycle_c_gen():
        c_gpus = check_gpu(c)
        if c_gpus.intersection(gpus):
            if c.status == 'running' or c.status == 'paused':
                print(clrd(f'Killing {c.name}','RED'))
                c.kill()
            else: print(f'\tSkipping, status:{c.status}')
        else:
            print(f'\tSkipping, @ gpu {c_gpus}')

def lock(gpus, delay):
    ''' Locks up gpu for user

        Lock dhpo usage (pause docker container) of specified gpu(s)
        for some period of time (delay)
    Args:
        gpus: GPU ids, int or tuple.  | 0 | 0,1 | 2,3,6
        delay: Time interval in minutes, float,
    '''
    delay = delay * 60
    if delay > 8*60: raise CantDoThatMuch
    switch(gpus, 'pause')
    #atexit.register(reset)
    locker(gpus, delay, path=Path(cfg.GPUS.LOCK))

def reset():
    ''' Updating locks state, dockers state. Removing expired locks '''
    lp = Path(cfg.GPUS.LOCK)
    for c in cycle_c_gen():
        locked_gpus = check_locks(lp)
        if not locked_gpus.intersection(check_gpu(c)): unpause(c)
        else: print('locked, skip')

if __name__ == '__main__':
    fire.Fire({'status':status,
               'lock':lock,
               'kill':kill,
               'clean':clean,
               'reset':reset,
               'z__switch':switch,
              })