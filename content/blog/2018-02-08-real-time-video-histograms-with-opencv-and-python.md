---
title: Real-time video histograms with OpenCV and Python
author: Najam Syed
type: post
date: 2018-02-09T04:25:15+00:00
url: /2018/02/08/real-time-video-histograms-with-opencv-and-python/
categories:
  - Computer Vision
tags:
  - histogram
  - image processing
  - matplotlib
  - OpenCV
  - Python
  - real-time

---
In this post, we&#8217;ll use OpenCV-Python to process video from a camera (or
from a video file) and Python&#8217;s matplotlib package to plot a histogram of
the video&#8217;s pixel intensities in real time. This is the final product:

{{< youtube iv60xgjGOvg >}}

What is a histogram and what is it good for? Histograms represent the frequency
with which something occurs. In the context of images (or video), a histogram
shows us the distribution of the intensity of all the pixels in the
image&#8212;in other words, how much of the image is light, how much of the
image is dark, and everything in between. In OpenCV, pixel intensity is
represented by an unsigned 8-bit integer, i.e., by a number from 0 to 255, where
0 is black and 255 is white. In an image with a lot of bright shades, more of
the pixels will be closer to 255. In contrast, in an image with a lot of dark
shades, a relatively large number of pixels will be closer to 0. Usually, the
pixel intensity range of 0 to 255 is sub-divided into groups of equal size,
called &#8220;bins,&#8221; to reduce computation time. For example, if we chose
to divide the range into 16 bins, the first bin&#8212;let&#8217;s call it bin
0&#8212;would contain pixel intensities from 0 to 15. Any pixel with a value
from 0 to 15 would fall into this first bin. The next bin, bin 1, would contain
pixel intensities from 16 to 31, and so on.

Histograms often serve important purposes in computer vision and image
processing. They can be used to determine how similar two images are, or they
can be used to differentiate objects in the foreground from the background,
since one will often be lighter than the other (which aids in thresholding). A
histogram also makes it easy to determine when an image has changed or when
something has moved. In the video above, you can see how even slight changes in
lighting or shadow are reflected in the histogram.

