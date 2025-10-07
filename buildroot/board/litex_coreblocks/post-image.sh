#!/bin/bash

set -e

BOARD_DIR="$(dirname $0)"
GENIMAGE_CFG="${BOARD_DIR}/genimage.cfg"
GENIMAGE_TMP="${BUILD_DIR}/genimage.tmp"

LINUX_ON_COREBLOCKS_OUT_DIR=$BR2_EXTERNAL_LITEX_COREBLOCKS_PATH/../images
DST_DTB=$LINUX_ON_COREBLOCKS_OUT_DIR/rv32_litex_coreblocks.dtb
DST_DTS=$LINUX_ON_COREBLOCKS_OUT_DIR/rv32_litex_coreblocks.dts
DST_DTS_TMP=$LINUX_ON_COREBLOCKS_OUT_DIR/rv32_litex_coreblocks.dts.tmp
#DST_OPENSBI=$LINUX_ON_COREBLOCKS_OUT_DIR/opensbi.bin
DST_IMAGE=$LINUX_ON_COREBLOCKS_OUT_DIR/Image
DST_ROOTFS=$LINUX_ON_COREBLOCKS_OUT_DIR/rootfs.cpio.gz

rm -f $DST_OPENSBI $DST_ROOTFS $DST_IMAGE
#ln -s $BINARIES_DIR/fw_jump.bin $DST_OPENSBI
ln -s $BINARIES_DIR/Image $DST_IMAGE
SRC_ROOTFS=$BINARIES_DIR/rootfs.cpio.gz
ln -s  $SRC_ROOTFS $DST_ROOTFS

INITRD_START="0x81000000"
INITRD_END=$( printf "0x%x" $(($INITRD_START + $(ls -l $SRC_ROOTFS | awk '{print $5}') )) )
echo "INITRD_START=$INITRD_START INITRD_END=$INITRD_END"

if [ ! -e $DST_DTS ]; then
	echo ""
	echo "Warning: missing file $DST_DTS"
	echo "a dummy .dtb file will be created"
	echo ""
	touch $DST_DTB
else
    cp $DST_DTS $DST_DTS_TMP
    sed -r -i "s/(initrd-start.*=.*<)(.*)(>)/\1$INITRD_START\3/g" $DST_DTS_TMP
    sed -r -i "s/(initrd-end.*=.*<)(.*)(>)/\1$INITRD_END\3/g" $DST_DTS_TMP
    dtc -O dtb -o $DST_DTB $DST_DTS_TMP
fi

# Pass an empty rootpath. genimage makes a full copy of the given rootpath to
# ${GENIMAGE_TMP}/root so passing TARGET_DIR would be a waste of time and disk
# space. We don't rely on genimage to build the rootfs image, just to insert a
# pre-built one in the disk image.

trap 'rm -rf "${ROOTPATH_TMP}"' EXIT
ROOTPATH_TMP="$(mktemp -d)"
rm -rf "${GENIMAGE_TMP}"

genimage \
    --rootpath "${ROOTPATH_TMP}"   \
    --tmppath "${GENIMAGE_TMP}"    \
    --inputpath "${LINUX_ON_COREBLOCKS_OUT_DIR}"  \
    --outputpath "${LINUX_ON_COREBLOCKS_OUT_DIR}" \
    --config "${GENIMAGE_CFG}"

exit $?

