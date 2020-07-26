# Setting up a Raspberry Pi Zero WH for Probe Collection

 - Using Raspbian Stretch Lite image from 08.04.2019
 - Follow [https://github.com/seemoo-lab/nexmon](Nexmon) instructions for building the patches for bcm43430a1 on the RPI3/Zero W
 - Make driver for 4.19. kernel like [https://github.com/seemoo-lab/nexmon/issues/280#issuecomment-524568257](described here)

Setup Script
```
sudo apt update
sudo apt upgrade

sudo apt install raspberrypi-kernel-headers git libgmp3-dev gawk qpdf bison flex make automake autoreconf tcpdump libtool libtool-bin

# Kernel needs reboot to update
sudo reboot

sudo su
cd ~

git clone https://github.com/seemoo-lab/nexmon.git
cd nexmon

FILE=/usr/lib/arm-linux-gnueabihf/libisl.so.10
if [[ ! -f "$FILE" ]]; then
    cd ~/nexmon/buildtools/isl-0.10
    ./configure
    make && make install
    ln -s /usr/local/lib/libisl.so /usr/lib/arm-linux-gnueabihf/libisl.so.10
fi

FILE=/usr/lib/arm-linux-gnueabihf/libmpfr.so.4
if [[ ! -f "$FILE" ]]; then
    cd ~/nexmon/buildtools/mpfr-3.1.4
    autoreconf -f -i
    ./configure
    make && make install
    ln -s /usr/local/lib/libmpfr.so /usr/lib/arm-linux-gnueabihf/libmpfr.so.4
fi

cd ~/nexmon
source setup_env.sh
make

cd ~/nexmon/patches/bcm43430a1/7_45_41_46/nexmon/
make
make backup-firmware
make install-firmware

cd ~/nexmon/patches/bcm43455c0/7_45_189/nexmon/
mkdir log
make brcmfmac.ko
rmmod brcmfmac
insmod brcmfmac_4.19.y-nexmon/brcmfmac.ko

cp brcmfmac_4.19.y-nexmon/brcmfmac.ko ~/nexmon/patches/bcm43430a1/7_45_41_46/nexmon


cd ~/nexmon/utilities/nexutil/
make
make install

apt remove wpasupplicant

iw phy `iw dev wlan0 info | gawk '/wiphy/ {printf "phy" $2}'` interface add mon0 type monitor
ifconfig mon0 up

# get path of default driver
#modinfo brcmfmac
# ex: /lib/modules/4.19.66+/kernel/drivers/net/wireless/broadcom/brcm80211/brcmfmac/brcmfmac.ko

# backup original firmware
#mv "<orig_fw.ko>" "<orig_fw.ko.orig>"

# copy modified driver
#cp "<nexmon_fw.ko>" "<orig_fw.ko>"

# generate new dependency
#depmod -a

# reboot
```

Monitor mode works now on Pi Zero

# Collecting Probes

[https://github.com/klein0r/probemon](Probemon) from klein0r is used