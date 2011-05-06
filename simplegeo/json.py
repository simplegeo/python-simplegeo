# -*- coding: utf-8 -*-
#
# © 2011 SimpleGeo, Inc All rights reserved.
# Author: Ian Eure <ian@simplegeo.com>
#

"""JSON helper."""

from functools import partial

import simplejson

loads = partial(simplejson.loads, use_decimal=True)
load = partial(simplejson.load, use_decimal=True)
dumps = partial(simplejson.dumps, use_decimal=True)
dump = partial(simplejson.dump, use_decimal=True)
