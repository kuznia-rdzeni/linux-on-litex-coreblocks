Linux on LiteX Coreblocks
==========================

Linux + buildroot + LiteX configurations for example SoC with Coreblocks running Linux.

A full, virtualised linux is supported; with Litex loader and OpenSBI M-mode interface.

Prerequisites
------------

Using Virtual Environment is recomended.

Coreblocks support is included now in upstream LiteX!

Get LiteX from [enjoy-digital/LiteX](https://github.com/enjoy-digital/litex).
Make sure to checkout the latest commit, and do the `full` config installation of LiteX to include Coreblocks support (or install [pythondata-cpu-coreblocks](https://github.com/litex-hub/pythondata-cpu-coreblocks) package).

Usual build stuff required for buildroot.

### Note

There is an (highly) expermiental Nix enviroment project [kuznia-nix-env](https://codeberg.org/ariac/kuznia-nix-env), that will setup everything for you, automates builds and flashes, is easy to integrate with local coreblocks changes, and provides (mostly) reproducible environment. But you need to be *ready* to see it, I warned you.

Build Linux with Buildroot
--------------------------

```bash
git clone https://gitlab.com/buildroot.org/buildroot.git --branch 2025.08.x --depth 1 build_buildroot

# Select and link device tree file (repeat this and next commands for rtl/sim change) 
# For FPGA target:
ln -sf src/litex_coreblocks.dts images/rv32_litex_coreblocks.dts
# For simulation target:
# ln -sf src/sim.dts images/rv32_litex_coreblocks.dts

# Prebuild device tree for the OpenSBI
dtc -O dtb images/rv32_litex_coreblocks.dts -o images/rv32_litex_coreblocks.dtb

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

It is slow. Recomended only for first attempts. `921600` baud in recomended.

```bash
litex_term /dev/ttyUSBX --speed 921600 --images images/boot.json
```

### 2. SD card boot

Recomended option.

Flash your SD card with buildroot generated image.
```bash
dd if=images/sdcard.img of=/dev/sdX
```

Image contains one vfat partition with the kernel image, initrd file system, and boot.json - that is loaded from LiteX BIOS.

### 3. Network boot

Use `with_ethernet` (incompatibile with `with_etherbone`), serve `images/` via TFTP to pre-assigned IP addresses.


### 4. Simulation

**FIXME - it's probably broken now**

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
* Vivado >=2023.1 synthesis, recommended.
* Buildroot doesn't handle dependecy and config changes tracking well enough in some cases, `make opensbi-dirclean` (like after dts change), `make linux-dirclean` and `make clean` in last resort, are your friends. 

