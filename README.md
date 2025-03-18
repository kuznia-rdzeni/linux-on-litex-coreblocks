Linux on LiteX Coreblocks
==========================

## WARNING: This is still in a very work in progress (and dirty) state. Expect dragons! (Contributions welcome)

Linux + buildroot + LiteX configurations for example SoC with Coreblocks running Linux.

Currently there is no virtual memory support and no supervisor mode in Coreblocks, so this is NO-MMU, with kernel in machine mode Linux configuration.

Prerequisites
------------

Using Virtual Environment is recomended.

Install patched LiteX with Coreblocks support from [kuznia-rdzeni/litex_](https://github.com/kuznia-rdzeni/litex_) repository.

Install python package with Coreblocks sources for LiteX from [kuznia-rdzeni/pythondata-cpu-coreblocks](https://github.com/kuznia-rdzeni/pythondata-cpu-coreblocks) repository.

Usual build stuff required for buildroot.

### LiteX patches:

(Temporary). Changes that not yet merged to Coreblocks `master` are required to run Linux. 
You need include them by:
* mannually enter `pythondata-cpu-coreblocks/sources/coreblocks/`
* add `https://github.com/piotro888/coreblocks.git` remote
* checkout `piotro/fosdem-2025` :) branch from remote above
* pip install `pythondata-cpu-coreblocks` again

Add patches for LiteX to match new Coreblocks version:
* checkout `piotro/fosdem-2025` inside `litex/litex`. (from original remote)

Build Linux with Buildroot
--------------------------

```bash
cd .. # (In separate directory)
git clone http://github.com/buildroot/buildroot
cd buildroot
make BR2_EXTERNAL=linux-on-litex-coreblocks/buildroot/ litex_coreblocks_defconfig
make -j 6
```

Build and load bitstream
------------------------

```bash
./make.py --build --load
```

Booting
-------

After successful build with default configs, you will have Linux image, device tree blob and rootfs generated in `images/`. (initramfs is embedded into kernel image).

There are multiple methods of uploading the required images and loading them into main RAM.

### 1. Serial boot

It is slow. Recomended only for first attempts.

```bash
litex_term /dev/ttyUSBX --speed 921600 --images images/boot.json
```

### 2. SD card boot
,
Recomended option.

Flash your SD card with dd with `images/sdcard.img` image.
Image contains one vfat partition with all required images + boot.json.

### 3. Network boot

Not tested yet.

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

(TODO)

* Use buildroot/rootfsoverlay to add files.
* Nice `packages/` included (manal build required).
* Look at buildroot menuconfig and menuconfig from linux downloaded by buildroot (`output/build/`).

Notes
-----

* There is a bug in Vivado synthesis step. Bitstreams targeting Xilinx devices will probably fail to work on FPGA. Needs further investigation. `standard` coreblocks configuration with icache additonally disabled may work.
* Due to using only Linux core-local (RISC-V Hart-Local) interrupt controller, many drivers are broken - ex. serial driver fall-backs to polling. (Will fix)
