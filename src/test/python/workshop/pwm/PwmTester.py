import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer


async def apb_write(dut, addr, data):
    """APB Write operation."""

    await RisingEdge(dut.clk)
    await Timer(1, units="ns")  # Wait 1ns for setup phase
    dut.io_apb_PADDR.value = addr
    dut.io_apb_PWDATA.value = data
    dut.io_apb_PSEL.value = 1   # Select the slave
    dut.io_apb_PENABLE.value = 1  # Access phase
    dut.io_apb_PWRITE.value = 1  # Write operation
    await Timer(10, units="ns")  # Wait 1ns for setup phase
    dut.io_apb_PSEL.value = 0  # De-select the slave
    dut.io_apb_PENABLE.value = 0
    dut.io_apb_PWRITE.value = 0
    await Timer(10, units="ns")  # Wait 1ns for access phase

async def apb_read(dut, addr):
    """APB Read operation."""
    await RisingEdge(dut.clk)
    await Timer(1, units="ns")  # Wait 1ns for setup phase

    dut.io_apb_PADDR.value = addr
    dut.io_apb_PWRITE.value = 0  # Read operation
    dut.io_apb_PSEL.value = 1   # Select the slave
    dut.io_apb_PENABLE.value = 1  # Access phase
    await Timer(10, units="ns")  # Wait 1ns for setup phase
    data = dut.io_apb_PRDATA.value  # Read data
    dut.io_apb_PSEL.value = 0  # De-select the slave
    dut.io_apb_PENABLE.value = 0
    await Timer(10, units="ns")  # Wait 1ns for access phase

    return data

@cocotb.test()
async def test_apbpwm(dut):
    """Test the APB PWM module."""
    # Generate clock
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())

    # Apply reset
    dut.reset.value = 1
    await Timer(20, units="ns")  # Reset active for 20ns
    dut.reset.value = 0

    # Initialize APB signals
    dut.io_apb_PSEL.value = 0
    dut.io_apb_PENABLE.value = 0
    dut.io_apb_PWRITE.value = 0
    dut.io_apb_PADDR.value = 0
    dut.io_apb_PWDATA.value = 0

    # Test 2: Write and read back duty cycle
    await apb_write(dut, addr=0x04, data=0x40)  # Set duty cycle to 0x40 (64)
    duty_cycle_val = await apb_read(dut, addr=0x04)
    assert duty_cycle_val == 0x40, f"Duty cycle readback failed, got {duty_cycle_val}"

    # Test 3: Write and read back timePeriod
    await apb_write(dut, addr=0x08, data=0x80)  # Set duty cycle to 0x80 (128)
    time_period_val = await apb_read(dut, addr=0x08)
    assert time_period_val == 0x80, f"timePeriod readback failed, got {time_period_val}"

    # Test 1: Write and read back logic_enable
    await apb_write(dut, addr=0x00, data=1)  # Enable the PWM
    enable_val = await apb_read(dut, addr=0x00)
    assert enable_val == 1, f"Enable readback failed, got {enable_val}"

    # Test 3: Check PWM output
    # Allow time for PWM to start toggling
    await Timer(1000, units="ns")
    for _ in range(100):  # Observe 100 clock cycles
        await RisingEdge(dut.clk)
        if dut.logic_timer.value == 0:
            assert dut.io_pwm.value == 1, "PWM output expected HIGH at start of cycle"
        elif dut.logic_timer.value == 64:
            assert dut.io_pwm.value == 0, "PWM output expected LOW after duty cycle"

    await apb_write(dut, addr=0x00, data=0)  # Enable the PWM
    await apb_write(dut, addr=0x08, data=0x40)  # Set duty cycle to 0x80 (128)
    await Timer(200, 'ns')
    await apb_write(dut, addr=0x00, data=1)  # Enable the PWM
    await Timer(1000, units="ns")
    for _ in range(100):  # Observe 100 clock cycles
        await RisingEdge(dut.clk)
        if dut.logic_timer.value == 0:
            assert dut.io_pwm.value == 1, "PWM output expected HIGH at start of cycle"
        elif dut.logic_timer.value == 64:
            assert dut.io_pwm.value == 0, "PWM output expected LOW after duty cycle"


    cocotb.log.info("All tests passed!")
