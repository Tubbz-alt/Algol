#!/usr/bin/env python
# Copyright (c) 2015 Angel Terrones (<angelterrones@gmail.com>)
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

from Core.core import Core
from Simulation.core.memory import Memory
from Core.wishbone import WishboneIntercon
from myhdl import instance
from myhdl import always
from myhdl import Signal
from myhdl import delay
from myhdl import modbv
from myhdl import Simulation
from myhdl import StopSimulation
from myhdl import traceSignals
from myhdl import now
from myhdl import Error
import sys

if sys.version_info[0] < 3:
    import ConfigParser as cp
else:
    import configparser as cp

# Constans for simulation.
TICK_PERIOD = 10
TIMEOUT     = 10000
RESET_TIME  = 5


def core_testbench(hex_file):
    """
    Connect the Core to the simulation memory, using wishbone interconnects.
    Assert the core for RESET_TIME.

    Finish the test after TIMEOUT units of time, or a write to toHost register.
    If toHost is different of 1, the test failed.
    """
    clk = Signal(True)
    rst = Signal(False)
    imem = WishboneIntercon()
    dmem = WishboneIntercon()

    toHost = Signal(modbv(0)[32:])

    config = cp.ConfigParser()
    config.read('Simulation/core/algol.ini')

    dut_core = Core(clk_i=clk,
                    rst_i=rst,
                    imem=imem,
                    dmem=dmem,
                    toHost=toHost,
                    IC_ENABLE=config.getboolean('ICache', 'Enable'),
                    IC_BLOCK_WIDTH=config.getint('ICache', 'BlockWidth'),
                    IC_SET_WIDTH=config.getint('ICache', 'SetWidth'),
                    IC_NUM_WAYS=config.getint('ICache', 'Ways'),
                    DC_ENABLE=config.getboolean('DCache', 'Enable'),
                    DC_BLOCK_WIDTH=config.getint('DCache', 'BlockWidth'),
                    DC_SET_WIDTH=config.getint('DCache', 'SetWidth'),
                    DC_NUM_WAYS=config.getint('DCache', 'Ways'))

    memory = Memory(clka_i=clk,
                    rsta_i=rst,
                    imem=imem,
                    clkb_i=clk,
                    rstb_i=rst,
                    dmem=dmem,
                    SIZE=int(config.get('Memory', 'Size'), 16),
                    HEX=hex_file,
                    BYTES_X_LINE=config.getint('Memory', 'Bytes_x_line'))

    @always(delay(int(TICK_PERIOD / 2)))
    def gen_clock():
        clk.next = not clk

    @always(toHost)
    def toHost_check():
        """
        Wait for a write to toHost register.
        """
        if toHost != 1:
            raise Error('Test failed. MTOHOST = {0}. Time = {1}'.format(toHost, now()))
        print("Time: {0}".format(now()))
        raise StopSimulation

    @instance
    def timeout():
        """
        Wait until timeout.
        """
        rst.next = True
        yield delay(RESET_TIME * TICK_PERIOD)
        rst.next = False
        yield delay(TIMEOUT * TICK_PERIOD)
        raise Error("Test failed: Timeout")

    return dut_core, memory, gen_clock, timeout, toHost_check


def test_core(hex_file, vcd):
    """
    Core: Behavioral test for the RISCV core.
    """
    if vcd:
        vcd = traceSignals(core_testbench, hex_file,)
        sim = Simulation(vcd)
    else:
        sim = Simulation(core_testbench(hex_file))

    sim.run()

# Local Variables:
# flycheck-flake8-maximum-line-length: 120
# flycheck-flake8rc: ".flake8rc"
# End:
