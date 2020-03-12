# -*- encoding: ascii -*-
# Python 2 and 3 compatible
from __future__ import division, absolute_import, print_function
from prga.compatible import *

from prga.core.context import Context
from prga.core.common import ModuleView
from prga.util import enable_stdout_logging

import re   # for the simple FASM, regexp processing is good enough
import struct
from bitarray import bitarray
import logging

__all__ = ['bitgen_scanchain']

_logger = logging.getLogger(__name__)
_reprog_param = re.compile("^b(?P<offset>\d+)\[(?P<high>\d+):(?P<low>\d+)\]=(?P<width>\d+)'b(?P<content>[01]+)$")

def bitgen_scanchain(bitstream_size     # bitstream size
        , istream                       # input file-like object
        , ostream                       # output file-like object
        ):
    """Generate bitstream for scanchain configuration circuitry.

    Args:
        bitstream_size (:obj:`int`): bitstream size
        istream (file-like object):
        ostream (file-like object):
    """
    qwords = bitstream_size // 64
    remainder = bitstream_size % 64 
    if remainder > 0:
        qwords += 1
    bits = bitarray('0', endian='little') * (qwords * 64)
    # process features
    for lineno, line in enumerate(istream):
        segments = line.strip().split('.')
        if segments[-1] == 'ignored':
            continue
        base = sum(int(segment[1:]) for segment in segments[:-1])
        if '[' in segments[-1]:
            matched = _reprog_param.match(segments[-1])
            base += int(matched.group('offset'))
            segment = bitarray(matched.group('content'))
            segment.reverse()
            high, low, width = map(lambda x: int(matched.group(x)), ('high', 'low', 'width'))
            if high < low:
                raise RuntimeError("LINE {:>08d}: Invalid range specifier".format(lineno + 1))
            elif width != len(segment):
                raise RuntimeError("LINE {:>08d}: Explicit width specifier mismatches with number of bits"
                        .format(lineno + 1))
            actual_width = high - low + 1
            if actual_width > width:
                segment.extend((False, ) * (actual_width - width))
            bits[base + low: base + low + actual_width] = segment[0: actual_width]
        else:
            bits[base + int(segments[-1][1:])] = True
    # emit lines in quad words
    for i in range(qwords):
        ostream.write('{:0>16x}'.format(struct.unpack('<Q', bits[i*64:(i + 1)*64].tobytes())[0]) + '\n')

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(
            description="Bitstream generator for scanchain configuration circuitry")
    
    parser.add_argument('summary', type=argparse.FileType(OpenMode.rb),
            help="Pickled architecture context or summary object")
    parser.add_argument('fasm', type=argparse.FileType('r'),
            help="FASM generated by the genfasm util of VPR")
    parser.add_argument('memh', type=argparse.FileType('w'),
            help="Generated bitstream in MEMH format for Verilog simulation")

    args = parser.parse_args()
    enable_stdout_logging(__name__, logging.INFO)
    summary = Context.unpickle(args.summary)
    if isinstance(summary, Context):
        summary = summary.summary
    bitstream_size = summary.bitstream_size
    _logger.info("Architecture context summary parsed")
    _logger.info("Bitstream size: {}".format(bitstream_size))
    bitgen_scanchain(bitstream_size, args.fasm, args.memh)
    _logger.info("Bitstream generated. Bye")