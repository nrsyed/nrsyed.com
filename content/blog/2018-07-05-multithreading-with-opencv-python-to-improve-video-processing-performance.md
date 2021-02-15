---
title: Multithreading with OpenCV-Python to improve video processing performance
author: Najam Syed
type: post
date: 2018-07-06T03:19:24+00:00
url: /2018/07/05/multithreading-with-opencv-python-to-improve-video-processing-performance/
categories:
  - Computer Vision
tags:
  - image processing
  - multithreading
  - OpenCV
  - Python

---
Video processing can be a computationally intensive task, and since computing
power is often at a premium, the more we can speed up a video processing
pipeline, the better. This is especially true for applications that require
real-time processing, like processing a video stream from a webcam. While
it&#8217;s important that the image processing portion of a video processing
pipeline be streamlined, input/output (I/O) operations also tend to be a major
bottleneck. One way to alleviate this is to split the computational load between
multiple threads. It&#8217;s important to note that, in Python, there exists
something called the _global interpreter lock (GIL)_, which prevents multiple
threads from accessing the same object. However, as the
[Python Wiki](https://wiki.python.org/moin/GlobalInterpreterLock) tells us:

> &#8230;potentially blocking or long-running operations, such as I/O, image
processing, and NumPy number crunching, happen outside the GIL. Therefore it is
only in multithreaded programs that spend a lot of time inside the GIL &#8230;
that the GIL becomes a bottleneck.

In other words, blocking I/O operations (which &#8220;block&#8221; the execution
of later code until the current code executes), like reading or displaying video
frames, are ripe for multithreaded execution. In this post, we&#8217;ll examine
the effect of putting calls to `cv2.VideoCapture.read()` and `cv2.imshow()` in
their own dedicated threads.

All the code used in this post
[can be found on Github](https://github.com/nrsyed/computer-vision/tree/master/multithread).

# Measuring changes in performance

First, we must define &#8220;performance&#8221; and how we intend to evaluate
it. In a single-threaded video processing application, we might have the main
thread execute the following tasks in an infinitely looping while loop: 1) get a
frame from the webcam or video file with `cv2.VideoCapture.read()`, 2) process
the frame as we need, and 3) display the processed frame on the screen with a
call to `cv2.imshow()`. By moving the reading and display operations to other
threads, each iteration of the while loop should take less time to execute.
Consequently, we&#8217;ll define our performance metric as the number of
iterations of the while loop in the main thread executed per second.

