package workshop.pwm

import org.scalatest.funsuite.AnyFunSuite
import spinal.core._
import spinal.lib._

// APB configuration class (generic/parameter)
case class ApbConfig(addressWidth : Int,
                     dataWidth    : Int,
                     selWidth     : Int)

// APB interface definition
case class Apb(config: ApbConfig) extends Bundle with IMasterSlave {

  val PSEL = Bits(config.selWidth bits)
  val PENABLE = Bool()
  val PADDR = UInt(config.addressWidth bits)
  val PWRITE = Bool()
  val PWDATA = Bits(config.dataWidth bits)
  val PRDATA = Bits(config.dataWidth bits)
  val PREADY = Bool()

  override def asMaster(): Unit = {

    out(PADDR, PSEL, PENABLE, PWRITE, PWDATA)
    in(PREADY, PRDATA)
  }
}

case class ApbPwm(apbConfig: ApbConfig,timerWidth : Int) extends Component {
  require(apbConfig.dataWidth == 32)
  require(apbConfig.selWidth == 1)

  val io = new Bundle{
    val apb = slave(Apb(apbConfig))
    val pwm = out Bool()
  }

  val logic = new Area {

    val enable = Reg(Bool()) init False
    val timer = Reg(UInt(timerWidth bits)) init 0
    val dutyCycle = Reg(UInt(timerWidth bits)) init 0
    val output = Reg(Bool()) init False
    val timePeriod = Reg(UInt(timerWidth bits)) init 0
    val firstEnableCycle = Reg(Bool()) init True

    when(enable) {
      // If timePeriod or dutyCycle is zero, or if dutyCycle > timePeriod, force the output low
      when(timePeriod === 0 || dutyCycle === 0 || dutyCycle > timePeriod) {
        output := False
        timer := 0
      } otherwise {
        // Handle the first enable cycle
        when(firstEnableCycle) {
          output := True
          timer := 0
          firstEnableCycle := False
        } otherwise {
          // Special case: dutyCycle == timePeriod (100% duty cycle)
          when(dutyCycle === timePeriod) {
            when(timer === timePeriod - 1) {
              timer := 0 // Wrap the timer
            } otherwise {
              timer := timer + 1
            }
            output := True // Always high
          } otherwise {
            // Normal operation
            when(timer === dutyCycle - 1) {
              timer := timer + 1
              output := False
            }
            when(timer === timePeriod - 1) {
              timer := 0 // Wrap the timer
              output := True
            } otherwise {
              timer := timer + 1
            }
          }
        }
      }
    } otherwise {
      output := False
      timer := 0
      firstEnableCycle := True
    }

    io.pwm := output
  }
  
  val control = new Area {

    val doWrite = io.apb.PSEL(0) && io.apb.PENABLE && io.apb.PWRITE
    val doRead = io.apb.PSEL(0) && io.apb.PENABLE && !io.apb.PWRITE
    io.apb.PRDATA := 0
    io.apb.PREADY := True
    switch(io.apb.PADDR) {
      is(0) {
        when(doRead) {
          io.apb.PRDATA(0) := logic.enable
        }
        when(doWrite) {
          logic.enable := io.apb.PWDATA(0)
        }
      }
      is(4) {
        when(doRead) {
          io.apb.PRDATA := logic.dutyCycle.asBits.resized
        }
        when(doWrite) {
          logic.dutyCycle := io.apb.PWDATA.asUInt.resized
        }
      }
      is(8) {
        when(doRead) {
          io.apb.PRDATA := logic.timePeriod.asBits.resized
        }
        when(doWrite) {
          logic.timePeriod := io.apb.PWDATA.asUInt.resized
        }
      }
    }
  }
}