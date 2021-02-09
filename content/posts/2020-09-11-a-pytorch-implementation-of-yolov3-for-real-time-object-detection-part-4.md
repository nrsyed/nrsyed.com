---
title: A PyTorch implementation of YOLOv3 for real-time object detection (part 4)
author: Najam Syed
type: post
date: 2020-09-12T04:24:54+00:00
url: /2020/09/11/a-pytorch-implementation-of-yolov3-for-real-time-object-detection-part-4/
categories:
  - Algorithms
  - Computer Vision
  - Deep Learning
  - Machine Learning
tags:
  - algorithms
  - computer vision
  - deep learning
  - machine learning
  - multithreading
  - neural networks
  - numerical methods
  - object detection
  - OpenCV
  - Python
  - yolo
  - yolov3

---
**Link to code**:
[https://github.com/nrsyed/pytorch-yolov3](https://github.com/nrsyed/pytorch-yolov3)

- [Part 1 (Background)][1]
- [Part 2 (Initializing the network)][2]
- [Part 3 (Inference)][3]
- Part 4 (Real-time multithreaded detection)
- [Part 5 (Command-line interface)][4]

In this post, we extend the inference code discussed in the last post and
demonstrate how to incorporate it into a multithreaded pipeline to perform
detection and display the results in real time on a webcam stream or video. The
functions and classes we&#8217;ll use to do so are also found in
[inference.py](https://github.com/nrsyed/pytorch-yolov3/blob/master/yolov3/inference.py).

# Real-time detection in a webcam stream

Let&#8217;s look at the definition of the function
[detect_in_cam()](https://github.com/nrsyed/pytorch-yolov3/blob/dd8344d7620fde09610f1ac2fadf7bcf88a9c6f1/yolov3/inference.py#L435), which, as the name implies, we&#8217;ll use to detect
objects in a webcam stream.

{{< highlight python "linenos=true,linenostart=435" >}}
def detect_in_cam(
    net, cam_id=0, device="cuda", prob_thresh=0.05, nms_iou_thresh=0.3,
    class_names=None, show_fps=False, frames=None
):
    """
    Run and display real-time inference on a webcam stream.

    Performs inference on a webcam stream, draw bounding boxes on the frame,
    and display the resulting video in real time.

    Args:
        net (torch.nn.Module): Instance of network class.
        cam_id (int): Camera device id.
        device (str): Device for inference (eg, "cpu", "cuda").
        prob_thresh (float): Detection probability threshold.
        nms_iou_thresh (float): NMS IOU threshold.
        class_names (list): List of all model class names in order.
        show_fps (bool): Display current frames processed per second.
        frames (list): Optional list to populate with frames being displayed;
            can be used to write or further process frames after this function
            completes. Because mutables (like lists) are passed by reference
            and are modified in-place, this function has no return value.
    """
{{< / highlight >}}

The inputs to the function on **lines 436-437** are defined in the subsequent
docstring. Several of them are either self-explanatory or were discussed in the
previous post (as inputs to the inference() function). The `class_names`
argument is a list of class names corresponding to the class indices
(`class_idx`) from the last post. The optional `frames` argument is used if the
frames (with bounding boxes drawn over the original webcam stream, etc.) are
needed by the calling code&#8212;for example, to write the result to a video
file (this is what was used to create
[the YouTube demonstration video](https://www.youtube.com/watch?v=wyKoi5Hc8WY)).
`frames` should be a list provided by the
caller. Each frame will be appended to the list as the webcam stream is
processed. Since lists are passed by reference, changes made to the list in this
function are also visible to the calling code.

{{< highlight python "linenos=true,linenostart=458" >}}
    video_getter = VideoGetter(cam_id).start()
    video_shower = VideoShower(video_getter.frame, "YOLOv3").start()

    # Number of frames to average for computing FPS.
    num_fps_frames = 30
    previous_fps = deque(maxlen=num_fps_frames)
{{< / highlight >}}

On **lines 458-459**, we instantiate the VideoGetter and VideoShower classes,
which are defined earlier in inference.py. We&#8217;ll get to the definitions of
these classes shortly. For now, all you need to know is that they enable us to
asynchronously get (hence Video<u>Get</u>ter) frames from the webcam and show
(hence Video<u>Show</u>er) the processed frames with detection bounding boxes in
separate threads. Utilizing multithreading for these I/O-bound tasks
significantly speeds up our pipeline. **Lines 462-463** initialize the variables
we&#8217;ll use to compute the running average FPS of the pipeline&#8212;this
will allow us to measure just how &#8220;real time&#8221; it is. For this, we
use a
[deque](https://docs.python.org/3/library/collections.html#collections.deque)
that keeps track of the processing time for the last 30 frames.

{{< highlight python "linenos=true,linenostart=465" >}}
    while True:
        loop_start_time = time.time()

        if video_getter.stopped or video_shower.stopped:
            video_getter.stop()
            video_shower.stop()
            break

        frame = video_getter.frame
        bbox_tlbr, _, class_idx = inference(
            net, frame, device=device, prob_thresh=prob_thresh,
            nms_iou_thresh=nms_iou_thresh
        )[0]
        draw_boxes(
            frame, bbox_tlbr, class_idx=class_idx, class_names=class_names
        )

        if show_fps:
            cv2.putText(
                frame,  f"{int(sum(previous_fps) / num_fps_frames)} fps",
                (2, 20), cv2.FONT_HERSHEY_COMPLEX_SMALL, 0.9,
                (255, 255, 255)
            )

        video_shower.frame = frame
        if frames is not None:
            frames.append(frame)

        previous_fps.append(int(1 / (time.time() - loop_start_time)))
{{< / highlight >}}

The rest of the function comprises a while loop that grabs the current frame
from the webcam on **line 473**, runs inference on the frame (**lines
474-477**), draws the resulting bounding boxes and class names (or class indices
if class names were not provided) on the frame (**lines 478-480**), draws the
current processing FPS on the frame if desired (**lines 482-487**), and
finally displays the frame on **line 489**. On **lines 490-491**, the resulting
frame is appended to the `frames` list if it was provided. Finally, on **line 493**,
the framerate for the current loop iteration, which is the inverse of the
processing time for the frame, is appended to the deque.

## Multithreading to get and display frames

One of the more popular posts I&#8217;ve written is on [multithreading with
OpenCV to improve performance][5]. As the comments on that post point out, there
were a couple issues with that implementation and my method of evaluation. These
issues have been corrected in this updated implementation (and which will
probably be evaluated in more detail in a future post). First, here&#8217;s the
code for the
[VideoGetter class](https://github.com/nrsyed/pytorch-yolov3/blob/dd8344d7620fde09610f1ac2fadf7bcf88a9c6f1/yolov3/inference.py#L11)
used to read frames from the webcam.

{{< highlight python "linenos=true,linenostart=11" >}}
class VideoGetter():
    def __init__(self, src=0):
        """
        Class to read frames from a VideoCapture in a dedicated thread.
        Args:
            src (int|str): Video source. Int if webcam id, str if path to file.
        """
        self.cap = cv2.VideoCapture(src)
        self.grabbed, self.frame = self.cap.read()
        self.stopped = False

    def start(self):
        threading.Thread(target=self.get, args=()).start()
        return self

    def get(self):
        """
        Method called in a thread to continually read frames from `self.cap`.
        This way, a frame is always ready to be read. Frames are not queued;
        if a frame is not read before `get()` reads a new frame, previous
        frame is overwritten.
        """
        while not self.stopped:
            if not self.grabbed:
                self.stop()
            else:
                self.grabbed, self.frame = self.cap.read()

    def stop(self):
        self.stopped = True
{{< / highlight >}}

The __init\_\_() method is fairly straightforward. It instantiates an OpenCV
VideoCapture object and initializes its return values (stored as instance
variables) by calling its read() method. We also initialize the boolean instance
variable `self.stopped` that can be used to determine if the thread is still
running.
The thread itself is started in the start() method on **line 22**; note
that we&#8217;re making use of the
[threading package](https://docs.python.org/3/library/threading.html),
which is part of Python&#8217;s standard library. The
thread runs the VideoGetter.get() method defined on **lines 26-37**. All it does
is continuously read the next frame from the VideoCapture object and store it in
self.frame such that a frame is always available. Note that, as the get()
method&#8217;s docstring indicates, frames are not stored in a queue&#8212;this
means that the previous frame is always overwritten. This was an intentional
design choice to ensure that we&#8217;re always reading the most recent frame,
even if previous frames were missed due to the processing taking too much time.

Below is the code for the
[VideoShower class](https://github.com/nrsyed/pytorch-yolov3/blob/dd8344d7620fde09610f1ac2fadf7bcf88a9c6f1/yolov3/inference.py#L44)
(that&#8217;s shower as in &#8220;show-er&#8221; and not
as in &#8220;rain shower&#8221;):

{{< highlight python "linenos=true,linenostart=44" >}}
class VideoShower():
    def __init__(self, frame=None, win_name="Video"):
        """
        Class to show frames in a dedicated thread.
        Args:
            frame (np.ndarray): (Initial) frame to display.
            win_name (str): Name of `cv2.imshow()` window.
        """
        self.frame = frame
        self.win_name = win_name
        self.stopped = False

    def start(self):
        threading.Thread(target=self.show, args=()).start()
        return self

    def show(self):
        """
        Method called within thread to show new frames.
        """
        while not self.stopped:
            # We can actually see an ~8% increase in FPS by only calling
            # cv2.imshow when a new frame is set with an if statement. Thus,
            # set `self.frame` to None after each call to `cv2.imshow()`.
            if self.frame is not None:
                cv2.imshow(self.win_name, self.frame)
                self.frame = None

            if cv2.waitKey(1) == ord("q"):
                self.stopped = True

    def stop(self):
        cv2.destroyWindow(self.win_name)
        self.stopped = True
{{< / highlight >}}

The class&#8217;s __init\_\_() method takes two optional arguments: `frame` (a
frame with which to initialize the class) and `win_name` (the name of the OpenCV
window in which the frame will be displayed). OpenCV relies on
[named windows](https://docs.opencv.org/2.4/modules/highgui/doc/user_interface.html?highlight=namedwindow#namedwindow)
to determine which window to update. Like the VideoGetter
class, it also has a start() method to start the thread used to show frames. The
show() method on **lines 61-74** is where most of the magic happens in a while
loop that continuously displays the current frame using
[OpenCV’s imshow() function](https://docs.opencv.org/2.4/modules/highgui/doc/user_interface.html#imshow).
As the method&#8217;s docstring indicates,
the class&#8217;s `self.frame` attribute is set to None after the call to
imshow(). This is because the call to imshow() is relatively computationally
expensive and by only running it when the calling code has manually set
`self.frame` to an actual frame, we can realize a performance increase. Also
note that that the loop monitors keypresses and that when the &#8220;q&#8221;
key is pressed, stops the loop.

# Detection in a video file

The
[detect_in_video()](https://github.com/nrsyed/pytorch-yolov3/blob/dd8344d7620fde09610f1ac2fadf7bcf88a9c6f1/yolov3/inference.py#L496)
function found in inference.py is used to run detection on
the frames of a video file. Functionally speaking, the detect_in_cam() and
detect_in_video() functions do the same thing (instantiate a VideoCapture
object, read frames from it, and run inference on those frames). The differences
are mainly stylistic in nature. The detect_in_video() function does not utilize
multithreading or the VideoGetter and VideoShower classes described above, and
it makes the video showing/displaying functionality optional. This is based on
the assumption that, with a video, we want to process every single frame; as we
learned above, the VideoGetter class might result in frames being skipped if the
processing time for a frame exceeds the time required to read the next frame
from the OpenCV VideoCapture object. It&#8217;s also based on the assumption
that, with a video file, there are no real-time constraints&#8212;in other
words, I&#8217;ve assumed that the goal is to process all frames regardless of
how long it takes.

The code for the function is below.

{{< highlight python "linenos=true,linenostart=496" >}}
def detect_in_video(
    net, filepath, device="cuda", prob_thresh=0.05, nms_iou_thresh=0.3,
    class_names=None, frames=None, show_video=True
):
    """
    Run and optionally display inference on a video file.
    Performs inference on a video, draw bounding boxes on the frame,
    and optionally display the resulting video.
    Args:
        net (torch.nn.Module): Instance of network class.
        filepath (str): Path to video file.
        device (str): Device for inference (eg, "cpu", "cuda").
        prob_thresh (float): Detection probability threshold.
        nms_iou_thresh (float): NMS IOU threshold.
        cam_id (int): Camera device id.
        class_names (list): List of all model class names in order.
        frames (list): Optional list to populate with frames being displayed;
            can be used to write or further process frames after this function
            completes. Because mutables (like lists) are passed by reference
            and are modified in-place, this function has no return value.
        show_video (bool): Whether to display output while processing.
    """
    cap = cv2.VideoCapture(filepath)

    while True:
        grabbed, frame = cap.read()
        if not grabbed:
            break

        bbox_tlbr, _, class_idx = inference(
            net, frame, device=device, prob_thresh=prob_thresh,
            nms_iou_thresh=nms_iou_thresh
        )[0]
        draw_boxes(
            frame, bbox_tlbr, class_idx=class_idx, class_names=class_names
        )

        if frames is not None:
            frames.append(frame)

        if show_video:
            cv2.imshow("YOLOv3", frame)
            if cv2.waitKey(1) == ord("q"):
                break

    cap.release()
    cv2.destroyAllWindows()
{{< / highlight >}}

In practice, there&#8217;s nothing stopping you from providing a webcam id for
the detect_in_cam() function&#8217;s `filepath` argument or, conversely, a path
to a video file for the `cam_id` argument of the detect_in_cam() function. In
fact, doing so might be an informative exercise.

# Summary

This post covered the functions used to run inference on a video file or webcam
stream for real time detection. In the next post, we&#8217;ll examine the
command line interface and the top-level code that actually calls these
functions.

[1]: {{< ref "2020-04-28-a-pytorch-implementation-of-yolov3-for-real-time-object-detection-part-1.md" >}}
[2]: {{< ref "2020-05-13-a-pytorch-implementation-of-yolov3-for-real-time-object-detection-part-2.md" >}}
[3]: {{< ref "2020-06-30-a-pytorch-implementation-of-yolov3-for-real-time-object-detection-part-3.md" >}}
[4]: {{< ref "2020-09-20-a-pytorch-implementation-of-yolov3-for-real-time-object-detection-part-5.md" >}}
[5]: {{< ref "2018-07-05-multithreading-with-opencv-python-to-improve-video-processing-performance.md" >}}