To measure iterations of the main while loop executing per second, we&#8217;ll
create a class and call it `CountsPerSec`,
[which can be found on Github](https://github.com/nrsyed/computer-vision/blob/master/multithread/CountsPerSec.py).

{{< highlight python "linenos=true" >}}
from datetime import datetime

class CountsPerSec:
    """
    Class that tracks the number of occurrences ("counts") of an
    arbitrary event and returns the frequency in occurrences
    (counts) per second. The caller must increment the count.
    """

    def __init__(self):
        self._start_time = None
        self._num_occurrences = 0

    def start(self):
        self._start_time = datetime.now()
        return self

    def increment(self):
        self._num_occurrences += 1

    def countsPerSec(self):
        elapsed_time = (datetime.now() - self._start_time).total_seconds()
        return self._num_occurrences / elapsed_time
{{< / highlight >}}

We import the `datetime` module to track the elapsed time. At the end of each
iteration of the while loop, we&#8217;ll call `increment()` to increment the
count. During each iteration, we&#8217;ll obtain the average _iterations per
second_ for the video with a call to the `countsPerSec()` method.

# Performance without multithreading

Before examining the impact of multithreading, let&#8217;s look at performance
without it. Create a file named `thread_demo.py`, or
[grab it on Github and follow along](https://github.com/nrsyed/computer-vision/blob/master/multithread/thread_demo.py).

{{< highlight python "linenos=true" >}}
import argparse
import cv2
from CountsPerSec import CountsPerSec
from VideoGet import VideoGet
from VideoShow import VideoShow

def putIterationsPerSec(frame, iterations_per_sec):
    """
    Add iterations per second text to lower-left corner of a frame.
    """

    cv2.putText(frame, "{:.0f} iterations/sec".format(iterations_per_sec),
        (10, 450), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 255, 255))
    return frame
{{< / highlight >}}

We begin with some imports, including the `CountsPerSec` class we made above. We
haven&#8217;t covered the `VideoGet` and `VideoShow` classes yet, but these will
be used to execute the tasks of getting video frames and showing video frames,
respectively, in their own threads. The function `putIterationsPerSec()`
overlays text indicating the frequency of the main while loop, in iterations per
second, to a frame before displaying the frame. It accepts as arguments the
frame (a numpy array) and the iterations per second (a float), overlays the
value as text via `cv2.putText()`, and returns the modified frame.

Next, we&#8217;ll define a function, `noThreading()`, to get frames, compute and
overlay the iterations per second value on each frame, and display the frame.

{{< highlight python "linenos=true,linenostart=16" >}}
def noThreading(source=0):
    """Grab and show video frames without multithreading."""

    cap = cv2.VideoCapture(source)
    cps = CountsPerSec().start()

    while True:
        (grabbed, frame) = cap.read()
        if not grabbed or cv2.waitKey(1) == ord("q"):
            break

        frame = putIterationsPerSec(frame, cps.countsPerSec())
        cv2.imshow("Video", frame)
        cps.increment()
{{< / highlight >}}

The function takes the video source as its only argument. If given an integer,
`source` indicates that the video source is a webcam. 0 refers to the first
webcam, 1 would refer to a second connected webcam, and so on. If a string is
provided, it&#8217;s interpreted as the path to a video file. On **lines
19-20**, we create an OpenCV `VideoCapture` object to grab and decode frames
from the webcam or video file, as well as a `CountsPerSec` object to track the
main while loop&#8217;s performance. **Line 22** begins the main while loop. On
**line 23**, we utilize the `VideoCapture` object&#8217;s `read()` method to get
and decode the next frame of the video stream; it returns a boolean, `grabbed`,
indicating whether or not the frame was successfully grabbed and decoded, as
well as the frame itself in the form of a numpy array, `frame`. On **line 24**,
we check if the frame was not successfully grabbed or if the user pressed the
&#8220;q&#8221; key to quit and exit the program. In either case, we halt
execution of the while loop with `break`. Barring either condition, we continue
by simultaneously obtaining and overlaying the current &#8220;speed&#8221; of
the loop (in iterations per second) in the lower-left corner of the frame on
**line 27**. Finally, the frame is displayed on the screen on **line 28** with a
call to `cv2.imshow()`, and the iteration count is incremented on **line 29**.

What do the results look like for both a webcam and a video file? These are the
values I got on my hardware:

{{< figure src=/img/no_thread.jpg >}}

Reading from a webcam, the while loop executed about 28 iterations/second.
Reading from an AVI file, about 240 iterations/second. These will serve as our
baseline values.

# A separate thread for getting video frames

What happens if we move the task of getting frames from the webcam or video file
into a separate thread? To do this, we&#8217;ll first define a class called
`VideoGet` in a file named `VideoGet.py`,
[which can be found on Github](https://github.com/nrsyed/computer-vision/blob/master/multithread/VideoGet.py).

{{< highlight python "linenos=true" >}}
from threading import Thread
import cv2

class VideoGet:
    """
    Class that continuously gets frames from a VideoCapture object
    with a dedicated thread.
    """

    def __init__(self, src=0):
        self.stream = cv2.VideoCapture(src)
        (self.grabbed, self.frame) = self.stream.read()
        self.stopped = False
{{< / highlight >}}

We import the `threading` module, which will allow us to spawn new threads. In
the class `__init__()` method, we initialize an OpenCV `VideoCapture` object and
read the first frame. We also create an attribute called `stopped` to act as a
flag, indicating that the thread should stop grabbing new frames.

{{< highlight python "linenos=true,linenostart=15" >}}
def start(self):
    Thread(target=self.get, args=()).start()
    return self

def get(self):
    while not self.stopped:
        if not self.grabbed:
            self.stop()
        else:
            (self.grabbed, self.frame) = self.stream.read()

def stop(self):
    self.stopped = True
{{< / highlight >}}

The `start()` method creates and starts the thread on **line 16**. The thread
executes the `get()` function, defined on **line 19**. This function
continuously runs a while loop that reads a frame from the video stream and
stores it in the class instance&#8217;s `frame` attribute, as long as the
`stopped` flag isn&#8217;t set. If a frame is not successfully read (which might
happen if the webcam is disconnected or the end of the video file is reached),
the `stopped` flag is set True by calling the `stop()` function, defined on
**line 26**.

We&#8217;re now ready to implement this class. Returning to the file
[thread_demo.py](https://github.com/nrsyed/computer-vision/blob/master/multithread/thread_demo.py), we define a function `threadVideoGet()`, which
will use the `VideoGet` object above to read video frames in a separate thread
while the main thread displays the frames.

{{< highlight python "linenos=true,linenostart=31" >}}
def threadVideoGet(source=0):
    """
    Dedicated thread for grabbing video frames with VideoGet object.
    Main thread shows video frames.
    """

    video_getter = VideoGet(source).start()
    cps = CountsPerSec().start()

    while True:
        if (cv2.waitKey(1) == ord("q")) or video_getter.stopped:
            video_getter.stop()
            break

        frame = video_getter.frame
        frame = putIterationsPerSec(frame, cps.countsPerSec())
        cv2.imshow("Video", frame)
        cps.increment()
{{< / highlight >}}

The function is pretty similar to the `noThreading()` function discussed in the
previous section, except we initialize the `VideoGet` object and start the
second thread on **line 37**. On **lines 41-43** of the main while loop, we
check to see if the user has pressed the &#8220;q&#8221; key or if the
`VideoGet` object&#8217;s `stopped` attribute has been set True, in which case
we halt the while loop. Otherwise, the loop gets the frame currently stored in
the `VideoGet` object on **line 45**, then proceeds to process and display it as
in the `noThreading()` function.

How does the function perform on a webcam video stream and on a video file?

{{< figure src=/img/thread_get.jpg >}}

Quite the difference compared to the single-thread case! With the frame-getting
task in a separate thread, the while loop executed 545 iterations/second for a
webcam and 585 iterations/second for a video file. At this point, it&#8217;s
important to note that these values _do not_ correspond to framerate or FPS. The
video FPS is largely limited by the camera hardware and/or the speed with which
each frame can be grabbed and decoded. The iterations per second simply show
that the main while loop is able to execute more quickly when some of the video
I/O is off-loaded to another thread. It demonstrates that the main thread can do
more processing when it isn&#8217;t also responsible for reading frames.

# A separate thread for showing video frames

To move the task of displaying video frames to a separate thread, we follow a
procedure similar to the last section and define a class called `VideoShow` in a
file named `VideoShow.py`, which, as before,
[can be found on Github](https://github.com/nrsyed/computer-vision/blob/master/multithread/VideoShow.py). The class definition begins just like the `VideoGet`
class:

{{< highlight python "linenos=true" >}}
from threading import Thread
import cv2

class VideoShow:
    """
    Class that continuously shows a frame using a dedicated thread.
    """

    def __init__(self, frame=None):
        self.frame = frame
        self.stopped = False
{{< / highlight >}}


This time, the new thread calls the `show()` method, defined on **line 17**.

{{< highlight python "linenos=true,linenostart=13" >}}
def start(self):
    Thread(target=self.show, args=()).start()
    return self

def show(self):
    while not self.stopped:
        cv2.imshow("Video", self.frame)
        if cv2.waitKey(1) == ord("q"):
            self.stopped = True

def stop(self):
    self.stopped = True
{{< / highlight >}}

Note that checking for user input, on **line 20**, is achieved in the separate
thread instead of the main thread, since the OpenCV `waitKey()` function
doesn&#8217;t necessarily play well in multithreaded applications and I found it
didn&#8217;t work properly when placed in the main thread. Once again, returning
to
[thread_demo.py](https://github.com/nrsyed/computer-vision/blob/master/multithread/thread_demo.py), we define a function called
`threadVideoShow()`.

{{< highlight python "linenos=true,linenostart=50" >}}
def threadVideoShow(source=0):
    """
    Dedicated thread for showing video frames with VideoShow object.
    Main thread grabs video frames.
    """

    cap = cv2.VideoCapture(source)
    (grabbed, frame) = cap.read()
    video_shower = VideoShow(frame).start()
    cps = CountsPerSec().start()

    while True:
        (grabbed, frame) = cap.read()
        if not grabbed or video_shower.stopped:
            video_shower.stop()
            break

        frame = putIterationsPerSec(frame, cps.countsPerSec())
        video_shower.frame = frame
        cps.increment()
{{< / highlight >}}

As before, this function is similar to the `noThreading()` function, except we
initialize a `VideoShow` object, which I&#8217;ve named `video_shower`
(that&#8217;s &#8220;shower&#8221; as in &#8220;something that shows,&#8221; not
&#8220;shower&#8221; as in &#8220;water and shampoo&#8221;) and start the new
thread on **line 58**. **Line 63** checks indirectly if the user has pressed
&#8220;q&#8221; to quit the program, since the `VideoShow` object is actually
checking for user input and setting its `stopped` attribute to True in the event
that the user presses &#8220;q&#8221;. **Line 68** sets the `VideoShow`
object&#8217;s `frame` attribute to the current frame.

And the result?

{{< figure src=/img/thread_show.jpg >}}

This is interesting. The webcam performs at 30 iterations/second, only slightly
faster than the 28 obtained in the case of a single thread. However, the video
file performs at ~400 iterations/second&#8212;faster than its single-thread
counterpart (240 iterations/second) but slower than the video file with video
reading in a separate thread (585 iterations/second). This suggests that
there&#8217;s a fundamental difference between reading from a camera stream and
from a file, and that the primary bottleneck for a camera stream is reading and
decoding video frames.

# Separate threads for both getting and showing video frames

Finally, we&#8217;ll implement a function named `threadBoth()` in
`thread_demo.py` that creates a thread for getting video frames via the
`VideoGet` class and another thread for displaying frames via the `VideoShow`
class, with the main thread existing to process and pass frames between the two
objects.

{{< highlight python "linenos=true,linenostart=71" >}}
def threadBoth(source=0):
    """
    Dedicated thread for grabbing video frames with VideoGet object.
    Dedicated thread for showing video frames with VideoShow object.
    Main thread serves only to pass frames between VideoGet and
    VideoShow objects/threads.
    """

    video_getter = VideoGet(source).start()
    video_shower = VideoShow(video_getter.frame).start()
    cps = CountsPerSec().start()

    while True:
        if video_getter.stopped or video_shower.stopped:
            video_shower.stop()
            video_getter.stop()
            break

        frame = video_getter.frame
        frame = putIterationsPerSec(frame, cps.countsPerSec())
        video_shower.frame = frame
        cps.increment()
{{< / highlight >}}

This function is a mixture of the `threadVideoGet()` and `threadVideoShow()`
functions, which turns out to have a very interesting result:

{{< figure src=/img/thread_both.jpg >}}

This seems to be at odds with the previous conclusion, which suggested that
reading frames was the primary bottleneck for the webcam. For whatever reason,
the combination of putting both frame-reading and frame-display in dedicated
threads bumps the performance in both cases up to a whopping ~48000
iterations/second. Not being as well-versed in multithreading as I&#8217;d like
to be, I can&#8217;t quite explain this result. Regardless, it appears fairly
clear that using multithreading for video I/O can free up considerable resources
for performing other image processing tasks.
