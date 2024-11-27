import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer
import random

# UART Configuration
BAUD_RATE = 115200
BIT_PERIOD = int(1e9 / BAUD_RATE)  # Bit period in nanoseconds
SAMPLING_SIZE = 8                 # Number of samples per bit for majority vote

async def send_uart_bit_with_samples(dut, bit_value, noise_sample=None):
    """
    Send a single UART bit with a series of samples, optionally introducing noise in one sample.
    """
    sample_period = BIT_PERIOD // SAMPLING_SIZE

    for sample_index in range(SAMPLING_SIZE):
        if noise_sample is not None and sample_index == noise_sample:
            # Inject noise into this sample
            print(f'noise inject at sample {sample_index}')
            dut.io_rxd.value = (~bit_value) & 1
        else:
            dut.io_rxd.value = bit_value

        # Toggle io_samplingTick to simulate sampling at each sample time
        await Timer(sample_period, units='ns')
        await RisingEdge(dut.clk)
        dut.io_samplingTick.value = 1
        await RisingEdge(dut.clk)
        dut.io_samplingTick.value = 0
        cocotb.log.info(f'sample of {sample_index} sent')

async def send_uart_frame_with_sample_noise(dut, data, baud_rate=BAUD_RATE, noisy_bit=None, noisy_sample=None):
    """
    Send a UART frame (8-N-1: 8 data bits, no parity, 1 stop bit) with noise introduced at the sample level.
    """
    bit_period = int(1e9 / baud_rate)

    # Start bit (low)
    await send_uart_bit_with_samples(dut, bit_value=0, noise_sample=noisy_sample if noisy_bit == 0 else None)
    cocotb.log.info(f'start bit sent')

    # Data bits (LSB first)
    for bit_index in range(8):
        bit_value = (data >> bit_index) & 1
        noise_sample = noisy_sample if noisy_bit == bit_index + 1 else None
        await send_uart_bit_with_samples(dut, bit_value=bit_value, noise_sample=noise_sample)
        cocotb.log.info(f'data bit {bit_index} sent')

    # Stop bit (high)
    await send_uart_bit_with_samples(dut, bit_value=1, noise_sample=noisy_sample if noisy_bit == 9 else None)
    cocotb.log.info('stop bit sent')

@cocotb.test()
async def uart_rx_test_with_sample_noise(dut):
    """
    Test the UART receiver with noise introduced at the sample level in one bit.
    """
    # Generate a clock
    clock = Clock(dut.clk, 10, units="ns")  # 10ns period = 100 MHz
    cocotb.start_soon(clock.start())

    # Reset the DUT
    dut.reset.value = 1
    dut.io_samplingTick.value = 0
    dut.io_rxd.value = 1  # Idle state
    await Timer(100, units="ns")
    dut.reset.value = 0

    # Test data and noise configuration
    test_data = 0x55  # Example data: 0b01011010
    noisy_bit = random.randint(1, 8)      # Introduce noise in a random data bit (1-8)
    noisy_sample = random.randint(0, SAMPLING_SIZE - 1)  # Introduce noise in a random sample within that bit

    # Log the noise injection point
    cocotb.log.info(f"Injecting noise in bit {noisy_bit} at sample {noisy_sample}")

    # Send the UART frame with sample-level noise
    await send_uart_frame_with_sample_noise(dut, test_data, noisy_bit=noisy_bit, noisy_sample=noisy_sample)

    # Wait for the DUT to process the frame
    await RisingEdge(dut.io_read_valid)

    # Check results
    received_data = int(dut.io_read_payload.value)
    assert received_data == test_data, f"Expected {test_data}, but got {received_data}"
    cocotb.log.info(f"Test passed! Received data: {hex(received_data)}")

    await Timer(100, 'us')
