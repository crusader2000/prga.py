# -*- encoding: ascii -*-
# Python 2 and 3 compatible
from __future__ import division, absolute_import, print_function
from prga.compatible import *

from prga.util import Object, Enum

import pexpect, logging, contextlib, time, os, re

_logger = logging.getLogger(__name__)

_pt_shell_setup_script = [
"set DV_ROOT $::env(DV_ROOT)", 
"set PITON_PROCESS $::env(PITON_PROCESS)", 
"set MODULE_PATH $::env(MODULE_PATH)", 
"set BUILD_ID $::env(BUILD_ID)", 
"source -echo ${DV_ROOT}/asicflow/${PITON_PROCESS}/generic/sta/pt/pt_setup.tcl",
"set link_create_black_boxes false",
"""
if {$input_from == "DC"} {
    read_verilog $DC_NETLIST_FILES
} else {
    read_verilog $ICC2_NETLIST_FILES
}
""",
"current_design $DESIGN_NAME",
"link",
"""
foreach {max_library min_library} "$MIN_LIBRARY_FILES $ADDITIONAL_MIN_LIBRARY_FILES" {
  set_min_library $max_library -min_version $min_library
}
""",
"""
if {$input_from == "DC"} {
    if { [info exists DC_PARASITIC_PATHS] && [info exists DC_PARASITIC_FILES] } {
        foreach para_path $DC_PARASITIC_PATHS para_file $DC_PARASITIC_FILES {
            if {[string compare $para_path $DESIGN_NAME] == 0} {
                read_parasitics -format spef $para_file
            } else {
                read_parasitics -path $para_path -format spef $para_file
            }
        }
    }
} else {
    if { [info exists ICC2_PARASITIC_PATHS] && [info exists ICC2_PARASITIC_FILES] } {
        foreach para_path $ICC2_PARASITIC_PATHS \
                para_max_file $ICC2_PARASITIC_MAX_FILES \
                para min_file $ICC2_PARASITIC_MIN_FILES {
            if {[string compare $para_path $DESIGN_NAME] == 0} {
                read_parasitics -format sbpf "$para_max_file  $para_min_file"
            } else {
                read_parasitics -path $para_path -format sbpf "$para_max_file $para_min_file"
            }
        }
    }
}
""",
"""
if {$input_from == "DC"} {
    if  {[info exists DC_CONSTRAINT_FILES]} {
        foreach constraint_file $DC_CONSTRAINT_FILES {
            if {[file extension $constraint_file] eq ".sdc"} {
                read_sdc -echo $constraint_file
            } else {
                source -echo $constraint_file
            }
        }
    }
} else {
    if  {[info exists ICC2_CONSTRAINT_FILES]} {
        foreach constraint_file $ICC2_CONSTRAINT_FILES {
            if {[file extension $constraint_file] eq ".sdc"} {
                read_sdc -echo $constraint_file
            } else {
                source -echo $constraint_file
            }
        }
    }
}
""",
"update_timing -full",
"set timing_report_unconstrained_paths true",
]

__all__ = ["BackendSTASessionSynopsysPT"]

class BackendSTASessionSynopsysPT(Object, contextlib.AbstractContextManager):
    """Wrapper class for managing and interacting with a subprocess of synopsys PrimeTime."""

    __slots__ = ['child', "compiled_reprogs"]
    def __init__(self, DV_ROOT, MODULE_PATH, BUILD_ID, PITON_PROCESS = 'gf14_invecas', **kwargs):
        command = kwargs.pop("command", "pt_shell")
        encoding = kwargs.pop("encoding", "ascii")
        env = os.environ
        env.update(DV_ROOT = DV_ROOT,
                MODULE_PATH = MODULE_PATH,
                BUILD_ID = BUILD_ID,
                PITON_PROCESS = PITON_PROCESS)
        self.child = pexpect.spawn(command, env = env, encoding = encoding, **kwargs)
        # setup
        self.command("source -echo", os.path.join(os.path.abspath(os.path.dirname(__file__)), "script",
            "pt_setup.tcl"))
        # compile re programs
        self.compiled_reprogs = {
                "error": re.compile("^Error:"),
                "no_path": re.compile("^No (?:constrained p|P)aths\.$"),
                "retval": re.compile("^[01]$"),
                "clock": re.compile("^clock network delay \(ideal\)"),
                "point": re.compile("^(?P<net>\S+)\s+\((?P<model>\w+)\).+?(?P<incr>\d+\.\d+).+?(?P<path>\d+\.\d+)"),
                "arrival": re.compile("^data arrival time"),
                "net": re.compile("^(?P<net>\w+)\[(?P<idx>\d+)\]$"),
                }

    def __exit__(self, exc_type, exc_value, traceback):
        if exc_type is None:
            self.child.sendeof()
            # give it one second
            time.sleep(1)
            # force quit if it's still alive
            self.child.close(force = True)
            return True
        return None

    def command(self, *commands):
        self.child.expect("pt_shell>")
        self.child.sendline(" ".join(" ".join(command.split()) for command in commands))

    def readline(self, *args, **kwargs):
        return self.child.readline(*args, **kwargs)

    class _TimingReportParserState(Enum):
        init = 0
        path = 1

    def report_timing(self, *args):
        command = "report_timing -slack_lesser_than 100000 -include_hierarchical_pins -nosplit -input_pins"
        if args:
            command += " " + " ".join(args)
        self.command(command)
        # process response
        state = self._TimingReportParserState.init
        while True:
            line = self.readline().strip()
            if state.is_init:
                if self.compiled_reprogs["error"].match(line):
                    raise RuntimeError(line)
                elif self.compiled_reprogs["no_path"].match(line):
                    return
                elif self.compiled_reprogs["clock"].match(line):
                    state = self._TimingReportParserState.path
                elif self.compiled_reprogs["retval"].match(line):
                    return
            elif state.is_path:
                if self.compiled_reprogs["arrival"].match(line):
                    state = self._TimingReportParserState.init
                    yield None
                matched = self.compiled_reprogs["point"].match(line)
                if matched is None:
                    continue
                # net = matched.group("net").split("/")
                # net, hierarchy = net[-1], tuple(reversed(net[:-1]))
                # net_matched = self.compiled_reprogs["net"].match(net)
                # if net_matched is None:
                #     net = 0, (net, ) + hierarchy
                # else:
                #     net = int(net_matched.group("idx")), (net_matched.group("net"), ) + hierarchy
                yield matched.group("net"), matched.group("model"), float(matched.group("incr")), float(matched.group("path"))
