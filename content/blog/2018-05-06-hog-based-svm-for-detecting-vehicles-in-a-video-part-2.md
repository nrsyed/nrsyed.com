---
title: HOG-based SVM for detecting vehicles in a video (part 2)
author: Najam Syed
type: post
date: 2018-05-07T03:47:01+00:00
url: /2018/05/06/hog-based-svm-for-detecting-vehicles-in-a-video-part-2/
categories:
  - Computer Vision
  - Machine Learning
tags:
  - HOG
  - SVM
  - object detection
  - OpenCV

---
This post is part of a series on developing an SVM classifier to find vehicles
in a video:

- [Part 1: SVMs, HOG features, and feature extraction][1]
- Part 2: Sliding window technique and heatmaps
- [Part 3: Feature descriptor code and OpenCV vs scikit-image HOG functions][2]
- [Part 4: Training the SVM classifier][3]
- [Part 5: Implementing the sliding window search][4]
- [Part 6: Heatmaps and object identification][5]

The code is also available on
[Github](https://github.com/nrsyed/svm-vehicle-detector). In this post, we&#8217;ll examine the portion of the vehicle
detection pipeline after the SVM has been trained. Once again, here&#8217;s the
final result:

{{< youtube uOxkAF0iA3E >}}

## The sliding window technique

The goal of our vehicle detection SVM is to classify an image as
&#8220;vehicle&#8221; or &#8220;non-vehicle&#8221;. For this project, I trained
the SVM on 64&#215;64 patches that either contained a vehicle or didn&#8217;t
contain a vehicle. A blown-up example of each (as well as its HOG visualization)
is presented again below:

{{< figure src=/img/hog_visualization.png >}}

These images were obtained from the
[Udacity dataset](https://github.com/udacity/CarND-Vehicle-Detection), which contained 8799 64&#215;64 images of vehicles and 8971
64&#215;64 images of non-vehicles, all cropped to the correct size. These images
are actually subsets of the
[GTI](http://www.gti.ssr.upm.es/data/Vehicle_database.html) and
[KITTI](http://www.cvlibs.net/datasets/kitti/eval_tracking.php) vehicle datasets, if you&#8217;d like to check those out.

However, actual frames of a video won&#8217;t be nicely cropped 64&#215;64
images. Instead, they&#8217;ll look something like this:
{{< figure src=/img/example_frame.png >}}

To find vehicles in a full image, we utilize a sliding window. Traditionally,
this involves selecting a window of a relatively small size, like 64&#215;64 or
100&#215;100, etc., and &#8220;sliding&#8221; it across the image in steps until
the entirety of the image has been covered. Each window is fed to the SVM, which
classifies that particular window as &#8220;vehicle&#8221; or
&#8220;non-vehicle&#8221;. This is repeated at several scales of the image by
scaling the image down. Sampling the image at different sizes helps ensure that
instances of the object both large and small will be found. For example, a
vehicle that&#8217;s nearby will appear larger than one that&#8217;s farther
away, so downscaling improves the odds that both will be detected. This repeated
downscaling of the image is referred to as an &#8220;image pyramid.&#8221;
Adrian Rosebrock has
[a good set of posts on using sliding windows and image pyramids for object
detection over at pyimagesearch](https://www.pyimagesearch.com/2015/03/23/sliding-windows-for-object-detection-with-python-and-opencv/).

In my implementation, I originally utilized a sliding window of fixed size
sampling different scales of the image via an image pyramid, but found it to
produce many false positives. As an alternative, I tried a sliding window of
variable size with a relatively small initial size that increased in size with
each step toward the bottom of the image, the rationale being that vehicles near
the bottom of the image are physically closer to the camera and appear larger
(and vice versa). Furthermore, I only scanned the portion of the image below the
horizon, since there shouldn&#8217;t be any vehicles above the horizon. This
seemed to improve the results significantly. The following short clip
demonstrates the technique:

{{< youtube 6e8XB-bKsZ4 >}}

Observe that there&#8217;s considerable overlap between windows:

{{< figure src=/img/sliding_window_example.png >}}

This means that the same vehicle will probably be detected multiple times in
adjacent windows, which ends up looking like this:

{{< figure src=/img/sliding_window_detections.png >}}

The full video, with all detections drawn at every frame:

{{< youtube TfX6jtuPL0I >}}

However, our goal is to find (and draw a box around) individual vehicles. To do
this, we must reduce multiple overlapping detections into a single detection,
which we&#8217;ll explore in the next section.

**IMPORTANT NOTE ON WINDOW SIZES:** Recall that the features extracted from each
window will be fed to and classified by the SVM (as &#8220;positive&#8221; /
&#8220;vehicle&#8221; or &#8220;negative&#8221; / &#8220;non-vehicle&#8221;). If
the SVM was trained on 64&#215;64 images, the features extracted from each
window must also come from a 64&#215;64 image. If the window is a different
size, then each window should be resized to 64&#215;64 before feature
extraction&#8212;otherwise, the results will be meaningless.

## Heatmap for combining repeated detections

Several methods exist for reducing repeated detections into a single detection.
One approach is to build a heatmap in which each detection contributes some
positive value to the region of the image it covers. Regions of the image with
many overlapping detections will provide a greater number of contributions to
that region of the heatmap, seen in the image below (the full-scale heatmap
superimposed on the raw image uses shades of red instead of grayscale like the
small-scale inset heatmap in the corner):

{{< figure src=/img/heatmap_overlay.png >}}

To reduce false positives, we can use the weighted sum and/or average of the
heatmaps of the last N frames of the video, giving a higher weight to more
recent frames and a lower weight to older frames, then consider only areas of
the summed heatmap with values above some threshold. This way, regions with
consistent and sustained detections are more likely to be correctly identified
as vehicles, while areas with fleeting detections that only last a couple frames
(which are likely false positives) are more likely to be ignored. Here&#8217;s
the complete video with the full-scale superimposed heatmap:

{{< youtube OT68xGggpkM >}}

## Labeling and boxing distinct objects

Having combined multiple detections into &#8220;blobs&#8221; on the heatmap, we
can now apply a connected-component algorithm to determine how many distinct
objects (blobs) are present, as well as which pixels belong to which object:

{{< figure src=/img/labeled_objects.png >}}

And, of course, the full video with each object labeled with a unique identifier
(number):

{{< youtube iOt_3tQJBFY >}}

This video demonstrates an important fact: objects are numbered arbitrarily and
sometimes change numbers between frames. In other words, this algorithm detects
objects but does _not_ track them.

The final step, after finding each object, is to draw the largest possible
bounding box around each object, ignoring objects that are too small and likely
to be false positives.

{{< figure src=/img/final_bounding_boxes.png >}}

In the next post, we&#8217;ll delve into finer implementation details and
specifics by examining the code.

[1]: {{< ref "2018-05-06-hog-based-svm-for-detecting-vehicles-in-a-video-part-1.md" >}}
[2]: {{< ref "2018-05-10-hog-based-svm-for-detecting-vehicles-in-a-video-part-3.md" >}}
[3]: {{< ref "2018-05-16-hog-based-svm-for-detecting-vehicles-in-a-video-part-4.md" >}}
[4]: {{< ref "2018-05-19-hog-based-svm-for-detecting-vehicles-in-a-video-part-5.md" >}}
[5]: {{< ref "2018-05-24-hog-based-svm-for-detecting-vehicles-in-a-video-part-6.md" >}}
