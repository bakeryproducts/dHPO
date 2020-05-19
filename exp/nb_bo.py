
#################################################
### THIS FILE WAS AUTOGENERATED! DO NOT EDIT! ###
#################################################
# file to edit: dev_nb/bo.ipynb

import os
import sys
sys.path.append(os.path.join(os.getcwd(),'exp'))

import numpy as np
from pprint import pprint

from skopt import Optimizer
from skopt.space import Real
#from bayes_opt import BayesianOptimization, UtilityFunction, SequentialDomainReductionTransformer

from config import cfg

class BaseConfigBo:
    def __init__(self, n):
        self.n_points = n

    def get_values(self, o, names):
        o.update_next()
        set_points = o.ask(n_points=self.n_points)
        points = [{n:p for n,p in zip(sorted(names), points)} for points in set_points]
        return points

    def init_opt(self, bounds):
        return Optimizer(
                    dimensions=bounds,
                    random_state=1,
                    base_estimator='gp',
                    n_initial_points=3*self.n_points)

    def register(self, o, hp_points):
        NEGATIVE = -1
        for hp_point in hp_points:
            points = hp_point['points']
            x = [points[k] for k in sorted(points)]
            y = NEGATIVE * hp_point['target']
            o.tell(x, y)
            print(f'Registrating: {x}, {y}')

    def init_map(self):
        raise NotImplementedError

    def read_params(self, params):
        bounds = {}
        space_type = Real
        space_args = {'prior':'uniform', 'transform':None}
        for p in params:
            space_args['low'],space_args['high'] = p['bounds'][0], p['bounds'][1]
            bounds[p['name']] = space_type(**space_args)

        bounds = [bounds[k] for k in sorted(bounds)]
        return bounds

    def create_state(self, points, params, idx):
        names = [p['name'] for p in params]
        bounds = self.read_params(params)
        o = self.init_opt(bounds)

        if points:
            self.register(o, points)

        new_params = self.get_values(o, names)
        pprint(new_params, indent=4)
        new_params = new_params[idx]

        params_map = self.init_map()
        cfg = {}
        for name, (full_name, p_type, default_value) in params_map.items():
            value = new_params.get(name, default_value)
            if value is not np.NaN:
                cfg[full_name] = p_type(value)
        return new_params, cfg