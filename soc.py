from litex.soc.interconnect.csr import *
from litex.soc.cores.gpio import GPIOOut, GPIOIn

import os

def SoCDemo(soc_cls, **kwargs):
    class _SoCDemo(soc_cls):
        csr_map = {**soc_cls.csr_map, **{
            "ctrl":       0,  # addr: 0xe0000000
            "ethmac":     1,  # addr: 0xe0000800
            "ethphy":     2,  # addr: 0xe0001000
            "sdram":      11, # addr: 0xe0005800
            #"switches":   12, # addr: 0xe0006000
            #"timer0":     13, # addr: 0xe0006800
            "uart":       14, # addr: 0xe0007000
            "uart1":       15, # addr: 0xe0007800
        }}

        interrupt_map = {**soc_cls.interrupt_map, **{
            "uart":       0,
            "timer0":     1,
            "ethmac":     3,
            #"switches":   4,
            "uart1":      5,
        }}

        mem_map_linux = {
            "rom":          0x00000000,
            "sram":         0x01000000,
            "main_ram":     0x80000000,
            "csr":          0xe0000000,
            "ethmac":       0xe8000000,
        }

        def __init__(self, **kwargs):
            soc_cls.mem_map.update(self.mem_map_linux)
            soc_cls.__init__(self,
                             cpu_type="coreblocks",
                             cpu_variant="small_linux",

                             **kwargs,
            )
            soc_cls.mem_map.update(self.mem_map_linux)

        def add_switches(self):
            #switches = self.platform.request_all("user_sw")
            #self.switches = GPIOIn(switches, with_irq=True)
            # IRQ registered in interrupt_map
            self.add_uart("uart1", "serial", baudrate=921600)
            

        def add_leds(self):
            #self.leds = GPIOOut(Cat(self.platform.request_all("user_led")))
            pass

        # Documentation generation -----------------------------------------------------------------
        def generate_doc(self, board_name):
            from litex.soc.doc import generate_docs
            doc_dir = os.path.join("build", board_name, "doc")
            generate_docs(self, doc_dir)
            print("generate docs")
            print("sphinx-build -M html {}/ {}/_build".format(doc_dir, doc_dir))
            os.system("sphinx-build -M html {}/ {}/_build".format(doc_dir, doc_dir))

    return _SoCDemo(**kwargs)
