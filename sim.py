#!/usr/bin/env python3

import json
import argparse

from migen import *

from litex.gen import *

from litex.build.generic_platform import *
from litex.build.sim              import SimPlatform
from litex.build.sim.config       import SimConfig
from litex.build.sim.verilator    import verilator_build_args, verilator_build_argdict

from litex.soc.interconnect.csr       import *
from litex.soc.integration.soc_core   import *
from litex.soc.integration.builder    import *

from litedram import modules as litedram_modules
from litedram.phy.model       import SDRAMPHYModel, sdram_module_nphases, get_sdram_phy_settings

from litex.tools.litex_json2dts_linux import generate_dts

# IOs ----------------------------------------------------------------------------------------------

_io = [
    # Clk / Rst.
    ("sys_clk", 0, Pins(1)),
    ("sys_rst", 0, Pins(1)),

    # Serial.
    ("serial", 0,
        Subsignal("source_valid", Pins(1)),
        Subsignal("source_ready", Pins(1)),
        Subsignal("source_data",  Pins(8)),

        Subsignal("sink_valid", Pins(1)),
        Subsignal("sink_ready", Pins(1)),
        Subsignal("sink_data",  Pins(8)),
    ),
]

# Platform -----------------------------------------------------------------------------------------

class Platform(SimPlatform):
    def __init__(self):
        SimPlatform.__init__(self, "SIM", _io)

# Supervisor ---------------------------------------------------------------------------------------

class Supervisor(LiteXModule):
    def __init__(self):
        self._finish = CSR()    # Controlled from CPU.
        self.finish  = Signal() # Controlled from logic.
        self.sync += If(self._finish.re | self.finish, Finish())

# SoCLinux -----------------------------------------------------------------------------------------

class SoCLinux(SoCCore):
    sim_mem_map = {
        "main_ram":     0x80000000,
        "csr":          0xe8000000,
    }

    csr_map = {
        "uart": 14,
    }

    def __init__(self, sys_clk_freq=int(100e6),
        init_memories    = True
    ):
        # Platform ---------------------------------------------------------------------------------
        platform     = Platform()
        out_countr = Signal(64)

        # CRG --------------------------------------------------------------------------------------
        self.crg = CRG(platform.request("sys_clk"))

        # SoCCore ----------------------------------------------------------------------------------
        self.mem_map.update(self.sim_mem_map)
        SoCCore.__init__(self, platform, clk_freq=sys_clk_freq,
            cpu_type            = "coreblocks",
            cpu_variant         = "small_linux",
            integrated_rom_size = 0x10000,
            uart_name           = "sim",
        )
        self.add_config("DISABLE_DELAYS")


        serial = platform.lookup_request("serial")

        # Trace Trigger -----------------------------------------------------------------------------
        # Use global --trace option to enable traces (dump in build/sim/gateware/)

        # # Trigger recording on UART Liftoff
        # # self.sync += If(serial.source_valid, out_countr.eq(out_countr+1))
        # # self.comb += platform.trace.eq(out_countr >= 1051)

        # # Trigger recording in cycle window after 'f!' char sequence (Liftoff!)
        trace_start = Signal()
        prev_char = Signal(8)
        self.sync += If(serial.source_valid, prev_char.eq(serial.source_data))
        self.sync += If(trace_start, out_countr.eq(out_countr+1))
        self.sync += If(serial.source_valid & (serial.source_data == ord('!')) & (prev_char == ord('f')), trace_start.eq(1))
        self.comb += platform.trace.eq(trace_start & (out_countr < 500000))

        # self.comb += platform.trace.eq(1)

        # Memory boot ------------------------------------------------------------------------------

        # Fixed for no-mmu configs. Linux `Image` must be loaded at this address in boot.json
        # DTB must be built into kernel, because boot.json 'bootargs' setup to set 'r2' (with dtb pointer)
        # before switch to Linux image from BIOS is not supported.
        boot_addr = 0x8000_0000
        # Macro for LiteX BIOS to define fallback boot address (always used here).
        # Disabling serial boot manually in sources is recommended to not wait for timeout.
        self.add_constant("ROM_BOOT_ADDRESS", boot_addr)

        # Supervisor -------------------------------------------------------------------------------
        self.supervisor = Supervisor()

        # SDRAM ------------------------------------------------------------------------------------
        ram_init = []
        if init_memories:
            ram_init = get_mem_data("images/boot.json", endianness="little", offset=boot_addr)

        sdram_module = "MT48LC16M16"
        sdram_clk_freq   = int(100e6)
        sdram_module_cls = getattr(litedram_modules, sdram_module)
        sdram_rate       = "1:{}".format(sdram_module_nphases[sdram_module_cls.memtype])
        sdram_module     = sdram_module_cls(sdram_clk_freq, sdram_rate)
        phy_settings     = get_sdram_phy_settings(
            memtype    = sdram_module.memtype,
            data_width = 32,
            clk_freq   = sdram_clk_freq,
        )
        self.sdrphy = SDRAMPHYModel(
            module    = sdram_module,
            settings  = phy_settings,
            clk_freq  = sdram_clk_freq,
            init      = ram_init,
        )
        self.add_sdram("sdram",
            phy           = self.sdrphy,
            module        = sdram_module,
            l2_cache_size = 0,
        )

        self.add_constant("SDRAM_TEST_DISABLE") # Skip SDRAM test to avoid corrupting pre-initialized contents.

    def _generate_dts(self, board_name):
        json_src = os.path.join("build", board_name, "csr.json")
        dts = os.path.join("build", board_name, "{}.dts".format(board_name))
        with open(json_src) as json_file, open(dts, "w") as dts_file:
            dts_content = generate_dts(json.load(json_file))
            dts_file.write(dts_content)

# Build --------------------------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Linux on LiteX Coreblocks Simulation.")
    verilator_build_args(parser)
    args = parser.parse_args()

    verilator_build_kwargs = verilator_build_argdict(args)
    sim_config = SimConfig(default_clk="sys_clk")
    sim_config.add_module("serial2console", "serial")

    soc = SoCLinux()
    board_name = "sim"
    build_dir  = os.path.join("build", board_name)
    builder = Builder(soc, output_dir=build_dir, csr_json=os.path.join(build_dir, "csr.json"))
    builder.build(sim_config=sim_config, **verilator_build_kwargs)

if __name__ == "__main__":
    main()
