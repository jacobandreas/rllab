from __future__ import print_function
from __future__ import absolute_import

import gym
import gym.envs
import gym.spaces
### from gym.monitoring import monitor
from gym.wrappers import Monitor
import os
import os.path as osp
from rllab.envs.base import Env, Step
from rllab.core.serializable import Serializable
from rllab.spaces.box import Box
from rllab.spaces.discrete import Discrete
from rllab.misc import logger
import logging


def convert_gym_space(space):
    if isinstance(space, gym.spaces.Box):
        return Box(low=space.low, high=space.high)
    elif isinstance(space, gym.spaces.Discrete):
        return Discrete(n=space.n)
    else:
        raise NotImplementedError


class CappedCubicVideoSchedule(object):
    def __call__(self, count):
        if count < 1000:
            return int(round(count ** (1. / 3))) ** 3 == count
        else:
            return count % 1000 == 0

class FixedIntervalVideoSchedule(object):

    def __init__(self, interval):
        self.interval = interval

    def __call__(self, count):
        return count % self.interval == 0


class NoVideoSchedule(object):
    def __call__(self, count):
        return False


class GymEnv(Env, Serializable):
    def __init__(self, env_name, record_video=True, video_schedule=None,
            log_dir=None, force_reset=False):
        if log_dir is None:
            if logger.get_snapshot_dir() is None:
                logger.log("Warning: skipping Gym environment monitoring since snapshot_dir not configured.")
            else:
                log_dir = os.path.join(logger.get_snapshot_dir(), "gym_log")
        Serializable.quick_init(self, locals())

        env = gym.envs.make(env_name)
        self.env = env
        self.env_id = env.spec.id

        if log_dir is None:
            self.monitoring = False
        else:
            if video_schedule is None:
                video_schedule = CappedCubicVideoSchedule()
            self.env = Monitor(self.env, log_dir, video_callable=video_schedule, force=True)
            self.monitoring = True

        ### monitor.logger.setLevel(logging.WARNING)
        ### if log_dir is None:
        ###     self.monitoring = False
        ### else:
        ###     if not record_video:
        ###         video_schedule = NoVideoSchedule()
        ###     else:
        ###         if video_schedule is None:
        ###             video_schedule = CappedCubicVideoSchedule()
        ###     self.env.monitor.start(log_dir, video_schedule)
        ###     self.monitoring = True

        self._observation_space = convert_gym_space(env.observation_space)
        self._action_space = convert_gym_space(env.action_space)
        self._horizon = env.spec.timestep_limit
        self._log_dir = log_dir
        self._force_reset = force_reset

    @property
    def observation_space(self):
        return self._observation_space

    @property
    def action_space(self):
        return self._action_space

    @property
    def horizon(self):
        return self._horizon

    def reset(self):
        #return self.env.reset()
        if self._force_reset and self.monitoring:
            from gym.wrappers.monitoring import Monitor
            assert isinstance(self.env, Monitor)
            recorder = self.env.stats_recorder
            if recorder is not None:
                recorder.done = True
        return self.env.reset()

    def step(self, action):
        next_obs, reward, done, info = self.env.step(action)
        return Step(next_obs, reward, done, **info)

    def render(self):
        self.env.render()

    def terminate(self):
        if self.monitoring:
            self.env.monitor.close()
            if self._log_dir is not None:
                print("""
    ***************************

    Training finished! You can upload results to OpenAI Gym by running the following command:

    python scripts/submit_gym.py %s

    ***************************
                """ % self._log_dir)
