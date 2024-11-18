import random

import cocotb
from cocotb.result import TestFailure
from cocotb.triggers import RisingEdge, Timer


async def genClockAndReset(dut):
    dut.reset.value = 1
    dut.clk.value   = 0
    await Timer(1, 'ns')

    dut.reset.value = 0
    await Timer(1, 'ns')
    while True:
        dut.clk.value = 1
        await Timer(0.5, 'ns')
        dut.clk.value = 0
        await Timer(0.5, 'ns')

@cocotb.test()
async def test1(dut):
    cocotb.start_soon(genClockAndReset(dut))

    counter = 0  # Used to model the hardware
    for i in range(256):
        await RisingEdge(dut.clk)
        if dut.io_value.value != counter:
            raise TestFailure("io_value mismatch")

        if dut.io_full.value != 1 if counter == 15 else 0:
            raise TestFailure("io_full mismatch")

        if dut.io_clear.value == 1:
            counter = 0
        else:
            counter = (counter + 1) & 0xf

        dut.io_clear.value = (random.random() < 0.03)


