---
title: Raspberry Pi Setup
author: Najam Syed
type: post
date: 2021-06-02T11:27:54-04:00
url: /2021/06/02/raspberry-pi-setup
draft: true
---

* [Introduction](#introduction)
* [Instructions](#instructions)
  - [Install Raspberry Pi OS on SD card](#install-os)
  - [Enable SSH for first boot](#enable-ssh)
  - [Set up static IP address](#static-ip)
  - [Configure host ethernet connection profile](#connection-profile)
  - [Connect the Raspberry Pi](#connect-pi)
* [References](#references)

<span id="introduction" />
# Introduction

As I write this post, I'm sitting in a hotel room with my laptop and a
Raspberry Pi, which I brought along because I'm traveling for several weeks
and I wanted some tech to play around with in my downtime. Go figure. The point
is that I'm on hotel WiFi with captive portal authentication, no access to the
router or router administration, and no router of my own. Nor do I have a
standalone keyboard or HDMI cable. I only had the space and foresight to bring
an ethernet cable.

{{< figure
  src="/img/rpi_hotel.jpg" alt="The view from my hotel room"
  caption="The view from my hotel room"
>}}

To simplify things, I also wanted my Raspberry Pi to have internet access
for downloading packages and updates without trying to figure out captive
portal authentication on the Pi without any keyboard/mouse input or video/HDMI
output.

Thus, this post was born out of necessity. In it, we'll learn how to:

- set up a Raspberry Pi via SSH with only a PC and ethernet cable
- share the PC's WiFi internet connection with the Raspberry Pi

#### What you **will** need:

- a laptop/desktop host PC with Ubuntu 18.04 (other versions of Ubuntu may
  also work, and the instructions can probably be adapted to other flavors of
  Linux as well)
- a Raspberry Pi (I'm using a 3B, but this should also work on other models)
- a power supply for the Raspberry Pi (I'm using [this 5V/3A PSU][1] from
  MakerSpot that I bought for $11 on Amazon)
- an ethernet cable
- an SD card and SD card reader/writer
- [*optional: an internet connection on the host PC*]

#### What you **will not** need:

- a monitor or video output (for the Raspberry Pi)
- an HDMI cable
- a mouse/keyboard (for the Raspberry Pi)

<span id="instructions" />
# Instructions

<span id="install-os" />
## Install Raspberry Pi OS on SD card

The first step is to install [Raspberry Pi OS][2] on an SD card. There are
[several ways][3] to do this. Currently, the easiest is to use Raspberry Pi
Imager, but at this point in time, the version in the Ubuntu 18.04 APT repository
doesn't work (see [this Github issue][4]). You can either build it yourself or
install the version from the Snap store:

{{< highlight plain >}}
snap install rpi-imager
{{< / highlight >}}

After installing Pi OS on your SD card, the SD card should have two partitions,
`boot` and `rootfs`. Mount both of these.

<span id="enable-ssh" />
## Enable SSH for first boot

Navigate to the SD card's `boot` partition and create a file named `ssh`
(replacing `/media/sd` with your mount point):

{{< highlight plain >}}
cd /media/sd/boot
touch ssh
{{< / highlight >}}

This will enable SSH access on boot, which is disabled by default. It's only
temporary, though&mdash;the file is removed after boot and you'll lose SSH
access again if the Pi is restarted (we'll address this in a later step by
starting the `ssh` service on the Pi).

<span id="static-ip" />
## Set up static IP address

Navigate to the SD card's `rootfs` directory and edit `/etc/dhcpcd.conf` with your
editor of choice (I use `vim`):

{{< highlight plain >}}
cd /media/sd/rootfs/etc
vim dhcpcd.conf
{{< / highlight >}}

Add these lines to the file:

{{< highlight plain >}}
interface eth0
static ip_address=192.168.4.2/24
static routers=192.168.4.1
static domain_name_servers=192.168.4.1
{{< / highlight >}}

<span id="connection-profile" />
## Configure host ethernet connection profile

Next, we'll set up an ethernet profile on the host PC that will allow us to
1) SSH into the Pi via ethernet and 2) share the host's internet connection
(if any) with the Pi. To do this, we'll use the NetworkManager connection
editor, which can be started from the terminal with:

{{< highlight plain >}}
nm-connection-editor
{{< / highlight >}}

This opens the following window:

{{< figure src="/img/rpi1.png" alt="Network Connections manager" >}}

Click the "+" button in the lower-left corner to add a new connection.

{{< figure src="/img/rpi2.png" alt="New connection" >}}

Select "Ethernet" from the connection type dropdown.

{{< figure src="/img/rpi3.png" alt="Connection settings" >}}

In the window that opens up, go to the IPv4 Settings tab. Select "Shared
to other computers" for Method, and add a new address with the values
address = 192.168.4.1, netmask = 24, and gateway = 192.168.4.1. Give the
new connection a name (I named mine "rpi"), then Save and exit.

Run the following `nmcli` terminal command to ensure the system doesn't
attempt to use the ethernet connection for internet instead of WiFi:

{{< highlight plain >}}
nmcli connection modify rpi ipv4.never-default true
{{< / highlight >}}

replacing `rpi` with whatever you named the connection.

<span id="connect-pi" />
## Connect the Raspberry Pi

At this point, you can insert the SD card into the Raspberry Pi, connect it
to your PC with the ethernet cable, and boot it up. Open up the PC's network
settings and ensure the new connection is activated.

{{< figure src="/img/rpi4.png" alt="Ubuntu network settings" >}}

Access the Pi via SSH using the static IP address we defined above. The default
username is `pi` and the default password is `raspberry`:

{{< highlight plain >}}
ssh pi@192.168.4.2
{{< / highlight >}}

On the Pi, permanently enable the SSH service:

{{< highlight plain >}}
systemctl enable ssh
systemctl start ssh
{{< / highlight >}}


<span id="references" />
# References

- [Headless Raspberry Pi Setup (SparkFun)][5]
- [Raspberry Pi remote access][6]
- [Share WiFi via Ethernet on Ubuntu 17.10][7]


[1]: https://www.amazon.com/gp/product/B075XMTQJC/
[2]: https://www.raspberrypi.org/software/operating-systems/#raspberry-pi-os-32-bit
[3]: https://www.raspberrypi.org/documentation/installation/installing-images/
[4]: https://github.com/raspberrypi/rpi-imager/issues/197
[5]: https://learn.sparkfun.com/tutorials/headless-raspberry-pi-setup/ethernet-with-static-ip-address
[6]: https://www.raspberrypi.org/documentation/remote-access/ssh/
[7]: https://www.cesariogarcia.com/?p=611
