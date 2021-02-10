---
title: Get pixel RGB value from webcam video in OpenCV (C++ and Python)
author: Najam Syed
type: post
date: 2018-02-13T03:19:54+00:00
url: /2018/02/12/get-pixel-rgb-value-from-webcam-video-in-opencv-c-and-python/
categories:
  - Computer Vision
tags:
  - C++
  - OpenCV
  - Python

---
This post will go through a simple OpenCV utility I made that allows you to get
the RGB value of any pixel in a snapshot taken from a webcam&#8217;s video feed.
The program presents the user with a &#8220;Video&#8221; window, which displays
the source video from the webcam, and a &#8220;Snapshot&#8221; window, which
displays the last snapshot taken; a snapshot of the current frame of the video
is taken by pressing the &#8220;T&#8221; key on the keyboard. Finally,
there&#8217;s a &#8220;Color&#8221; window; when the user clicks anywhere within
the Snapshot window, the color of the pixel they clicked on fills the Color
window, and the RGB value corresponding to the color is displayed. This allows
the user to check visually that they did, in fact, click on the correct pixel in
the Snapshot window and that the RGB value corresponds to the color they
actually wanted. Here&#8217;s a demonstration:

{{< youtube EvBfcM2Y-Kk >}}

# The code

Both
[the C++ version](https://github.com/nrsyed/computer-vision/blob/master/get_video_pixel/get_video_pixel.cpp) and
[the Python version](https://github.com/nrsyed/computer-vision/blob/master/get_video_pixel/get_video_pixel.py) of the program can be found on Github. Below, we&#8217;ll
go through them simultaneously. For each block of code, I&#8217;ll start with
the Python version to explain the gist and touch on Python-specific
implementation details, then show the C++ version and discuss C++-specific
implementation details.

_Python_

{{< highlight python "linenos=true" >}}
import numpy as np
import cv2

COLOR_ROWS = 80
COLOR_COLS = 250
{{< / highlight >}}

<br class="" />
_C++_

{{< highlight cpp "linenos=true" >}}
#include <iostream>
#include <string>
#include <opencv2/opencv.hpp>
#include <opencv2/videoio.hpp>
#include <opencv2/highgui.hpp>
#include <opencv2/imgproc.hpp>

#define COLOR_ROWS 80
#define COLOR_COLS 250
{{< / highlight >}}

First, our imports/globals and includes/defines. `COLOR_ROWS` and `COLOR_COLS`
are used to set the size of the Color window or, more specifically, the size of
the image that fills the Color window.

_Python_

{{< highlight python "linenos=true,linenostart=7" >}}
capture = cv2.VideoCapture(0)
if not capture.isOpened():
    raise RuntimeError('Error opening VideoCapture.')

(grabbed, frame) = capture.read()
snapshot = np.zeros(frame.shape, dtype=np.uint8)
cv2.imshow('Snapshot', snapshot)

colorArray = np.zeros((COLOR_ROWS, COLOR_COLS, 3), dtype=np.uint8)
cv2.imshow('Color', colorArray)
{{< / highlight >}}

First, we initialize a `VideoCapture` object, which I&#8217;ve named `capture`,
on **line 7**. The input to the constructor, `0` (in `cv2.VideoCapture(0)`) is
the device ID of the camera; if there&#8217;s only one webcam connected, you can
simply provide `0`. On **lines 8-9**, we check that the previous step was
successful. On **line 11** we use `capture.read()` to grab, decode, and return
the first frame of the video in the form of a numpy array, which we&#8217;ll
call `frame`. On **lines 12-13**, we use the shape of the video output `frame`
to initialize `snapshot`, which is the image array that will be displayed in the
Snapshot window (to start with, we initialize the snapshot array to an entirely
black image using `np.zeros()`). The Snapshot window is shown with
`cv2.imshow('Snapshot', snapshot)`. In a similar fashion, we initialize the
color image array, `colorArray`, which will be displayed in the Color window, on
**lines 15-16**.

_C++_

{{< highlight cpp "linenos=true,linenostart=39" >}}
int main(int argc, char** argv) {
	cv::VideoCapture capture(0);

	if (!capture.isOpened()) {
		std::cout << "Error opening VideoCapture." << std::endl;
		return -1;
	}

	cv::Mat frame, snapshot, colorArray;
	capture.read(frame);

	snapshot = cv::Mat(frame.size(), CV_8UC3, cv::Scalar(0,0,0));
	cv::imshow("Snapshot", snapshot);

	colorArray = cv::Mat(COLOR_ROWS, COLOR_COLS, CV_8UC3, cv::Scalar(0,0,0));
	cv::imshow("Color", colorArray);
{{< / highlight >}}

We achieve the same thing in the C++ version with a few different constructs
(also note that the line number jump in the C++ version occurs because it's
organized slightly differently than the Python version). After initializing and
checking the `VideoCapture` object on **lines 40-45**, we declare `frame`,
`snapshot`, and `colorArray` as `Mat` objects. On **line 48**, the first frame
of the video is read into `frame`. On **line 50**, we initialize `snapshot` by
providing the size of `frame`, the datatype `CV_8UC3` for the `Mat` array, and a
`Scalar` object representing a black pixel, i.e., `cv::Scalar(0,0,0)`. The
datatype `CV_8UC3` tells the constructor that we're creating a `Mat` object with
3 channels (the `C3` in `CV_8UC3`) whose values will be 8-bit unsigned ints (the
`8U` in `CV_8UC3`). The `Scalar` object is counterintuitively named, because
it's essentially a wrapper for a standard C++ `Vector` of up to 4 elements
(though we only use 3 elements here). We call the same `Mat` constructor on
**line 53** to initialize `colorArray`.

_Python_

{{< highlight python "linenos=true,linenostart=18" >}}
def on_mouse_click(event, x, y, flags, userParams):
    if event == cv2.EVENT_LBUTTONDOWN:
        colorArray[:] = snapshot[y, x, :]
        rgb = snapshot[y, x, [2,1,0]]

        # From stackoverflow.com/questions/1855884/determine-font-color-based-on-background-color
        luminance = 1 - (0.299*rgb[0] + 0.587*rgb[1] + 0.114*rgb[2]) / 255
        if luminance < 0.5:
            textColor = [0,0,0]
        else:
            textColor = [255,255,255]

        cv2.putText(colorArray, str(rgb), (20, COLOR_ROWS - 20),
            fontFace=cv2.FONT_HERSHEY_SIMPLEX, fontScale=0.8, color=textColor)
        cv2.imshow('Color', colorArray)

cv2.setMouseCallback('Snapshot', on_mouse_click)
{{< / highlight >}}

Next, we define the event callback function `on_mouse_click()`, which, when a
pixel is clicked in the Snapshot window, will get the RGB value of the pixel and
update the Color window accordingly. Although I use the term RGB (because that's
the order in which we will display the values on the screen), OpenCV uses BGR by
default. We will have to account for this when displaying the RGB text string.
Also note that the function doesn't have to be named `on_mouse_click`
&#8212;I've just called it that because it's how we'll be using it by checking,
on **line 19**, if the left mouse button was clicked. On **line 20**, we extract
the value of the clicked pixel and store it in `colorArray`. On **line 21**, we
extract the value of the clicked pixel in RGB format and store it in `rgb`.

**Lines 24-28** determine whether the text in the Color window should be black
or white, based on the
[relative luminance](https://en.wikipedia.org/wiki/Relative_luminance) of the pixel color (the pixel color will fill the
background of the Color window, and the text will be superimposed on top of it,
so the text color must be chosen such that it will be readable). This is
achieved by means of the formula on **line 24**, which I borrowed from
[an answer on StackOverflow](https://stackoverflow.com/questions/1855884/determine-font-color-based-on-background-color). On **lines 30-32**, we add the text in the
appropriate `textColor` to `colorArray` by means of `cv2.putText()`, then update
the Color window. Finally, **line 34** connects this callback function to the
Snapshot window.

_C++_

{{< highlight cpp "linenos=true,linenostart=11" >}}
void on_mouse_click(int event, int x, int y, int flags, void* ptr) {
	if (event == cv::EVENT_LBUTTONDOWN) {
		cv::Mat* snapshot = (cv::Mat*)ptr;
		cv::Vec3b pixel = snapshot->at<cv::Vec3b>(cv::Point (x, y));
		int b, g, r;
		b = pixel[0];
		g = pixel[1];
		r = pixel[2];
		std::string rgbText = "[" + std::to_string(r) + ", " + std::to_string(g)
			+ ", " + std::to_string(b) + "]";

		// From stackoverflow.com/questions/1855884/determine-font-color-based-on-background-color
		float luminance = 1 - (0.299*r + 0.587*g + 0.114*b) / 255;
		cv::Scalar textColor;
		if (luminance < 0.5) {
			textColor = cv::Scalar(0,0,0);
		} else {
			textColor = cv::Scalar(255,255,255);
		}

		cv::Mat colorArray;
		colorArray = cv::Mat(COLOR_ROWS, COLOR_COLS, CV_8UC3, cv::Scalar(b,g,r));
		cv::putText(colorArray, rgbText, cv::Point2d(20, COLOR_ROWS - 20),
			cv::FONT_HERSHEY_SIMPLEX, 0.8, textColor);
		cv::imshow("Color", colorArray);
	}
}
{{< / highlight >}}

The C++ counterpart to the `on_mouse_click()` function follows the same basic
idea. However, unlike Python, functions in C++ do not have direct access to any
scope outside their own. Therefore, we pass a pointer to `snapshot` via the last
argument to `on_mouse_click()`. On **line 13**, we cast the input pointer to a
`Mat` pointer. On **line 14**, we treat the pixel in `snapshot` as a `Vec3b`
type, which is essentially just a `Vector` with 3 elements, and access the pixel
using `at`, which requires us to specify the type (`<cv::Vec3b>`) and the point.
The point is specified with a `Point` object, which is simply an object that
possesses an `x` attribute and a `y` attribute. On lines **15-20**, we extract
the RGB values and construct the text string to be displayed. The rest of this
block of code is analogous to the Python version.

Returning briefly to the `main()` method, we use `setMouseCallback()` to link
the callback function to the Snapshot window:

{{< highlight cpp "linenos=true,linenostart=55" >}}
cv::setMouseCallback("Snapshot", on_mouse_click, &snapshot);
{{< / highlight >}}

The first argument to `setMouseCallback()` is the name of the window. The second
argument is the name of the function. The third argument is for any other
parameter we wish to pass&#8212;in this case, a pointer to `snapshot`. If we
didn't want to pass anything else, we would simply pass `NULL`.

_Python_

{{< highlight python "linenos=true,linenostart=36" >}}
while True:
    (grabbed, frame) = capture.read()
    cv2.imshow('Video', frame)

    if not grabbed:
        break

    keyVal = cv2.waitKey(1) & 0xFF
    if keyVal == ord('q'):
        break
    elif keyVal == ord('t'):
        snapshot = frame.copy()
        cv2.imshow('Snapshot', snapshot)

capture.release()
cv2.destroyAllWindows()
{{< / highlight >}}

Lastly, we come to the main loop, which continually grabs and returns frames
from the webcam video source. If this is unsuccessful (which might occur if the
camera is suddenly disconnected), **lines 40-41** exit the loop. **Line 43**
checks to see if a key has been pressed via `cv2.waitKey(1)`, where the `1`
indicates the timeout in milliseconds. The `waitKey()` function returns a 32-bit
int whose last 8 bits are the ASCII representation of the key pressed, if any
key was pressed. Using the bitwise AND `&` isolates these 8 bits (0xFF is a hex
value equal to 0b11111111 in binary). The built-in Python function `ord()`
returns the ASCII representation of the given character. In other words, the
if-elseif statement on **lines 44-48** checks whether the "q" key has been
pressed, in which case it breaks the loop, or whether the "t" key has been
pressed, in which case it **t**akes a snapshot by updating `snapshot` with the
current frame and updating the Snapshot window with the new `snapshot`. To
update the `snapshot` array, we use the numpy function `copy()`. If we didn't do
this (and instead used `snapshot = frame`), `snapshot` would simply refer to
`frame`, i.e., clicking in the Snapshot window would yield the current pixel
value of the live webcam source, not the "frozen" snapshot.

_C++_

{{< highlight cpp "linenos=true,linenostart=57" >}}
int keyVal;
	while (1) {
		if (!capture.read(frame)) {
			break;
		}
		cv::imshow("Video", frame);

		keyVal = cv::waitKey(1) & 0xFF;
		if (keyVal == 113) {
			break;
		} else if (keyVal == 116) {
			snapshot = frame.clone();
			cv::imshow("Snapshot", snapshot);
		}
	}
	return 0;
}
{{< / highlight >}}

Again, the C++ version is analogous to the Python version. The only difference
is that, here, we use the actual ASCII decimal values, 113 (q) and 116 (t), for
the comparisons on **lines 65 and 67**. On **line 68**, we use the `Mat` method
`clone` to create a snapshot of the current frame.

That's it. I hope you've found this program (or this post) useful.
