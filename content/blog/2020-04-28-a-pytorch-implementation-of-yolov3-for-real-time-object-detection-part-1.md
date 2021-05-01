---
title: A PyTorch implementation of YOLOv3 for real-time object detection (part 1)
author: Najam Syed
type: post
date: 2020-04-29T03:24:47+00:00
url: /2020/04/28/a-pytorch-implementation-of-yolov3-for-real-time-object-detection-part-1/
categories:
  - Algorithms
  - Computer Vision
  - Deep Learning
  - Machine Learning
tags:
  - K-means clustering
  - neural networks
  - object detection
  - Python
  - yolo

---
**Link to code**:
[https://github.com/nrsyed/pytorch-yolov3](https://github.com/nrsyed/pytorch-yolov3)

- Part 1 (Background)
- [Part 2 (Initializing the network)][1]
- [Part 3 (Inference)][2]
- [Part 4 (Real-time multithreaded detection)][3]
- [Part 5 (Command-line interface)][4]

[YOLOv3](https://pjreddie.com/darknet/yolo/), the third iteration of Joseph Redmon et al&#8217;s YOLO (&#8220;You
Only Look Once&#8221;)
[Darknet-based](https://pjreddie.com/darknet/) object detection neural network architecture, was developed
and published in 2018
([link to paper](https://arxiv.org/abs/1804.02767)). The defining characteristic of YOLO is that it combines
object detection (&#8220;is there an object?&#8221;), classification
(&#8220;what kind of object is it?&#8221;), and localization (&#8220;where in
the image is the object?&#8221;) in a single pass through the network. This
makes it more computationally efficient and robust than other networks that only
perform one or two of these tasks simultaneously.

The [original Darknet/YOLO code](https://github.com/pjreddie/darknet) is
written in C, making it performant but more
difficult to understand and play around with than if it were written in Python
(my personal favorite language) using a framework like PyTorch (my personal
favorite deep learning framework). Before taking a deep dive into the background
and my implementation, let&#8217;s look at an example of the end result for
real-time object detection on a webcam video stream:

{{< youtube wyKoi5Hc8WY >}}

This post will touch on the background and fundamental theory behind YOLOv3,
while the next post will examine the code and implementation.

# How does YOLOv3 work?

Let&#8217;s use the following sample image taken from the
[COCO 2017 validation dataset](http://cocodataset.org/#download):

{{< figure src=/img/yolov3_sample_img.jpg >}}

The classification layer of the YOLO network divides this image into a grid of
cells. For illustration, let&#8217;s say it&#8217;s a 7&#215;7 grid, which would
look like the following (in the actual algorithm, there are three distinct grid
sizes corresponding to different scales at different layers of the
network&#8212;we&#8217;ll get to that in a minute):

{{< figure src=/img/yolov3_cells_7x7.jpg >}}

YOLO makes use of bounding box &#8220;priors&#8221; or &#8220;anchors&#8221;.
These are predefined bounding boxes whose shape and size is similar to those of
objects in the training dataset. The authors of YOLO used [K-means
clustering][5] to cluster the bounding boxes of objects in the training data to
determine suitable anchor box sizes. These anchor boxes essentially serve as a
guideline for the algorithm to look for objects of similar size and shape. The
YOLO classification layer uses three anchor boxes; thus, at each grid cell in
the image above, it makes a prediction for each of three bounding boxes based on
the three anchor boxes.

{{< figure src=/img/yolov3_paper_pred.png >}}

In the figure above, which is taken from the YOLOv3 paper, the dashed box
represents an anchor box whose width and height are given by p<sub>w</sub> and
p<sub>h</sub>, respectively. The network predicts parameters t<sub>w</sub> and
t<sub>h</sub> that, when exponentiated, scale the anchor box dimensions to fit
the detected object. The network also predicts the x/y position of the center of
the bounding box within the cell via the parameters t<sub>x</sub> and
t<sub>y</sub>, respectively (note that the sigmoid function must be applied to
the raw values first). The x/y center of the bounding box with respect to the
image origin is obtained by adding the offset of the cell origin from the image
origin, given by c<sub>x</sub> and c<sub>y</sub>, to the offset of the bounding
box center from the cell origin. This yields the final predicted bounding box,
shown in blue.

For a 7&#215;7 grid, there would be 49 cells each predicting three bounding
boxes for a total of 147 bounding boxes. That&#8217;s a lot of predictions!
However, for each bounding box, the algorithm also predicts an
&#8220;objectness&#8221; score&#8212;the likelihood that the predicted bounding
box actually contains an object&#8212;as well as a class score for each class,
which represent the likelihood of the object belonging to each class. This
allows us to filter out detections with low probabilities.

# Network architecture and design

While there are several variations of YOLOv3, they all share the Darknet-53
backbone, which comprises the first 74 layers and is so named because it
contains 53 convolutional layers. The lengthy table below details the layer
types and layer input/output shapes for a 608&#215;608 input image. There are a
couple special layer types, namely &#8220;shortcut&#8221; (which is a residual
layer that sums the outputs of several previous layers) and &#8220;route&#8221;
(which concatenates the outputs of one or more previous layers). For the
shortcut and route layers, the table specifies layer indices. For example, layer
4 is a shortcut layer whose Input column contains &#8220;[3, 1]&#8221;, which
indicates that the output feature maps from layers 3 and 1 are summed. The
result becomes the input for layer 5. Some route layers only contain a single
layer index, like layer 83 whose input is &#8220;[79]&#8221;&#8212;in other
words, this is a skip connection that simply takes the output from layer 79 and
makes it the input for layer 80. On the other hand, layer 86 is a route layer
with inputs &#8220;[85, 61]&#8221;&#8212;in other words, it concatenates the
feature maps from layers 85 and 61. Finally, there are three YOLO classification
layers; each one makes predictions at a different scale.

<table style="width:70%">
<tr>
<th style="width:15%">
Layer #
</th>

<th>
Type
</th>

<th>
Input
</th>

<th>
Output shape
</th>
</tr>

<tr>
<td>
</td>

<td>
convolutional
</td>

<td>
(3, 608, 608)
</td>

<td>
(32, 608, 608)
</td>
</tr>

<tr>
<td>
1
</td>

<td>
convolutional
</td>

<td>
(32, 608, 608)
</td>

<td>
(64, 304, 304)
</td>
</tr>

<tr>
<td>
2
</td>

<td>
convolutional
</td>

<td>
(64, 304, 304)
</td>

<td>
(32, 304, 304)
</td>
</tr>

<tr>
<td>
3
</td>

<td>
convolutional
</td>

<td>
(32, 304, 304)
</td>

<td>
(64, 304, 304)
</td>
</tr>

<tr>
<td>
<em>4</em>
</td>

<td>
<em>shortcut</em>
</td>

<td>
<em>[3, 1]</em>
</td>

<td>
<em>(64, 304, 304)</em>
</td>
</tr>

<tr>
<td>
5
</td>

<td>
convolutional
</td>

<td>
(64, 304, 304)
</td>

<td>
(128, 152, 152)
</td>
</tr>

<tr>
<td>
6
</td>

<td>
convolutional
</td>

<td>
(128, 152, 152)
</td>

<td>
(64, 152, 152)
</td>
</tr>

<tr>
<td>
7
</td>

<td>
convolutional
</td>

<td>
(64, 152, 152)
</td>

<td>
(128, 152, 152)
</td>
</tr>

<tr>
<td>
<em>8</em>
</td>

<td>
<em>shortcut</em>
</td>

<td>
<em>[7, 5]</em>
</td>

<td>
<em>(128, 152, 152)</em>
</td>
</tr>

<tr>
<td>
9
</td>

<td>
convolutional
</td>

<td>
(128, 152, 152)
</td>

<td>
(64, 152, 152)
</td>
</tr>

<tr>
<td>
10
</td>

<td>
convolutional
</td>

<td>
(64, 152, 152)
</td>

<td>
(128, 152, 152)
</td>
</tr>

<tr>
<td>
<em>11</em>
</td>

<td>
<em>shortcut</em>
</td>

<td>
<em>[10, 8]</em>
</td>

<td>
<em>(128, 152, 152)</em>
</td>
</tr>

<tr>
<td>
12
</td>

<td>
convolutional
</td>

<td>
(128, 152, 152)
</td>

<td>
(256, 76, 76)
</td>
</tr>

<tr>
<td>
13
</td>

<td>
convolutional
</td>

<td>
(256, 76, 76)
</td>

<td>
(128, 76, 76)
</td>
</tr>

<tr>
<td>
14
</td>

<td>
convolutional
</td>

<td>
(128, 76, 76)
</td>

<td>
(256, 76, 76)
</td>
</tr>

<tr>
<td>
<em>15</em>
</td>

<td>
<em>shortcut</em>
</td>

<td>
<em>[14, 12]</em>
</td>

<td>
<em>(256, 76, 76)</em>
</td>
</tr>

<tr>
<td>
16
</td>

<td>
convolutional
</td>

<td>
(256, 76, 76)
</td>

<td>
(128, 76, 76)
</td>
</tr>

<tr>
<td>
17
</td>

<td>
convolutional
</td>

<td>
(128, 76, 76)
</td>

<td>
(256, 76, 76)
</td>
</tr>

<tr>
<td>
<em>18</em>
</td>

<td>
<em>shortcut</em>
</td>

<td>
<em>[17, 15]</em>
</td>

<td>
<em>(256, 76, 76)</em>
</td>
</tr>

<tr>
<td>
19
</td>

<td>
convolutional
</td>

<td>
(256, 76, 76)
</td>

<td>
(128, 76, 76)
</td>
</tr>

<tr>
<td>
20
</td>

<td>
convolutional
</td>

<td>
(128, 76, 76)
</td>

<td>
(256, 76, 76)
</td>
</tr>

<tr>
<td>
<em>21</em>
</td>

<td>
<em>shortcut</em>
</td>

<td>
<em>[20, 18]</em>
</td>

<td>
<em>(256, 76, 76)</em>
</td>
</tr>

<tr>
<td>
22
</td>

<td>
convolutional
</td>

<td>
(256, 76, 76)
</td>

<td>
(128, 76, 76)
</td>
</tr>

<tr>
<td>
23
</td>

<td>
convolutional
</td>

<td>
(128, 76, 76)
</td>

<td>
(256, 76, 76)
</td>
</tr>

<tr>
<td>
<em>24</em>
</td>

<td>
<em>shortcut</em>
</td>

<td>
<em>[23, 21]</em>
</td>

<td>
<em>(256, 76, 76)</em>
</td>
</tr>

<tr>
<td>
25
</td>

<td>
convolutional
</td>

<td>
(256, 76, 76)
</td>

<td>
(128, 76, 76)
</td>
</tr>

<tr>
<td>
26
</td>

<td>
convolutional
</td>

<td>
(128, 76, 76)
</td>

<td>
(256, 76, 76)
</td>
</tr>

<tr>
<td>
<em>27</em>
</td>

<td>
<em>shortcut</em>
</td>

<td>
<em>[26, 24]</em>
</td>

<td>
<em>(256, 76, 76)</em>
</td>
</tr>

<tr>
<td>
28
</td>

<td>
convolutional
</td>

<td>
(256, 76, 76)
</td>

<td>
(128, 76, 76)
</td>
</tr>

<tr>
<td>
29
</td>

<td>
convolutional
</td>

<td>
(128, 76, 76)
</td>

<td>
(256, 76, 76)
</td>
</tr>

<tr>
<td>
<em>30</em>
</td>

<td>
<em>shortcut</em>
</td>

<td>
<em>[29, 27]</em>
</td>

<td>
<em>(256, 76, 76)</em>
</td>
</tr>

<tr>
<td>
31
</td>

<td>
convolutional
</td>

<td>
(256, 76, 76)
</td>

<td>
(128, 76, 76)
</td>
</tr>

<tr>
<td>
32
</td>

<td>
convolutional
</td>

<td>
(128, 76, 76)
</td>

<td>
(256, 76, 76)
</td>
</tr>

<tr>
<td>
<em>33</em>
</td>

<td>
<em>shortcut</em>
</td>

<td>
<em>[32, 30]</em>
</td>

<td>
<em>(256, 76, 76)</em>
</td>
</tr>

<tr>
<td>
34
</td>

<td>
convolutional
</td>

<td>
(256, 76, 76)
</td>

<td>
(128, 76, 76)
</td>
</tr>

<tr>
<td>
35
</td>

<td>
convolutional
</td>

<td>
(128, 76, 76)
</td>

<td>
(256, 76, 76)
</td>
</tr>

<tr>
<td>
<em>36</em>
</td>

<td>
<em>shortcut</em>
</td>

<td>
<em>[35, 33]</em>
</td>

<td>
<em>(256, 76, 76)</em>
</td>
</tr>

<tr>
<td>
37
</td>

<td>
convolutional
</td>

<td>
(256, 76, 76)
</td>

<td>
(512, 38, 38)
</td>
</tr>

<tr>
<td>
38
</td>

<td>
convolutional
</td>

<td>
(512, 38, 38)
</td>

<td>
(256, 38, 38)
</td>
</tr>

<tr>
<td>
39
</td>

<td>
convolutional
</td>

<td>
(256, 38, 38)
</td>

<td>
(512, 38, 38)
</td>
</tr>

<tr>
<td>
<em>40</em>
</td>

<td>
<em>shortcut</em>
</td>

<td>
<em>[39, 37]</em>
</td>

<td>
<em>(512, 38, 38)</em>
</td>
</tr>

<tr>
<td>
41
</td>

<td>
convolutional
</td>

<td>
(512, 38, 38)
</td>

<td>
(256, 38, 38)
</td>
</tr>

<tr>
<td>
42
</td>

<td>
convolutional
</td>

<td>
(256, 38, 38)
</td>

<td>
(512, 38, 38)
</td>
</tr>

<tr>
<td>
<em>43</em>
</td>

<td>
<em>shortcut</em>
</td>

<td>
<em>[42, 40]</em>
</td>

<td>
<em>(512, 38, 38)</em>
</td>
</tr>

<tr>
<td>
44
</td>

<td>
convolutional
</td>

<td>
(512, 38, 38)
</td>

<td>
(256, 38, 38)
</td>
</tr>

<tr>
<td>
45
</td>

<td>
convolutional
</td>

<td>
(256, 38, 38)
</td>

<td>
(512, 38, 38)
</td>
</tr>

<tr>
<td>
<em>46</em>
</td>

<td>
<em>shortcut</em>
</td>

<td>
<em>[45, 43]</em>
</td>

<td>
<em>(512, 38, 38)</em>
</td>
</tr>

<tr>
<td>
47
</td>

<td>
convolutional
</td>

<td>
(512, 38, 38)
</td>

<td>
(256, 38, 38)
</td>
</tr>

<tr>
<td>
48
</td>

<td>
convolutional
</td>

<td>
(256, 38, 38)
</td>

<td>
(512, 38, 38)
</td>
</tr>

<tr>
<td>
<em>49</em>
</td>

<td>
<em>shortcut</em>
</td>

<td>
<em>[48, 46]</em>
</td>

<td>
<em>(512, 38, 38)</em>
</td>
</tr>

<tr>
<td>
50
</td>

<td>
convolutional
</td>

<td>
(512, 38, 38)
</td>

<td>
(256, 38, 38)
</td>
</tr>

<tr>
<td>
51
</td>

<td>
convolutional
</td>

<td>
(256, 38, 38)
</td>

<td>
(512, 38, 38)
</td>
</tr>

<tr>
<td>
<em>52</em>
</td>

<td>
<em>shortcut</em>
</td>

<td>
<em>[51, 49]</em>
</td>

<td>
<em>(512, 38, 38)</em>
</td>
</tr>

<tr>
<td>
53
</td>

<td>
convolutional
</td>

<td>
(512, 38, 38)
</td>

<td>
(256, 38, 38)
</td>
</tr>

<tr>
<td>
54
</td>

<td>
convolutional
</td>

<td>
(256, 38, 38)
</td>

<td>
(512, 38, 38)
</td>
</tr>

<tr>
<td>
<em>55</em>
</td>

<td>
<em>shortcut</em>
</td>

<td>
<em>[54, 52]</em>
</td>

<td>
<em>(512, 38, 38)</em>
</td>
</tr>

<tr>
<td>
56
</td>

<td>
convolutional
</td>

<td>
(512, 38, 38)
</td>

<td>
(256, 38, 38)
</td>
</tr>

<tr>
<td>
57
</td>

<td>
convolutional
</td>

<td>
(256, 38, 38)
</td>

<td>
(512, 38, 38)
</td>
</tr>

<tr>
<td>
<em>58</em>
</td>

<td>
<em>shortcut</em>
</td>

<td>
<em>[57, 55]</em>
</td>

<td>
<em>(512, 38, 38)</em>
</td>
</tr>

<tr>
<td>
59
</td>

<td>
convolutional
</td>

<td>
(512, 38, 38)
</td>

<td>
(256, 38, 38)
</td>
</tr>

<tr>
<td>
60
</td>

<td>
convolutional
</td>

<td>
(256, 38, 38)
</td>

<td>
(512, 38, 38)
</td>
</tr>

<tr>
<td>
<em>61</em>
</td>

<td>
<em>shortcut</em>
</td>

<td>
<em>[60, 58]</em>
</td>

<td>
<em>(512, 38, 38)</em>
</td>
</tr>

<tr>
<td>
62
</td>

<td>
convolutional
</td>

<td>
(512, 38, 38)
</td>

<td>
(1024, 19, 19)
</td>
</tr>

<tr>
<td>
63
</td>

<td>
convolutional
</td>

<td>
(1024, 19, 19)
</td>

<td>
(512, 19, 19)
</td>
</tr>

<tr>
<td>
64
</td>

<td>
convolutional
</td>

<td>
(512, 19, 19)
</td>

<td>
(1024, 19, 19)
</td>
</tr>

<tr>
<td>
<em>65</em>
</td>

<td>
<em>shortcut</em>
</td>

<td>
<em>[64, 62]</em>
</td>

<td>
<em>(1024, 19, 19)</em>
</td>
</tr>

<tr>
<td>
66
</td>

<td>
convolutional
</td>

<td>
(1024, 19, 19)
</td>

<td>
(512, 19, 19)
</td>
</tr>

<tr>
<td>
67
</td>

<td>
convolutional
</td>

<td>
(512, 19, 19)
</td>

<td>
(1024, 19, 19)
</td>
</tr>

<tr>
<td>
<em>68</em>
</td>

<td>
<em>shortcut</em>
</td>

<td>
<em>[67, 65]</em>
</td>

<td>
<em>(1024, 19, 19)</em>
</td>
</tr>

<tr>
<td>
69
</td>

<td>
convolutional
</td>

<td>
(1024, 19, 19)
</td>

<td>
(512, 19, 19)
</td>
</tr>

<tr>
<td>
70
</td>

<td>
convolutional
</td>

<td>
(512, 19, 19)
</td>

<td>
(1024, 19, 19)
</td>
</tr>

<tr>
<td>
<em>71</em>
</td>

<td>
<em>shortcut</em>
</td>

<td>
<em>[70, 68]</em>
</td>

<td>
<em>(1024, 19, 19)</em>
</td>
</tr>

<tr>
<td>
72
</td>

<td>
convolutional
</td>

<td>
(1024, 19, 19)
</td>

<td>
(512, 19, 19)
</td>
</tr>

<tr>
<td>
73
</td>

<td>
convolutional
</td>

<td>
(512, 19, 19)
</td>

<td>
(1024, 19, 19)
</td>
</tr>

<tr>
<td>
<em>74</em>
</td>

<td>
<em>shortcut</em>
</td>

<td>
<em>[73, 71]</em>
</td>

<td>
<em>(1024, 19, 19)</em>
</td>
</tr>

<tr>
<td>
75
</td>

<td>
convolutional
</td>

<td>
(1024, 19, 19)
</td>

<td>
(512, 19, 19)
</td>
</tr>

<tr>
<td>
76
</td>

<td>
convolutional
</td>

<td>
(512, 19, 19)
</td>

<td>
(1024, 19, 19)
</td>
</tr>

<tr>
<td>
77
</td>

<td>
convolutional
</td>

<td>
(1024, 19, 19)
</td>

<td>
(512, 19, 19)
</td>
</tr>

<tr>
<td>
78
</td>

<td>
convolutional
</td>

<td>
(512, 19, 19)
</td>

<td>
(1024, 19, 19)
</td>
</tr>

<tr>
<td>
79
</td>

<td>
convolutional
</td>

<td>
(1024, 19, 19)
</td>

<td>
(512, 19, 19)
</td>
</tr>

<tr>
<td>
80
</td>

<td>
convolutional
</td>

<td>
(512, 19, 19)
</td>

<td>
(1024, 19, 19)
</td>
</tr>

<tr>
<td>
81
</td>

<td>
convolutional
</td>

<td>
(1024, 19, 19)
</td>

<td>
(255, 19, 19)
</td>
</tr>

<tr>
<td>
<strong>82</strong>
</td>

<td>
<strong>yolo</strong>
</td>

<td>
<strong>(255, 19, 19)</strong>
</td>

<td>
</td>
</tr>

<tr>
<td>
<em>83</em>
</td>

<td>
<em>route</em>
</td>

<td>
<em>[79]</em>
</td>

<td>
<em>(512, 19, 19)</em>
</td>
</tr>

<tr>
<td>
84
</td>

<td>
convolutional
</td>

<td>
(512, 19, 19)
</td>

<td>
(256, 19, 19)
</td>
</tr>

<tr>
<td>
85
</td>

<td>
upsample
</td>

<td>
(256, 19, 19)
</td>

<td>
(256, 38, 38)
</td>
</tr>

<tr>
<td>
<em>86</em>
</td>

<td>
<em>route</em>
</td>

<td>
<em>[85, 61]</em>
</td>

<td>
<em>(768, 38, 38)</em>
</td>
</tr>

<tr>
<td>
87
</td>

<td>
convolutional
</td>

<td>
(768, 38, 38)
</td>

<td>
(256, 38, 38)
</td>
</tr>

<tr>
<td>
88
</td>

<td>
convolutional
</td>

<td>
(256, 38, 38)
</td>

<td>
(512, 38, 38)
</td>
</tr>

<tr>
<td>
89
</td>

<td>
convolutional
</td>

<td>
(512, 38, 38)
</td>

<td>
(256, 38, 38)
</td>
</tr>

<tr>
<td>
90
</td>

<td>
convolutional
</td>

<td>
(256, 38, 38)
</td>

<td>
(512, 38, 38)
</td>
</tr>

<tr>
<td>
91
</td>

<td>
convolutional
</td>

<td>
(512, 38, 38)
</td>

<td>
(256, 38, 38)
</td>
</tr>

<tr>
<td>
92
</td>

<td>
convolutional
</td>

<td>
(256, 38, 38)
</td>

<td>
(512, 38, 38)
</td>
</tr>

<tr>
<td>
93
</td>

<td>
convolutional
</td>

<td>
(512, 38, 38)
</td>

<td>
(255, 38, 38)
</td>
</tr>

<tr>
<td>
<strong>94</strong>
</td>

<td>
<strong>yolo</strong>
</td>

<td>
<strong>(255, 38, 38)</strong>
</td>

<td>
</td>
</tr>

<tr>
<td>
<em>95</em>
</td>

<td>
<em>route</em>
</td>

<td>
<em>[91]</em>
</td>

<td>
<em>(256, 38, 38)</em>
</td>
</tr>

<tr>
<td>
96
</td>

<td>
convolutional
</td>

<td>
(256, 38, 38)
</td>

<td>
(128, 38, 38)
</td>
</tr>

<tr>
<td>
97
</td>

<td>
upsample
</td>

<td>
(128, 38, 38)
</td>

<td>
(128, 76, 76)
</td>
</tr>

<tr>
<td>
<em>98</em>
</td>

<td>
<em>route</em>
</td>

<td>
<em>[97, 36]</em>
</td>

<td>
<em>(384, 76, 76)</em>
</td>
</tr>

<tr>
<td>
99
</td>

<td>
convolutional
</td>

<td>
(384, 76, 76)
</td>

<td>
(128, 76, 76)
</td>
</tr>

<tr>
<td>
100
</td>

<td>
convolutional
</td>

<td>
(128, 76, 76)
</td>

<td>
(256, 76, 76)
</td>
</tr>

<tr>
<td>
101
</td>

<td>
convolutional
</td>

<td>
(256, 76, 76)
</td>

<td>
(128, 76, 76)
</td>
</tr>

<tr>
<td>
102
</td>

<td>
convolutional
</td>

<td>
(128, 76, 76)
</td>

<td>
(256, 76, 76)
</td>
</tr>

<tr>
<td>
103
</td>

<td>
convolutional
</td>

<td>
(256, 76, 76)
</td>

<td>
(128, 76, 76)
</td>
</tr>

<tr>
<td>
104
</td>

<td>
convolutional
</td>

<td>
(128, 76, 76)
</td>

<td>
(256, 76, 76)
</td>
</tr>

<tr>
<td>
105
</td>

<td>
convolutional
</td>

<td>
(256, 76, 76)
</td>

<td>
(255, 76, 76)
</td>
</tr>

<tr>
<td>
<strong>106</strong>
</td>

<td>
<strong>yolo</strong>
</td>

<td>
<strong>(255, 76, 76)</strong>
</td>

<td>
</td>
</tr>
</table>

Though our example above used a 7&#215;7 grid, the actual network makes
predictions on 19&#215;19, 38&#215;38, and 76&#215;76 grids (for a 608&#215;608
input image). Three different anchor boxes are used at each scale for a total of
nine anchor boxes. This is illustrated in the images below, where the cell grid
and anchor boxes (scaled relative to image dimensions) are shown for each YOLO
prediction layer, i.e., for layers 82, 94, and 106. The positions of the anchor
boxes don&#8217;t mean anything; they&#8217;ve simply been arranged to show each
one clearly.

**First YOLO layer (19&#215;19) anchor boxes&#8212;predict largest objects in
image:**
{{< figure src=/img/yolov3_anchors_19x19.jpg >}}

**Second YOLO layer (38&#215;38) anchor boxes:**
{{< figure src=/img/yolov3_anchors_38x38.jpg >}}

**Third YOLO layer (76&#215;76) anchor boxes&#8212;predict smallest objects in
image:**
{{< figure src=/img/yolov3_anchors_76x76.jpg >}}

The key takeaway is that the later YOLO layers learn more fine-grained features
while incorporating information from earlier layers via the route connections,
ultimately using this information to make predictions on smaller scales.

# Post-processing

Altogether, the three YOLO layers make (19\*19 + 38\*38 + 76\*76) \* 3 = 22743
predictions. By filtering out detections below some nominal probability
threshold (e.g., 0.15), we eliminate most of the false positives. However, since
each grid cell makes 3 predictions and multiple cells are likely to detect the
same objects as their neighbors, we still end up with a lot of duplicate
detections. These can be filtered out via non-maximum suppression (NMS). This
process (all detections &#8211;> probability thresholding &#8211;> duplicate
elimination via NMS) is shown in the animation below. The top frame and bottom
frame of the animation are identical except the top excludes object labels,
since they obscure some of the detected objects.

{{< figure src=/img/yolov3_postprocess.gif >}}

# Conclusion

These are the basic principles underlying a YOLOv3 detection pipeline. Stay
tuned for the next post, in which we&#8217;ll take a closer look at the actual
implementation for real-time detection.

[1]: {{< ref "2020-05-13-a-pytorch-implementation-of-yolov3-for-real-time-object-detection-part-2.md" >}}
[2]: {{< ref "2020-06-30-a-pytorch-implementation-of-yolov3-for-real-time-object-detection-part-3.md" >}}
[3]: {{< ref "2020-09-11-a-pytorch-implementation-of-yolov3-for-real-time-object-detection-part-4.md" >}}
[4]: {{< ref "2020-09-20-a-pytorch-implementation-of-yolov3-for-real-time-object-detection-part-5.md" >}}
[5]: {{< ref "2017-11-20-animating-k-means-clustering-in-2d-with-matplotlib.md" >}}
