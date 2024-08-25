#!/usr/bin/env python
# This is needed instead of running ipython directly,
# for the same issue as described here:
# https://github.com/ipython/ipython/issues/11730
import gevent.monkey
gevent.monkey.patch_all()

import IPython
IPython.start_ipython()
