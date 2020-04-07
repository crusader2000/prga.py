# -*- encoding: ascii -*-
# Python 2 and 3 compatible
from __future__ import division, absolute_import, print_function
from prga.compatible import *

from prga.netlist.common import NetType
from prga.netlist.net.util import NetUtils
from prga.core.common import Position, Subtile, SegmentID, BlockPinID, Corner
from prga.core.array import NonLeafArrayBuilder
from prga.passes.vpr import VPR_RRG_Generation

import networkx as nx
from itertools import chain

class BackendUtils(object):
    """Wrapper for backend utility functions."""

    @classmethod
    def _backtrack_net(cls, g, array, net):
        def yield_or_stop(m, n):
            idx, net_key = n
            if isinstance(idx, NetType):
                return False
            elif isinstance(net_key[0], SegmentID):
                return net_key[0].segment_type.is_sboxout
            elif isinstance(net_key[0], BlockPinID):
                return False
            else:
                return True
        def skip(m, n):
            idx, net_key = n
            if isinstance(net_key[0], SegmentID) or isinstance(net_key[0], BlockPinID):
                return not m.hierarchy[net_key[1:]].model.module_class.is_routing_box
            return False
        for path in NetUtils._navigate_backwards(array, NetUtils._reference(net),
                yield_ = yield_or_stop, stop = yield_or_stop, skip = skip):
            cur = path[0]
            for next_ in path[1:]:
                g.add_edge(cur, next_)
                cur = next_

    @classmethod
    def build_timing_graph_array(cls, array, node_by_name = True):
        """Build the timing graph for array."""
        g = nx.DiGraph()
        for x, y in product(range(array.width), range(array.height)):
            pos = Position(x, y)
            # block pin
            inst = NonLeafArrayBuilder._get_hierarchical_root(array, pos, Subtile.center)
            if inst is not None and pos == VPR_RRG_Generation._calc_hierarchical_position(inst):
                # this is a block instance
                block = inst.model
                for subblock in range(block.capacity):
                    inst = NonLeafArrayBuilder._get_hierarchical_root(array, pos, subblock)
                    for pin in itervalues(inst.pins):
                        if pin.model.direction.is_output or hasattr(pin.model, 'global_'):
                            continue
                        for bit in pin:
                            cls._backtrack_net(g, array, bit)
            # segments
            for corner in Corner:
                inst = NonLeafArrayBuilder._get_hierarchical_root(context.top, pos, corner.to_subtile())
                if inst is None or not inst.model.module_class.is_switch_box:
                    continue
                for node, port in iteritems(inst.model.ports):
                    if not node.segment_type.is_sboxout:
                        continue
                    pin = port._to_pin( inst )
                    args = self._analyze_routable_pin(pin)
                    for bit in pin:
