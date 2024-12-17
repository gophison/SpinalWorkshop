import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, FallingEdge, Timer, ClockCycles


@cocotb.test()
async def test_memory_summing(dut):
    """Test the MemorySumming module."""

    # Generate clocks for io_wr_clk and io_sum_clk
    cocotb.start_soon(Clock(dut.io_wr_clk, 10, units="ns").start())
    cocotb.start_soon(Clock(dut.io_sum_clk, 20, units="ns").start())

    # Reset the DUT
    dut.io_sum_reset.value = 1
    await Timer(50, units="ns")  # Wait for some time
    dut.io_sum_reset.value = 0

    # Initialize input signals
    dut.io_wr_en.value = 0
    dut.io_wr_addr.value = 0
    dut.io_wr_data.value = 0
    dut.io_sum_start.value = 0

    # Write data into the memory
    data_to_write = [i for i in range(256)]  # Example data: 0 to 255
    await FallingEdge(dut.io_wr_clk)
    for addr, data in enumerate(data_to_write):
        dut.io_wr_en.value = 1
        dut.io_wr_addr.value = addr
        dut.io_wr_data.value = data
        await RisingEdge(dut.io_wr_clk)

    # Disable write enable after writing data
    dut.io_wr_en.value = 0

    # Start summing operation
    dut.io_sum_start.value = 1
    await RisingEdge(dut.io_sum_clk)
    dut.io_sum_start.value = 0

    # Wait for summing operation to complete
    while dut.io_sum_done.value == 0:
        await RisingEdge(dut.io_sum_clk)


    # Verify the result
    expected_sum = sum(data_to_write)
    actual_sum = dut.io_sum_value.value.integer

    assert actual_sum == expected_sum, f"Summing failed: expected {expected_sum}, got {actual_sum}"

    cocotb.log.info(f"Test passed: Summed value is {actual_sum}")
    await ClockCycles(dut.io_sum_clk, 10)
