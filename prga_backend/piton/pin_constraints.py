# -*- encoding: ascii -*-
# Python 2 and 3 compatible
from __future__ import division, absolute_import, print_function
from prga.compatible import *

from prga.core.common import SegmentID, BlockPinID, Orientation, Direction, Dimension

import sys
import logging

_logger = logging.getLogger(__name__)

class BackendPinConstraintsGenerator(object):
    """Wrapper for algorithms generating backend pin placement constraints."""

    @classmethod
    def generate_for_subarray(cls, module, f = sys.stdout):
        """Generate pin placement constraints for subarray ``module``.

        This method generates `set_individual_pin_constraints` commands for the routing node pins of ``module``.
        """
        for key, port in iteritems(module.ports):
            ori, offset = None, None
            if isinstance(key, SegmentID):
                dim = key.orientation.dimension
                majorpos, minorpos = key.position[dim], key.position[dim.perpendicular]
                # boundary
                majorbound, minorbound = dim.case( (module.width, module.height), (module.height, module.width) )
                if 0 <= minorpos < minorbound - 1:
                    ori = port.direction.case(key.orientation.opposite, key.orientation)
                    offset = minorpos
                elif minorpos == -1:
                    ori = Orientation.compose(dim.perpendicular, Direction.dec)
                    offset = max(0, min(majorbound - 1, majorpos))
                elif minorpos == minorbound - 1:
                    majorpos2 = majorpos
                    if port.direction.is_output:
                        majorpos2 += port.direction.case(1, -1) * key.prototype.length
                    if 0 <= majorpos2 < majorbound:
                        ori = Orientation.compose(dim.perpendicular, Direction.inc)
                        offset = max(0, min(majorbound - 1, majorpos))
                    else:
                        ori = port.direction.case(key.orientation.opposite, key.orientation)
                        offset = minorpos
                else:
                    raise RuntimeError("Routing key '{}' is not touching array '{}'"
                            .format(key, module))
            elif isinstance(key, BlockPinID):
                dim = key.prototype.orientation.dimension
                if key.position[dim] < 0:
                    ori = Orientation.compose(dim, Direction.dec)
                elif key.position[dim] >= dim.case(module.width, module.height):
                    ori = Orientation.compose(dim, Direction.inc)
                else:
                    diff_dec = key.position[dim]
                    diff_inc = dim.case(module.width, module.height) - 1 - key.position[dim]
                    if diff_dec > diff_inc:
                        ori = Orientation.compose(dim, Direction.dec)
                    else:
                        ori = Orientation.compose(dim, Direction.inc)
                offset = min(dim.case(module.width, module.height) - 1, max(0, key.position[dim.perpendicular]))
            else:
                _logger.info("Ignoring non-routing pin: {}".format(port))
                continue
            if ori.is_east:
                offset = module.height - 1 - offset
            elif ori.is_south:
                offset = module.width - 1 - offset
            f.write(("set_individual_pin_constraints -ports [get_ports {0}[*]] -side {1} "
                "-offset [list [expr {2} * $PRGA_TILE_{metric}] [expr {3} * $PRGA_TILE_{metric}]]\n")
                .format(port.name, ori.case(2, 3, 4, 1), offset, offset + 1,
                    metric = ori.dimension.case("HEIGHT", "WIDTH")))
