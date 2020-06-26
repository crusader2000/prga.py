# -*- encoding: ascii -*-
# Python 2 and 3 compatible
from __future__ import division, absolute_import, print_function
from prga.compatible import *

from .base import AbstractPass
from ..core.common import ModuleView
from ..util import Object, uno
from ..exception import PRGAInternalError

import os

__all__ = ['Tester']

# ----------------------------------------------------------------------------
# -- Tester Pass ------------------------------------------------------
# ----------------------------------------------------------------------------
class Tester(Object, AbstractPass):
    """Collecting Verilog rendering tasks.
    
    Args:
        renderer (`FileRenderer`): File generation tasks are added to the specified renderer
        src_output_dir (:obj:`str`): Verilog source files are generated in the specified directory. Default value is
            the current working directory.
        header_output_dir (:obj:`str`): Verilog header files are generated in the specified directory. Default value
            is "{src_output_dir}/include"
        view (`ModuleView`): Generate Verilog source files with the specified view. Currently No use in tester pass
    """

    __slots__ = ['renderer', 'src_output_dir', 'header_output_dir', 'view', 'visited']
    def __init__(self, renderer, rtl_dir, src_output_dir = ".", header_output_dir = None, view = ModuleView.logical):
        self.renderer = renderer
        self.src_output_dir = src_output_dir
        self.rtl_dir = rtl_dir
        self.header_output_dir = os.path.abspath(uno(header_output_dir, os.path.join(src_output_dir, "include")))
        self.view = view
        self.visited = {}

    def _process_module(self, module):
        if module.key in self.visited:
            return
        # f = os.path.join(os.path.abspath(self.src_output_dir), "test_" + module.name + ".v")
        self.visited[module.key] = f

        if not hasattr(module, "rtl_dir"):
            module["rtl_dir"] = self.rtl_dir
        
        if module.module_class == 0 :
            # This if condition checks if the module is a primitive
            self.renderer.add_makefile(module, f, getattr(module, "test_makefile_template", "test_base.tmpl"))
            self.renderer.add_python_test(module, f, getattr(module, "test_python_template", "test_base.tmpl.py"))
       
        for instance in itervalues(module.instances):
            self._process_module(instance.model)

    @property
    def key(self):
        return "rtl.verilog"

    @property
    def dependences(self):
        if self.view.is_logical:
            return ("translation", )
        else:
            return ("translation", "materialization")

    @property
    def is_readonly_pass(self):
        return True

    def run(self, context):
        top = context.system_top
        if top is None:
            raise PRGAInternalError("System top module is not set")
        if not hasattr(context.summary, "rtl"):
            context.summary.rtl = {}
        self.visited = context.summary.rtl["sources"] = {}
        context.summary.rtl["includes"] = [self.header_output_dir]
        self._process_module(top)
