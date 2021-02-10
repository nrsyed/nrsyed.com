---
title: A PyTorch implementation of YOLOv3 for real-time object detection (part 5)
author: Najam Syed
type: post
date: 2020-09-21T04:24:11+00:00
url: /2020/09/20/a-pytorch-implementation-of-yolov3-for-real-time-object-detection-part-5/
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
  - neural networks
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
- [Part 4 (Real-time multithreaded detection)][4]
- Part 5 (Command-line interface)

The last several posts covered the theory behind YOLOv3, as well as the code
responsible for performing inference on an image and real-time detection in a
webcam stream. In this post, we&#8217;ll tackle the command line interface that
ties it all together and which was used to produce the video from the first post
(included again below for good measure).

{{< youtube wyKoi5Hc8WY >}}

# Command-line interface

The command-line interface (CLI) is defined in the main() function of
[__main\_\_.py](https://github.com/nrsyed/pytorch-yolov3/blob/master/yolov3/__main__.py).
They&#8217;re described in more detail below.

## Input source arguments

The input source can be 1) a webcam or video stream, 2) an image or images, or
3) a video file. One and only one of these three options must be provided.

* `--cam, -C [cam_id]`: This option performs detection on the stream from a
webcam or video stream. By default, it uses video capture device id 0 (if only
one webcam is plugged in or you&#8217;re using a laptop with a built-in webcam,
its device id is usually 0) if no value is supplied, i.e., `-C`. However, the
numeric device id or a path to a video stream (e.g., the path to an RTSP stream)
can optionally be specified as an argument, e.g., `-C 1`.
* `--image, -I <path>`: This option has one required argument&#8212;a path to an
image file or to a directory of image files, e.g.,
`-I /path/to/image/directory`.
* `--video, -V <path>`: This option has one required argument&#8212;a path to a
video file, e.g., `-V /path/to/video.mp4`.

## Model arguments

There are several model-related arguments, some of which are required and others
optional.

