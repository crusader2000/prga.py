import cocotb
from cocotb.triggers import Timer,RisingEdge,Edge,First,NextTimeStep
from cocotb.clock import Clock
import random
import math
from cocotb.result import TestFailure
from cocotb.binary import BinaryValue
from cocotb.scoreboard import Scoreboard

# cocotb coroutine for driving the clocks
def clock_generation(clk,clock_period=10,test_time=100000):
    c= Clock(clk,clock_period)
    cocotb.fork(c.start(test_time//clock_period))
    
@cocotb.test()
def test_flipflop(dut):
    """
    cocotb test for testing the primitive flipflop
    """

    # Initialize the clock
    clk = dut.clk
    clock_generation(clk)
    
    D = dut.D
    Q = dut.Q
    cfg_e = dut.cfg_e
    
    # Reset the Flipflop signals
    for _ in range(3):
        yield RisingEdge(clk)
        cfg_e <= 1

    D <= 0
    cfg_e <= 0
    yield RisingEdge(clk)

    #######################################################
    ## TESTING ############################################
    #######################################################

    # Testing the working of flipflop
    for i in range(100):
        prev_d = D.value.integer
        D <= random.choice([0,1])
        yield RisingEdge(clk)
        if not cfg_e.value.integer:       
            if Q.value.binstr != 'x' and Q.value.binstr != 'z':
                if Q.value.integer != prev_d:
                    raise TestFailure("Test Failed at "+str(i)+"iteration when D="+D.value.binstr+" and Q="+Q.value.binstr)
