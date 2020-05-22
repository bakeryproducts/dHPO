from yacs.config import CfgNode as CN

_C = CN()

_C.OWNER='sokolov'

_C.GPUS = CN()
_C.GPUS.IDS= [1]
_C.GPUS.LOCK = '/home/sokolov/work/cycler/dHPO/sync/locks'

_C.DAG = CN()
_C.DAG.ROOT = '/home/sokolov/work/cycler/dHPO/exp/'
_C.DAG.RUNS = '/home/sokolov/work/cycler/dHPO/results/dhpo_runs/'
_C.DAG.NAME = 'dhpo2'
_C.DAG.DESC = 'testing'
_C.DAG.SCHED_INTERVAL = '@daily'
_C.DAG.RETRIES = 30
_C.DAG.RETRY_DELAY = 10
_C.DAG.DEF_POOL = 'sokolov_pool_gpu0'
_C.DAG.POOL_PREFIX = 'sokolov_pool_gpu'

_C.DOCKER = CN()
_C.DOCKER.CONTAINER_PREFIX = '_dHPO_'
_C.DOCKER.RUN_PATH = '/home/sokolov/work/cycler/dHPO/results/runs/'


cfg = _C