* `--config, -c <path>` (**required**): The path to the Darknet config file in
which the network architecture is defined, e.g., `-c models/yolov3.cfg`.
* `--device, -d <device>` (**optional**): The PyTorch device on which to run the
network (default &#8220;cuda&#8221;). This should be a string that can be parsed
by
[torch.device](https://pytorch.org/docs/stable/tensor_attributes.html#torch-device). This can be, for example, &#8220;cpu&#8221; to run on the CPU
or &#8220;cuda&#8221; to run on the primary CUDA device/GPU. The CUDA device/GPU
can be specified using &#8220;cuda:0&#8221;, &#8220;cuda:1&#8221;,
&#8220;cuda:2&#8221;, etc. to run on GPU 0 or GPU 1 or GPU 2, respectively, if
you have multiple GPUs. Note that the GPU device id as seen by the OS (which can
be determined from nvidia-smi) may not be the same as the device id as seen by
PyTorch. For example, I have two GPUs in my system: an RTX 2080 Ti and a GTX
Titan X. nvidia-smi reports the following information about these GPUs:
{{< highlight plain >}}
+-----------------------------------------------------------------------------+
| NVIDIA-SMI 435.21       Driver Version: 435.21       CUDA Version: 10.1     |
|-------------------------------+----------------------+----------------------+
| GPU  Name        Persistence-M| Bus-Id        Disp.A | Volatile Uncorr. ECC |
| Fan  Temp  Perf  Pwr:Usage/Cap|         Memory-Usage | GPU-Util  Compute M. |
|===============================+======================+======================|
|   0  GeForce RTX 208...  Off  | 00000000:2D:00.0  On |                  N/A |
| 15%   55C    P0    63W / 250W |   1041MiB / 11011MiB |      1%      Default |
+-------------------------------+----------------------+----------------------+
|   1  GeForce GTX TIT...  Off  | 00000000:2E:00.0 Off |                  N/A |
| 22%   31C    P8    14W / 250W |      1MiB / 12212MiB |      0%      Default |
+-------------------------------+----------------------+----------------------+
{{< / highlight >}}

Here, we can see that RTX 2080 Ti is GPU 0 and the GTX Titan X is GPU 1.
However, the GPU ids as seen by PyTorch may not necessarily match. To be sure
you&#8217;re running on the correct GPU, you can supply the `-v` or `--verbose`
option, which will print the name of the GPU, but if you have multiple identical
GPUs, you may be better off using a tool like
[nvtop](https://github.com/Syllo/nvtop) to check GPU usage. </li>

* `--iou-thresh, -i <iou>` (**optional**): The IOU threshold is a value in the
range (0, 1] that sets the bounding box overlap for two detections to be
considered duplicates. This value is ultimately passed to the non-max
suppression function. By default, it&#8217;s set to 0.3.
* `--class-names, -n <path>` (**optional**): The path to the text file of
newline-separate class names, e.g., `-n models/coco.names`. The contents of this
file are simply used to display the correct name above each bounding box. If
omitted, the class index (an integer from 0 to `num_classes - 1`) is displayed
instead.
* `--prob-thresh, -p <prob>` (**optional**): The detection probability
threshold&#8212;a float between [0, 1]. Detections below the given probability
will be ignored. By default, this is set to 0.05 to filter out low confidence
predictions.
* `--weights, -w <path>` (**required**): The path to the model weights, e.g.,
`-w models/yolov3.weights`. </ul>
## Output-related arguments

Lastly, there are several arguments that control what information or files are
output by the detection pipeline.

* `--output, -o <path>` (**optional**): Path to output .mp4 video file.
* `--show-fps` (**optional**): Show the current framerate (frames per second) on
the displayed video.
* `--verbose, -v` (**optional**): Print diagnostic information to the terminal
while running the detection pipeline.
## Setting up the network and detector

We use argparse to process these command line arguments, then initialize the
network and set some basic parameters starting on **line 106**
[of the current version of \_\_main__.py](https://github.com/nrsyed/pytorch-yolov3/blob/dd8344d7620fde09610f1ac2fadf7bcf88a9c6f1/yolov3/__main__.py#L106).

{{< highlight python "linenos=true,linenostart=106" >}}
    device = args["device"]
    if device.startswith("cuda") and not torch.cuda.is_available():
        warnings.warn(
            "CUDA not available; falling back to CPU. Pass `-d cpu` or ensure "
            "compatible versions of CUDA and pytorch are installed.",
            RuntimeWarning, stacklevel=2
        )
        device = "cpu"

    net = yolov3.Darknet(args["config"], device=device)
    net.load_weights(args["weights"])
    net.eval()

    if device.startswith("cuda"):
        net.cuda(device=device)

    if args["verbose"]:
        if device == "cpu":
            device_name = "CPU"
        else:
            device_name = torch.cuda.get_device_name(net.device)
        print(f"Running model on {device_name}")

    class_names = None
    if args["class_names"] is not None and os.path.isfile(args["class_names"]):
        with open(args["class_names"], "r") as f:
            class_names = [line.strip() for line in f.readlines()]
{{< / highlight >}}

On **line 107**, we check if CUDA is available (if it was specified). If it
isn&#8217;t, we tell the user and utilize the CPU instead. If CUDA was specified
but is not available, this can either mean CUDA isn&#8217;t installed on the
system, or that PyTorch was compiled without CUDA, or that the PyTorch version
doesn&#8217;t support the version of CUDA installed on the system. On **lines
115-117**, we instantiate the Darknet class and load the network weights (see
previous posts), then set the network to eval mode&#8212;this is a PyTorch
[torch.nn.Module method](https://pytorch.org/docs/stable/generated/torch.nn.Module.html#torch.nn.Module.eval) that should be called for inference (as opposed to
training). On **lines 119-120**, we also call
[torch.nn.Module.cuda()](https://pytorch.org/docs/stable/generated/torch.nn.Module.html#torch.nn.Module.cuda) if the model is to be loaded on the GPU and not the
CPU. **Lines 122-127** print information on the device being used, e.g., GPU, if
the verbose option was supplied. Finally, we load the list of class names on
**lines 129-132** if a path to a file was given.

{{< highlight python "linenos=true,linenostart=134" >}}
    if args["image"]:
        source = "image"
    elif args["video"]:
        source = "video"
    else:
        source = "cam"
        # If --cam argument is str representation of an int, interpret it as
        # an int device ID. Else interpret as a path to a video capture stream.
        if isinstance(args["cam"], str) and args["cam"].isdigit():
            args["cam"] = int(args["cam"])
{{< / highlight >}}

On **lines 134-143**, we set the value for the input source.

{{< highlight python "linenos=true,linenostart=145" >}}
    if source == "image":
        if os.path.isdir(args["image"]):
            image_dir = args["image"]
            fnames = os.listdir(image_dir)
        else:
            image_dir, fname = os.path.split(args["image"])
            fnames = [fname]

        images = []
        for fname in fnames:
            images.append(cv2.imread(os.path.join(image_dir, fname)))

        # TODO: batch images
        results = []
        for image in images:
            results.extend(
                yolov3.inference(
                    net, image, device=device, prob_thresh=args["prob_thresh"],
                    nms_iou_thresh=args["iou_thresh"]
                )
            )

        for image, (bbox_xywh, _, class_idx) in zip(images, results):
            yolov3.draw_boxes(
                image, bbox_xywh, class_idx=class_idx, class_names=class_names
            )
            cv2.imshow("YOLOv3", image)
            cv2.waitKey(0)
{{< / highlight >}}

**Lines 145-172** handle the case where the input source is an image or a
directory of images. The images are loaded into memory and each image is
processed sequentially on **lines 158-165**. In the future, I may add the option
to run all the images in a single batch&#8212;this can provide a performance
boost over running the images one by one, but also utilizes more GPU memory (or
CPU memory if not using CUDA). Finally, **lines 167-172** draw bounding boxes on
each image and display them one at a time.

{{< highlight python "linenos=true,linenostart=173" >}}
    else:
        frames = None
        if args["output"]:
            frames = []
{{< / highlight >}}

Both the webcam and video input sources are handled in the same top-level else
block encompassed by **lines 173-210**. The actual detection functionality for
these cases was discussed in [the previous post][4] and is found in
[inference.py](https://github.com/nrsyed/pytorch-yolov3/blob/master/yolov3/inference.py).
On lines **174-176**, we initialize a list called `frames` if
the resulting video is to be written to an mp4 output file. Each processed frame
will be appended to `frames` by inference.detect_in_cam() or
inference.detect_in_video(). After the function has completed, we&#8217;ll write
the frames to a video using the OpenCV
[VideoWriter](https://docs.opencv.org/2.4/modules/highgui/doc/reading_and_writing_images_and_video.html?highlight=imwrite#videowriter) class.

The VideoWriter class allows us to write one frame to a video file at a time,
which begs the question: why have I chosen to store the frames in a list and
then write them all at the end instead of writing them as they&#8217;re
processed? When I tried the latter approach, I found that processing time
increased dramatically and severely reduced performance, even when I put the
video writing functionality into a separate thread (in addition to the video
reading and showing threads). For whatever reason, I couldn&#8217;t leverage
multithreading to concurrently read, display, and write frames, which leads me
to believe there&#8217;s something going on under the hood that will require a
deeper dive for me to understand. For now, I&#8217;ve opted to stick with the
list because, even though it has the disadvantage of consuming an
ever-increasing amount of RAM as it grows, this memory usage is relatively
small. Recording for a longer duration (on the order of hours) would require a
more robust solution.

{{< highlight python "linenos=true,linenostart=178" >}}
        if source == "cam":
            start_time = time.time()

            # Wrap in try/except block so that output video is written
            # even if an error occurs while streaming webcam input.
            try:
                yolov3.detect_in_cam(
                    net, cam_id=args["cam"], device=device,
                    prob_thresh=args["prob_thresh"],
                    nms_iou_thresh=args["iou_thresh"],
                    class_names=class_names, show_fps=args["show_fps"],
                    frames=frames
                )
            except Exception as e:
                raise e
            finally:
                if args["output"] and frames:
                    # Get average FPS and write output at that framerate.
                    fps = 1 / ((time.time() - start_time) / len(frames))
                    write_mp4(frames, fps, args["output"])
        elif source == "video":
            yolov3.detect_in_video(
                net, filepath=args["video"], device=device,
                prob_thresh=args["prob_thresh"],
                nms_iou_thresh=args["iou_thresh"], class_names=class_names,
                frames=frames
            )
            if args["output"] and frames:
                # Get input video FPS and write output video at same FPS.
                cap = cv2.VideoCapture(args["video"])
                fps = cap.get(cv2.CAP_PROP_FPS)
                cap.release()
                write_mp4(frames, fps, args["output"])
{{< / highlight >}}

Webcam input is handled on **lines 178-197**. The detection function is wrapped
in a try/except/finally block so that the output video is written even if the
detect_in_cam() function encounters an error and exits unexpectedly. The video
file input is handled on **lines 198-210**. In both cases, writing an output
video file is handled by the write_mp4() function, which is defined
[earlier in the same file](https://github.com/nrsyed/pytorch-yolov3/blob/dd8344d7620fde09610f1ac2fadf7bcf88a9c6f1/yolov3/__main__.py#L13).

{{< highlight python "linenos=true,linenostart=13" >}}
def write_mp4(frames, fps, filepath):
    """
    Write provided frames to an .mp4 video.
    Args:
        frames (list): List of frames (np.ndarray).
        fps (int): Framerate (frames per second) of the output video.
        filepath (str): Path to output video file.
    """
    if not filepath.endswith(".mp4"):
        filepath += ".mp4"

    h, w = frames[0].shape[:2]

    writer = cv2.VideoWriter(
        filepath, cv2.VideoWriter_fourcc(*"mp4v"), int(fps), (w, h)
    )

    for frame in frames:
        writer.write(frame)
    writer.release()
{{< / highlight >}}

This function is fairly straightforward. **Line 24** gets the output video
dimensions from the first frame in `frames`. The OpenCV VideoWriter object is
instantiated by providing it the path to the output video, a
[FourCC code](https://en.wikipedia.org/wiki/FourCC) corresponding to the mp4 encoding, the output video framerate,
and the output video dimensions.

# Conclusion

With this discussion of the command line interface, this series of posts comes
to an end. We&#8217;ve delved into the fundamentals of YOLOv3, the PyTorch
implementation of the network, utilizing the network for inference, and the
multithreaded approach to real-time detection. This approach can generalize to
any detection backend, not just YOLOv3, and I&#8217;m sure I&#8217;ll revisit
this pipeline again in the future.

[1]: {{< ref "2020-04-28-a-pytorch-implementation-of-yolov3-for-real-time-object-detection-part-1.md" >}}
[2]: {{< ref "2020-05-13-a-pytorch-implementation-of-yolov3-for-real-time-object-detection-part-2.md" >}}
[3]: {{< ref "2020-06-30-a-pytorch-implementation-of-yolov3-for-real-time-object-detection-part-3.md" >}}
[4]: {{< ref "2020-09-11-a-pytorch-implementation-of-yolov3-for-real-time-object-detection-part-4.md" >}}
