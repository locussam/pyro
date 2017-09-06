import pyro
import torch
import sys
if sys.version_info[0] < 3:
    from Queue import Queue
else:
    from queue import Queue

import pyro.poutine as poutine
from pyro.infer import TracePosterior


class Search(TracePosterior):
    """
    New Trace and Poutine-based implementation of systematic search
    """
    def __init__(self, model, max_tries=1e6):
        """
        Constructor
        """
        self.model = model
        self.max_tries = int(max_tries)

    def _traces(self, *args, **kwargs):
        """
        algorithm entered here
        Returns traces from the posterior
        Running until the queue is empty and collecting the marginal histogram
        is performing exact inference
        """
        self.queue = Queue()
        self.queue.put(poutine.Trace())

        p = poutine.trace(
            poutine.queue(self.model, queue=self.queue, max_tries=self.max_tries))
        while not self.queue.empty():
            tr = p(*args, **kwargs)
            yield (tr, tr.log_pdf())

    def log_z(self, *args, **kwargs):
        """
        harmonic mean log-evidence estimator
        """
        # XXX weights not correct?
        log_z = 0.0
        n = 0
        # TODO parallelize
        for _, log_weight in self._traces(*args, **kwargs):
            n += 1
            log_z = log_z + log_weight
        return log_z / n
