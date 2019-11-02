# -*- encoding: ascii -*-
# Python 2 and 3 compatible
from __future__ import division, absolute_import, print_function
from prga.compatible import *

from prga.flow.context import ArchitectureContext
from prga.util import uno

from prga_tools.util import find_verilog_top, parse_parameters

import jinja2 as jj
import os

def generate_makefile(context, template, ostream,
        tb_top, tb_sources, behav_top, behav_sources, yosys_script,
        channel_width, archdef, rrgraph, fpga_sources,
        compiler = "vcs", partial_binding = None, tb_plus_args = None,
        tb_includes = None, tb_defines = None, tb_parameters = None,
        behav_includes = None, behav_defines = None, behav_parameters = None):
    """Generate Makefile for simulation flow."""
    param = {}
    param["compiler"] = compiler

    # target (behavioral model)
    target = param["target"] = {}
    target["name"] = behav_top.name
    target["sources"] = uno(behav_sources, tuple())
    target["defines"] = uno(behav_defines, tuple())
    target["parameters"] = uno(behav_parameters, {})

    # host (testbench)
    host = param["host"] = {}
    host["name"] = tb_top.name
    host["sources"] = uno(tb_sources, tuple())
    host["defines"] = uno(tb_defines, tuple())
    host["parameters"] = uno(tb_parameters, {})
    host["args"] = uno(tb_plus_args, tuple())

    # context
    param["context"] = context

    # yosys script
    param["yosys_script"] = yosys_script

    # vpr settings
    vpr = param["vpr"] = {}
    vpr["channel_width"] = channel_width
    vpr["archdef"] = archdef
    vpr["rrgraph"] = rrgraph

    # fpga sources
    param["rtl"] = fpga_sources

    # partial IO binding
    vpr["partial_binding"] = partial_binding

    # generate
    template.stream(param).dump(ostream)

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(
            description="Testbench generator for bitchain-style configuration circuitry")
    
    parser.add_argument('context', type=str, help="Pickled architecture context object")
    parser.add_argument('output', type=argparse.FileType("w"), help="Generated Makefile")

    parser.add_argument('-t', '--testbench', type=str, nargs='+', dest="testbench",
            help="Testbench file(s) for behavioral model")
    parser.add_argument('--testbench_top', type=str,
            help="Top-level module name of the testbench. Required if the testbench comprises multiple files/modules")
    parser.add_argument('--testbench_includes', type=str, nargs="+", default=[],
            help="Include directories for the testbench")
    parser.add_argument('--testbench_defines', type=str, nargs="+", default=[],
            help="Macros for the testbench. Use MACRO for valueless macro, and MACRO=VALUE for macros with value")
    parser.add_argument('--testbench_parameters', type=str, nargs="+", default=[],
            help="Parameters for the testbench: PARAMETER0=VALUE0 PARAMETER1=VALUE1 ...")
    parser.add_argument('--testbench_plus_args', type=str, nargs="+", default=[],
            help="Plus arguments to run the testbench. Use ARG for valueless args, and ARG=VALUE for args with value")

    parser.add_argument('-m', '--model', type=str, nargs='+', dest="model",
            help="Source file(s) for the target design")
    parser.add_argument('--model_top', type=str,
            help="Top-level module name of the target design. Required if the design comprises multiple files/modules")
    parser.add_argument('--model_includes', type=str, nargs="+", default=[],
            help="Include directories for the target design")
    parser.add_argument('--model_defines', type=str, nargs="+", default=[],
            help="Macros for the target design. Use MACRO for valueless macro, and MACRO=VALUE for macros with value")
    parser.add_argument('--model_parameters', type=str, nargs="+", default=[],
            help="Parameters for the target design: PARAMETER0=VALUE0 PARAMETER1=VALUE1 ...")

    parser.add_argument('-y', '--yosys', type=str, dest="yosys",
            help="Yosys script to synthesize the target design")
    parser.add_argument('--io', type=str, dest="io",
            help="Partial or complete assignment of the IOs")
    parser.add_argument('-c', '--compiler', type=str, choices=['vcs', 'iverilog'], dest='compiler',
            help="Verilog compiler used to build the simulator")

    args = parser.parse_args()

    context = ArchitectureContext.unpickle(args.context)
    channel_width = 2 * sum(sgmt.width * sgmt.length for sgmt in itervalues(context.segments))

    # get verilog template
    env = jj.Environment(loader=jj.FileSystemLoader(
        os.path.join(os.path.abspath(os.path.dirname(__file__)), 'templates')))

    tb_top = find_verilog_top(args.testbench, args.testbench_top)
    tb_top.parameters = parse_parameters(args.testbench_parameters)
    behav_top = find_verilog_top(args.model, args.model_top)
    behav_top.parameters =parse_parameters(args.model_parameters) 

    generate_makefile(args.context, env.get_template('tmpl.Makefile'), args.output,
            tb_top, args.testbench, behav_top, args.model, args.yosys,
            channel_width, context._vpr_archdef, context._vpr_rrgraph, context._verilog_sources,
            args.compiler, args.io, args.testbench_plus_args, args.testbench_includes, args.testbench_defines,
            args.testbench_parameters, args.model_includes, args.model_defines, args.model_parameters)