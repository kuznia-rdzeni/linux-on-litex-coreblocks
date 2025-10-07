Linux on LiteX Coreblocks
==========================

Linux + buildroot + LiteX configurations for example SoC with Coreblocks running Linux.

Currently there is no virtual memory support and no supervisor mode in Coreblocks - this is no-MMU kernel variant, with kernel running in machine mode configuration.

Prerequisites
------------

Using Virtual Environment is recomended.

Coreblocks support is included now in upstream LiteX!

Get LiteX from [enjoy-digital/LiteX](https://github.com/enjoy-digital/litex).
Make sure to checkout the latest commit, and do the `full` config installation of LiteX to include Coreblocks support (or install [pythondata-cpu-coreblocks](https://github.com/litex-hub/pythondata-cpu-coreblocks) package).

Usual build stuff required for buildroot.

Build Linux with Buildroot
--------------------------

```bash
git clone https://gitlab.com/buildroot.org/buildroot.git --branch 2025.08.x --depth 1 build_buildroot

# Select and link device tree file (repeat this and next commands for rtl/sim change) 
# For FPGA target:
ln -sf src/litex_coreblocks.dts images/rv32_litex_coreblocks.dts
# For simulation target:
# ln -sf src/sim.dts images/rv32_litex_coreblocks.dts

cd build_buildroot
make BR2_EXTERNAL=../buildroot/ litex_coreblocks_defconfig
make -j $(nproc)
```

Build and load bitstream
------------------------

For `digilent_arty` board run:

```bash
./make.py --build --load --board digilent_arty
```

Booting
-------

After successful build with default configs, you will have Linux image, device tree blob built into kernel image, and rootfs generated in `images/`.

There are multiple methods of uploading the required images and loading them into main RAM.

### 1. Serial boot

It is slow. Recomended only for first attempts. You may want to increase the serial speed to `921600` baud in `soc.py`.

```bash
litex_term /dev/ttyUSBX --speed 115200 --images images/boot.json
```

### 2. SD card boot

Recomended option.

Flash your SD card with buildroot generated image.
```bash
dd if=images/sdcard.img of=/dev/sdX
```

Image contains one vfat partition with the kernel image, initrd file system, and boot.json - that is loaded from LiteX BIOS.

### 3. Network boot

Not tested yet.


### 4. Simulation

Very slow - change `images/rv32_litex_coreblocks.dts` link to `sim.dts` device tree, rebuild buildroot kernel and image.

Run `python sim.py`

make.py options
---------------

-----
| Option | Help |
|---|---|
| --board | select target board |
| --build | build bitstream |
| --load | load bitstream |
| --doc | generate SoC documentation | 

Customization tips
------------------

* Use buildroot/rootfsoverlay to add files.
* Look at buildroot `make menuconfig` and `ARCH=riscv make menuconfig` from linux downloaded by buildroot (`build_buildroot/output/build/linux-6.9/`).
* Some extra `packages/` included (manal build required).

Notes
-----

* This is still in Work in progress state, YMMV. Contributions welcome.
* Due to using only Linux core-local (RISC-V Hart-Local) interrupt controller, many drivers are broken - ex. serial driver fall-backs to polling. (Will fix)
* Arty A7 build tested with Vivado 2024.2 (there are workarounds for Vivado verisions >=2023.1 synthesis included in Coreblocks).

