
#################################################
### THIS FILE WAS AUTOGENERATED! DO NOT EDIT! ###
#################################################
# file to edit: dev_nb/locker.ipynb

import argparse
import numpy  as np
from pathlib import Path
import os
import datetime
import time
import atexit
from functools import partial

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

def lock(*, gpus='', seconds_delay=.1, path='/tmp'):
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

def is_expired(name):
    date = name.name.strip('dhpo_').rstrip('.lock')
    datetime_object = datetime.datetime.strptime(date, '%Y_%b_%d_%H_%M_%S_%f')
    datetime_object, datetime_object > datetime.datetime.now()
    return datetime_object < datetime.datetime.now()

def clean_up(name):
    print(f'\n\t ooo deleting{name}')
    os.remove(name)

def read_lock(name):
    with open(name, 'r') as f:
        data = f.read()
    return set([int(i) for i in data if i.isdigit()])

def check_gpu_access(path, gpus):
    print(f'\n\tChecking {path} for locks on gpu {gpus}...')
    #path = Path('./test')
    #gpus='0'
    #lock_delay = 5

    target_gpu = set([int(i) for i in gpus if i.isdigit()])
    all_gpus = set((0,1,2,3))

    #while True:
    locked_gpus = check_locks(path)
    avail_gpus = all_gpus - locked_gpus
    if target_gpu.issubset(avail_gpus):
        print(f'\n\tgpu {target_gpu} is avaliable...')
        #break
    else:
        print(f'\n\tWaiting, gpu #{target_gpu} is locked. Current gpus under lock: {locked_gpus}')
        #time.sleep(lock_delay)
        raise TimeoutError

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--mdelay', '-md', dest='minute_delay',
                    default=.1,
                    help='delay in minutes')
    parser.add_argument('--gpus', '-g', dest='gpus',
                    default=None,
                    help='gpus to lock, 0,2')

    args = parser.parse_args()
    gpus = args.gpus
    p = Path('/home/sokolov/work/cycler/crsch_cycle/locks')

    minute_delay = args.minute_delay
    seconds_delay = float(minute_delay) * 60
    print(f'DELAY: {seconds_delay} seconds')
    print(f'GPUS: {gpus}')
    print(f'PATH: {p}')
    lock(path=p, gpus=gpus, seconds_delay=seconds_delay)