Let&#8217;s dive into the code and see how the video was created. Note that this
post assumes you have OpenCV and the OpenCV-Python bindings installed and set
up. Installing OpenCV can be an involved and nontrivial process that is
considerably outside the scope of this post. You might find the OpenCV
installation documentation for
[Linux](https://docs.opencv.org/2.4/doc/tutorials/introduction/linux_install/linux_install.html#linux-installation),
[Windows](https://docs.opencv.org/2.4/doc/tutorials/introduction/windows_install/windows_install.html#windows-installation), or
[iOS](https://docs.opencv.org/2.4/doc/tutorials/introduction/ios_install/ios_install.html#ios-installation) useful. Personally, I&#8217;m currently running OpenCV 3.2.0 on Ubuntu
16.04 and found
[Adrian Rosebrock’s instructions at pyimagesearch](https://www.pyimagesearch.com/2016/10/24/ubuntu-16-04-how-to-install-opencv/) to be invaluable.

# The code

Open your favorite editor and create a file named real\_time\_histogram.py, or
[grab the file from my Github](https://github.com/nrsyed/computer-vision/blob/master/real_time_histogram/real_time_histogram.py) and follow along.

{{< highlight python "linenos=true" >}}
import numpy as np
import matplotlib.pyplot as plt
import argparse
import cv2

parser = argparse.ArgumentParser()
parser.add_argument('-f', '--file',
    help='Path to video file (if not using camera)')
parser.add_argument('-c', '--color', type=str, default='gray',
    help='Color space: "gray" (default) or "rgb"')
parser.add_argument('-b', '--bins', type=int, default=16,
    help='Number of bins per channel (default 16)')
parser.add_argument('-w', '--width', type=int, default=0,
    help='Resize video to specified width in pixels (maintains aspect)')
args = vars(parser.parse_args())
{{< / highlight >}}

First, we import the necessary packages and set up the argument parser. All
arguments are optional; by default, the script will take video input from a
camera without resizing the video frames, and will display a grayscale histogram
with 16 bins.

{{< highlight python "linenos=true,linenostart=17" >}}
# Configure VideoCapture class instance for using camera or file input.
if not args.get('file', False):
    capture = cv2.VideoCapture(0)
else:
    capture = cv2.VideoCapture(args['file'])

color = args['color']
bins = args['bins']
resizeWidth = args['width']
{{< / highlight >}}

Next, we process the arguments. On **lines 19 and 21**, we create an object
called `capture`, an instance of the `VideoCapture` class. If using a camera,
`cv2.VideoCapture()` must be supplied with an integer representing the device
ID. If there&#8217;s only one camera connected, we can simply pass 0, as on
**line 19**. Alternatively, to read from a video file or image sequence, we must
pass it a filename, as on **line 21**.

{{< highlight python "linenos=true,linenostart=27" >}}
# Initialize plot.
fig, ax = plt.subplots()
if color == 'rgb':
    ax.set_title('Histogram (RGB)')
else:
    ax.set_title('Histogram (grayscale)')
ax.set_xlabel('Bin')
ax.set_ylabel('Frequency')
{{< / highlight >}}

Here, we initialize the plot and axis, as well as set the plot title and the x
and y axis labels.

{{< highlight python "linenos=true,linenostart=36" >}}
# Initialize plot line object(s). Turn on interactive plotting and show plot.
lw = 3
alpha = 0.5
if color == 'rgb':
    lineR, = ax.plot(np.arange(bins), np.zeros((bins,)), c='r', lw=lw, alpha=alpha)
    lineG, = ax.plot(np.arange(bins), np.zeros((bins,)), c='g', lw=lw, alpha=alpha)
    lineB, = ax.plot(np.arange(bins), np.zeros((bins,)), c='b', lw=lw, alpha=alpha)
else:
    lineGray, = ax.plot(np.arange(bins), np.zeros((bins,1)), c='k', lw=lw)
ax.set_xlim(0, bins-1)
ax.set_ylim(0, 1)
plt.ion()
plt.show()
{{< / highlight >}}

Next, we initialize the line(s) that will actually represent the histogram(s).
In the case of the RGB histogram (**lines 40-42**), we have three line objects,
one for each channel: red, green, and blue. In the grayscale histogram (**line
44**), there&#8217;s only one channel and, consequently, one line object. All
the lines are initialized with the specified number of bins on the x axis, with
the x axis values spanning the range from 0 to `bins - 1`, which is accomplished
with `np.arange(bins)`. Because a line requires both x values and y values to be
initialized, we also pass an array of zeros for the y data using
`np.zeros((bins,))`. The `lw` keyword argument sets the line width. The `c`
keyword argument sets the color. `alpha` sets the transparency of the line.

**Lines 45-46** set the x and y axis limits, respectively. On **line 47**, we
turn on interactive plotting. Although our plot will not be interactive,
interactive plotting allows other code to execute while the plot is
open&#8212;in this case, the &#8220;other code&#8221; is the upcoming block that
processes the video. **Line 48** displays the plot window.

{{< highlight python "linenos=true,linenostart=50" >}}
# Grab, process, and display video frames. Update plot line object(s).
while True:
    (grabbed, frame) = capture.read()

    if not grabbed:
        break

    # Resize frame to width, if specified.
    if resizeWidth > 0:
        (height, width) = frame.shape[:2]
        resizeHeight = int(float(resizeWidth / width) * height)
        frame = cv2.resize(frame, (resizeWidth, resizeHeight),
            interpolation=cv2.INTER_AREA)
{{< / highlight >}}

We arrive now at the loop that will continuously process each frame of the
video. On **line 52**, we utilize the `read()` method of our `VideoCapture`
class instance, `capture`. The `read()` method grabs, decodes, and returns the
next frame of the video, which we store in the variable `frame`. It also returns
a Boolean True if a frame was successfully grabbed or False if not, which we
store in the variable `grabbed`. A False value would be returned after the end
of the video, if reading from a file, or if the camera were disconnected, if
reading from a camera.

On **lines 58-62**, `frame` is resized to the specified width in pixels (if a
width was given as one of the arguments to the script). In OpenCV-Python, images
are represented by numpy arrays, so we can use standard numpy functions, as we
do on **line 59**, to get the height and width of the frame.

{{< highlight python "linenos=true,linenostart=64" >}}
# Normalize histograms based on number of pixels per frame.
numPixels = np.prod(frame.shape[:2])
if color == 'rgb':
    cv2.imshow('RGB', frame)
    (b, g, r) = cv2.split(frame)
    histogramR = cv2.calcHist([r], [0], None, [bins], [0, 255]) / numPixels
    histogramG = cv2.calcHist([g], [0], None, [bins], [0, 255]) / numPixels
    histogramB = cv2.calcHist([b], [0], None, [bins], [0, 255]) / numPixels
    lineR.set_ydata(histogramR)
    lineG.set_ydata(histogramG)
    lineB.set_ydata(histogramB)
else:
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    cv2.imshow('Grayscale', gray)
    histogram = cv2.calcHist([gray], [0], None, [bins], [0, 255]) / numPixels
    lineGray.set_ydata(histogram)
fig.canvas.draw()
{{< / highlight >}}

At last, the main event. For the RGB case, we first split the three-channel
image array into three single-channel arrays with `cv2.split()` on **line 68**.
_It is important to note that OpenCV uses the BGR format to represent images by
default_, hence the ordering of the tuple for the output arrays,
`(b, g, r) = cv2.split(frame)`. To actually compute the histograms, we use
`cv2.calcHist()`, which does the heavy lifting for us. The first argument to
`calcHist()` is a list of the source images. In this case, we&#8217;re computing
a one-dimensional histogram for each channel, so we only provide one image for
each histogram. However, the `calcHist()` function can also create
multidimensional histograms. For example, a two-dimensional RG histogram would
provide information on how frequently red and green (at varying intensities)
occur together in the same pixel.

The second argument to `calcHist()` is a list of the indices of the channels
from the source images to use for the histogram. Again, since we&#8217;re
supplying a single-channel source image for each histogram, there&#8217;s only
one index: `[0]`. The third argument is an optional mask, e.g., if we were only
interested in a certain part of the image, we could create a mask&#8212;a 2D
array of the same width and height as the source images that contained positive
nonzero integers for the pixels we were interested in and zeros for the pixels
we wanted to ignore. In this case, we&#8217;re interested in the whole image, so
we set the mask argument to `None`. The fourth argument to `calcHist()` is a
list of the number of bins for each dimension of the histogram. Since
we&#8217;re creating one-dimensional arrays, we supply it with a single value.
The fifth argument is a list of the `min, max` values of the bin boundaries for
each dimension. OpenCV represents images with unsigned 8-bit integers, which
take on a range of values from 0 to 255.

After computing the histograms, the plot line objects defined earlier are
updated with the new frequencies on **lines 72-74**.

The grayscale histogram is similar, except we first convert the image from BGR
to grayscale with `cv2.cvtColor()` on **line 76**. Because there&#8217;s only
one channel (and one corresponding plot line object), we only need one call to
`calcHist()`. In both cases, the image is displayed with `cv2.imshow()`, whose
first argument is a string for the title of the window and whose second argument
is the image to display.

To actually refresh the plot, we call `fig.canvas.draw()`.

{{< highlight python "linenos=true,linenostart=82" >}}
if cv2.waitKey(1) & 0xFF == ord('q'):
    break

ure.release()
destroyAllWindows()
{{< / highlight >}}

Finally, the if statement on **line 82** exits the loop if the user presses the
Q key. The function `cv2.waitKey()` waits for a keypress for a number of
milliseconds determined by the input argument. `cv2.waitKey(1)` means it waits 1
millisecond. If it&#8217;s given an integer less than or equal to zero, it waits
indefinitely (if we did this instead of a positive value like 1, the loop
wouldn&#8217;t proceed to the next iteration until a key was pressed). If a key
is pressed, a 32-bit int is returned, but only the last 8 bits of the value
correspond to the ASCII representation of the key. The bitwise AND operator `&`
is used to extract these 8 bits (`0xFF` is a hex value that is equivalent to
11111111 in binary, i.e., `0b11111111`). This 8-bit ASCII value is then compared
to the ASCII value of &#8220;q,&#8221; which is given by the built-in Python
function `ord()`.

Once the loop is exited, the `VideoCapture` method `release()` closes the video
file or camera input, and `cv2.destroyAllWindows()` closes any open OpenCV
windows.

Hopefully, that was relatively straightforward. Perhaps we&#8217;ll explore uses
of histograms in a future post.
