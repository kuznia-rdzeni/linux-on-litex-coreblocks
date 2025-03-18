#!/usr/bin/env python3

from litex.soc.integration.builder import Builder
from litex.tools.litex_json2dts_linux import generate_dts
import json

import os
import argparse

from soc import SoCDemo

class Board:
    def __init__(self, soc_cls):
        self.soc_cls = soc_cls
        self.soc_kwargs = {
                "with_ethernet": True,
                "l2_size": 1024,
                "integrated_rom_size": 0xC000,
                "with_led_chaser": False,
        }

    def load(self, soc, filename):
        prog = soc.platform.create_programmer()
        prog.load_bitstream(filename)

    def flash(self, soc, filename):
        prog = soc.platform.create_programmer()
        prog.flash(0, filename)

    def setup_soc(self, soc):
        soc.add_switches()
        soc.add_leds()

class TerasicDe2115Board(Board):
    board_name = "terasic_de2_115"

    def __init__(self):
        from litex_boards.targets import terasic_de2_115
        super().__init__(soc_cls=terasic_de2_115.BaseSoC)

        self.soc_kwargs.update(**{
            "sys_clk_freq": 50e6,
            "with_ethernet": False,
            "with_sdcard": True,
        })


class ArtyA7Board(Board):
    board_name = "digilent_arty"

    def __init__(self):
        from litex_boards.targets import digilent_arty
        super().__init__(soc_cls=digilent_arty.BaseSoC)

        self.soc_kwargs.update(**{
            "sys_clk_freq": 30e6,
            "l2_size": 512,
            "toolchain": "openxc7",
        })

    def setup_soc(self, soc):
        from litex_boards.platforms import digilent_arty
        super().setup_soc(soc)
        soc.platform.add_extension(digilent_arty._sdcard_pmod_io)
        soc.add_sdcard()


supported_boards = [TerasicDe2115Board, ArtyA7Board]

def main():
    description = "Demo Coreblocks SoC"
    parser = argparse.ArgumentParser(description=description, formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument("--build",          action="store_true",         help="Build bitstream.")
    parser.add_argument("--load",           action="store_true",         help="Load bitstream (to SRAM).")
    parser.add_argument("--flash",          action="store_true",         help="Flash bitstream/images (to Flash).")
    parser.add_argument("--doc",            action="store_true",         help="Build documentation.")
    parser.add_argument("--board",          action="store",              help="Select board target.", default="digilent_arty")

    args = parser.parse_args()

    # Select board -----------------------------------------------------------------------------
    board = None
    board_name = args.board
    for b in supported_boards:
        if args.board == b.board_name:
            board = b()

    if not board:
        raise ValueError(f"Unsupported board '{board_name}'. Expected one of {set([b.board_name for b in supported_boards])}")

    # Create SoC -------------------------------------------------------------------------------
    soc = SoCDemo(board.soc_cls, **board.soc_kwargs)
    board.setup_soc(soc)

    build_dir = os.path.join("build", board_name)
    builder   = Builder(soc,
        output_dir   = os.path.join("build", board_name),
        bios_console = "lite",
        csr_json     = os.path.join(build_dir, "csr.json"),
        csr_csv      = os.path.join(build_dir, "csr.csv")
    )
    # Build FPGA bitstream ---------------------------------------------------------------------
    if args.build:
        builder.build(run=args.build, build_name=board_name)

    # Load FPGA bitstream ----------------------------------------------------------------------
    if args.load:
        board.load(soc, builder.get_bitstream_filename(mode="sram"))

    # Flash bitstream/images (to SPI Flash) ----------------------------------------------------
    if args.flash:
        board.flash(soc, builder.get_bitstream_filename(mode="flash"))

    # Generate SoC documentation ---------------------------------------------------------------
    if args.doc:
        soc.generate_doc(board_name)

        json_src = os.path.join("build", board_name, "csr.json")
        dts = os.path.join("build", board_name, "{}.dts".format(board_name))

        with open(json_src) as json_file, open(dts, "w") as dts_file:
            dts_content = generate_dts(json.load(json_file), polling=False)
            dts_file.write(dts_content)

if __name__ == "__main__":
    main()
