---
title: How to install OpenCV on Arch Linux (in a VirtualBox VM)
author: Najam Syed
type: post
date: 2018-10-28T05:38:52+00:00
url: /2018/10/28/how-to-install-opencv-on-arch-linux-in-a-virtualbox-vm/
categories:
  - Computer Vision
  - Linux
tags:
  - Arch
  - Arch Linux
  - build
  - C++
  - compile
  - computer vision
  - Linux
  - OpenCV
  - Python
  - repository
  - source
  - virtual environment
  - virtual machine
  - VirtualBox
  - virtualenv
  - VM

---
- [Introduction](#introduction)
- [Prerequisites](#prerequisites)
- [Install OpenCV from the Arch repositories](#heading-from-repo)
- [Install OpenCV by building from source](#heading-from-source)
  - [Virtual machine&#8211;specific details](#aside-vm-details)
  - [Potential error: can't write PCH file](#aside-pch-error)
  - [Potential issue: make hangs at XX%](#aside-make-hangs)
- [Check the installation (C++)](#heading-check-cpp)
  - [Potential error: No such file or directory](#aside-no-header)
- [Link the OpenCV Python bindings](#heading-link-python)

## Introduction

If you&#8217;re looking to install OpenCV on Arch, you have two options. The
first is to just use the
[pre-compiled package](https://www.archlinux.org/packages/extra/x86_64/opencv/)
available in the official Arch repositories.

The other option is to compile OpenCV from source, which gives you more control
over what gets installed. For starters, if you install from the Arch
repositories, you&#8217;re locked in to the version of OpenCV for which the
package was compiled, which, at the time of this writing, is 3.4.3&#8212;the
current stable release. The 4.0.0 pre-release is not yet available through the
repositories. This probably won&#8217;t be an issue for most people, but could
be if you need features only available in the pre-release.

Furthermore, the pre-built package seems like it contains all available modules,
including extra modules from the `opencv_contrib` Github repository.
Again, this isn&#8217;t a problem in and of itself, but may be if you
don&#8217;t want the extra modules or are working on a system with limited
storage space.

Additionally, if you plan to use OpenCV-Python, the Python hooks in the
pre-built package have been compiled against Python 2.7 and Python 3.7. Once
again, most likely not an issue, but if you&#8217;re using a different version
of Python on your machine, it may present problems. The pre-built package has
also been compiled against a specific version of numpy&#8212;likely the latest
at the time of its release&#8212;and if you&#8217;re using a different version
of numpy, there may also be compatibility issues.

Lastly, the title mentions installing on a copy of Arch that&#8217;s running in
a VM. While I did perform my install in a VM, the instructions are applicable
for any installation of OpenCV on Arch, whether in a VM or not. There are a
couple VM-specific pieces of information that have clearly been marked as such;
you can ignore these if they&#8217;re not applicable to you.

With that out of the way, let&#8217;s dive in.

## Prerequisites

You&#8217;ll want to make sure you&#8217;ve installed `base-devel`
(which is simply a group of development-related packages), `cmake`,
and `ffmpeg` (or libav video codecs). You may also want to make sure
you have image codec libraries, like `libjpeg-turbo` and `libtiff`.
You can find a more thorough list of dependencies in the
[OpenCV documentation](https://docs.opencv.org/master/d7/d9f/tutorial_linux_install.html).

If you plan to work with Python, you should obviously have Python installed, as
well as `python-pip`. Generally, with Python, you&#8217;ll want to
work in a virtual environment, so be sure you&#8217;ve also installed
`virtualenv` through `pip`.

{{< highlight bash >}}
$ sudo pip install virtualenv
{{< / highlight >}}

**Generally, you should not install Python packages with `sudo`!**
Doing so installs them globally rather than within an
isolated, controlled virtual environment. The only Python packages you should
install globally should be those related to setting up and managing virtual
environments. Personally, I like to supplement `virtualenv` with
`virtualenvwrapper`:

{{< highlight bash >}}
$ sudo pip install virtualenv virtualenvwrapper
{{< / highlight >}}

Like the examples shown in the
[virtualenvwrapper installation documentation](https://virtualenvwrapper.readthedocs.io/en/latest/install.html), I use
`~/.virtualenvs` as the directory for my virtual environments, but you can
use any directory you&#8217;d like.

For the remainder of this post, I&#8217;ll use a Python virtual environment
named `cv` but, again, you can name it anything. To create a new
virtual environment with `virtualenvwrapper`, issue the following command:

{{< highlight bash >}}
$ mkvirtualenv cv
{{< / highlight >}}

Ensure the virtual environment is activated, then install `numpy`.

{{< highlight bash >}}
$ workon cv
$ pip install numpy
{{< / highlight >}}

## <span id="heading-from-repo">Install OpenCV from the Arch repositories</span>

The easiest way to install OpenCV on Arch is to simply use the
[pre-built package](https://www.archlinux.org/packages/extra/x86_64/opencv/) from the official repositories.

{{< highlight bash >}}
$ sudo pacman -S opencv
{{< / highlight >}}

Optionally, you can also install the OpenCV samples:

{{< highlight bash >}}
$ sudo pacman -S opencv opencv-samples
{{< / highlight >}}

## <span id="heading-from-source">Install OpenCV by building from source</span>

First, make sure git is installed.

{{< highlight bash >}}
$ sudo pacman -S --needed git
{{< / highlight >}}

Clone the main `opencv` repository and, if desired, the
`opencv_contrib` repository, which contains extra modules, from Github. For
simplicity, the instructions that follow will put these repositories in your
home directory, but the location doesn&#8217;t matter.

{{< highlight bash >}}
$ cd ~
$ git clone https://github.com/opencv/opencv.git
$ git clone https://github.come/opencv/opencv_contrib.git
{{< / highlight >}}

The rest of the instructions for this step borrow from
[Adrian Rosebrock’s latest post](https://www.pyimagesearch.com/2018/05/28/ubuntu-18-04-how-to-install-opencv/) on installing OpenCV for Ubuntu 18.04.

Within the cloned `opencv` repository, make a directory named
`build` and `cd` into that directory.

{{< highlight bash >}}
$ cd ~/opencv
$ mkdir build
$ cd build

{{< / highlight >}}

Next, ensure that your Python virtual environment is active, then run
`cmake` with the following parameters:

{{< highlight bash >}}
$ cmake -D CMAKE_BUILD_TYPE=RELEASE \
  -D CMAKE_INSTALL_PREFIX=/usr/local \
  -D INSTALL_PYTHON_EXAMPLES=OFF \
  -D INSTALL_C_EXAMPLES=OFF \
  -D OPENCV_EXTRA_MODULES_PATH=~/opencv_contrib/modules \
  -D PYTHON_EXECUTABLE=~/.virtualenvs/cv/bin/python \
  -D BUILD_EXAMPLES=ON \
  -D ENABLE_PRECOMPILED_HEADERS=ON ..

{{< / highlight >}}

You can choose whether to compile or not compile any of the
examples&#8212;they&#8217;re not necessary for the installation itself. If
you&#8217;ve chosen not to install the `opencv_contrib` modules,
omit that line above. To obtain the correct path to your Python executable, make
sure you&#8217;re in the correct virtual environment, then use the
`which` command:

{{< highlight bash >}}
$ which python
/home/najam/.virtualenvs/cv/bin/python
{{< / highlight >}}

After you&#8217;ve run this `cmake` command, examine the output,
particularly the Python-related portions near the end. It should look something
like this:

{{< figure src=/img/arch_cv_cmake.jpg >}}

In particular, make sure that the lines for the Python interpreter and
`numpy` point to the correct locations&#8212;they should correspond to the
path for your virtual environment. If they&#8217;re not correct, remove all
files from the `build` folder:

{{< highlight bash >}}
$ rm -R ~/opencv/build/*
{{< / highlight >}}

Be sure you&#8217;ve activated the correct virtual environment and that the
`cmake` flags are correct. Examine the rest of the
`cmake` output as well to make sure nothing else important is missing.
Then, run the aforementioned `cmake` command again.

Once `cmake` is happy (and you&#8217;re satisfied with its output),
it&#8217;s time to actually build the necessary files. In the
`build` directory, simply run `make`. To speed up the build
process, take advantage of all the cores your processor has with the
`-j` flag.

{{< highlight bash >}}
$ make -j4
{{< / highlight >}}

In this example, `-j4` instructs `make` to run up to
four jobs in parallel (assuming your processor has at least four CPUs). Run
`lscpu` to find out how many CPUs are available on your system:

{{< highlight bash >}}
$ lscpu | grep -i '^cpu(s)'
CPU(s):        4

{{< / highlight >}}


<div class="aside">
<h3 id="aside-vm-details">Virtual machine&#8211;specific details</h3>

If, like me, you&#8217;re working with a copy of Arch in a virtual machine, you
may have to make a couple adjustments. The instructions and screenshots below
are for VirtualBox, since that&#8217;s what I&#8217;m using.

To permit the VM to utilize your CPU&#8217;s cores for the build process (i.e.,
for `make`&#8217;s `-j` flag), make the following
changes in the VM&#8217;s System settings:

1. On the Motherboard tab, check &#8220;Enable I/O APIC&#8221; under Extended Features.
{{< figure src=/img/arch_cv_vm_settings1.png >}}

2. On the Acceleration tab, make sure that &#8220;Enable VT-x/AMD-V&#8221; is
selected under Hardware Virtualization.
{{< figure src=/img/arch_cv_vm_settings2.png >}}

3. On the Processor tab, increase the number of CPUs to the desired number.
{{< figure src=/img/arch_cv_vm_settings3.png >}}

In the VM itself, check that the number of CPUs reflects your chosen settings by
running `lscpu` as mentioned previously.
</div>

<div class="aside">
<h3 id="aside-pch-error">Potential error: can't write PCH file</h3>

In my case, the partition on which I was installing OpenCV apparently
wasn&#8217;t large enough to fit some of the header files created during the
build process (which can be several GB larger than the library itself).
Specifically, I received the following error:

{{< highlight bash >}}
fatal error: can't write PCH file: No space left on device
compilation terminated
{{< / highlight >}}

{{< figure src=/img/arch_cv_pch_error.jpg >}}

(Note that the output of my `make` command in the screenshot above
is more verbose than normal because I ran it with the `-d` (debug) flag).

&#8220;PCH&#8221; refers to &#8220;precompiled headers.&#8221; To address this
error, I had to re-run `cmake` with `-DENABLE_PRECOMPILED_HEADERS=OFF`. If you
have to do this, remove all the files originally generated by `cmake` first.
</div>

<div class="aside">
<h3 id="aside-make-hangs">Potential issue: make hangs at XX%</h3>

This seems to be a relatively common problem, according to a Google search, in
which `make` reaches [28%] or [37%] or [99%] or [100%] or some other
percentage and hangs there indefinitely. Some individuals report having to wait
up to 20 or 30 minutes at [99%] or [100%], so try being patient, first. However,
if that doesn&#8217;t help, there may be a few potential solutions.

In my case, I hadn&#8217;t given my VM instance enough RAM. I found that
increasing the amount of memory from 1GB to 2GB in the instance System settings
Motherboard tab (&#8220;Base Memory&#8221;) did the trick.

{{< figure src=/img/arch_cv_vm_settings1.png >}}

Other solutions include compiling with a single CPU via `make -j1`
or increasing the amount of swap space. You can also run `make` with
the `-d` option to print all debug information, which might help you
zero in on the issue if the aforementioned solutions don&#8217;t work.
</div>

Hopefully, at this point, you&#8217;ve been able to get OpenCV to compile
successfully. The next step is to perform the actual install and update the
linker with the following commands:

{{< highlight bash >}}
$ sudo make install
$ sudo ldconfig
{{< / highlight >}}

## <span id="heading-check-cpp">Check the installation (C++)</span>

After completing the installation per the previous steps, fire up a text editor
and write the following short C++ program (I&#8217;ll call it `cv.cpp`):

{{< highlight cpp >}}
#include <iostream>
#include <opencv2/core.hpp>

int main() {
  std::cout << "OpenCV version: " << CV_VERSION << std::endl;
  return 0;
}
{{< / highlight >}}

Then compile and run the program as follows.

{{< highlight bash >}}
$ g++ cv.cpp -o cv
$ ./cv
OpenCV version: 4.0.0-pre
{{< / highlight >}}

<div class="aside">
<h3 id="aside-no-header">Potential error: No such file or directory</h3>

When I first tried to compile the program above, I received the following error:

{{< highlight plain >}}
fatal error: opencv2/core.hpp: No such file or directory
#include <opencv2/core.hpp>
compilation terminated
{{< / highlight >}}

{{< figure src=/img/arch_cv_header_error.png >}}

To troubleshoot the issue, I ran `find` from the root directory:

{{< highlight bash >}}
$ cd /
$ sudo find . -name '*core.hpp'
{{< / highlight >}}

Ignoring the results from my home directory (which were simply from the build,
not the install), I saw that the header files had been installed to
`/usr/local/include/opencv4/opencv2/` instead of `/usr/local/include/opencv2/`:

{{< figure src=/img/arch_cv_find.png >}}

I've used the procedure in this post to build and install OpenCV (including the
4.0.0 pre-release) from source in the past and haven't encountered this issue
before. Thus, I have no idea whether it's due to some peculiarity with my system
and setup&#8212;with Arch or with VirtualBox&#8212;or whether I overlooked
something during the build process. If you can shed some light on this
phenomenon, please leave a comment or send me a message. Regardless, I was able
to solve it by creating a symlink as follows:

{{< highlight bash >}}
$ sudo ln -s /usr/local/include/opencv4/opencv2/ /usr/local/include/opencv2
{{< / highlight >}}

After doing this, I had no problems compiling the program.
</div>

## <span id="heading-link-python">Link the OpenCV Python bindings</span>

Lastly, if you're planning to use OpenCV-Python, you need to create a symlink
between the OpenCV Python shared library and your Python virtual environment.
The file you need to link to should be located in
`/usr/local/lib/python3.7/site-packages` (replace `python3.7`
with the version against which you built OpenCV) and will be named something
like `cv2.cpython-37m-x86_64-linux-gnu.so`. If you can't find it
there, run a search with the `find` command:

{{< highlight bash >}}
$ cd /
$ sudo find . -name 'cv2*.so'
{{< / highlight >}}

You'll want to create a symlink to that file in the `site-packages`
directory *of your virtual environment*. In my case, that would be
`~/.virtualenvs/cv/lib/python3.7/site-packages`. Replace this path
with the path corresponding to your virtual environment, and name the symlink
`cv2.so`, as in the following example.

{{< highlight bash >}}
$ ln -s /usr/local/lib/python3.7/site-packages/cv2.cpython-37m-x86_64-linux-gnu.so ~/.virtualenvs/cv/lib/python3.7/site-packages/cv2.so
{{< / highlight >}}

Now, test it out. Make sure you're in your Python virtual environment, enter the
Python shell, and run a couple commands:

{{< highlight bash >}}
$ workon cv
$ python
Python 3.7.1 (default, Oct 22 2018, 10:41:28)
[GCC 8.2.1 20180831] on linux
Type "help", "copyright", "credits" or "license" for more information.
>>> import cv2
>>> cv2.__version__
'4.0.0-pre'
>>>
{{< / highlight >}}

Congratulations! If you've gotten this far, everything should finally be
working. Plus, if you've gone the route of building from source, it makes you
feel like you've really accomplished something, which, I think, is its own
reward.
