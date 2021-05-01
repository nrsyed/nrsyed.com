---
title: HOG-based SVM for detecting vehicles in a video (part 3)
author: Najam Syed
type: post
date: 2018-05-11T00:50:47+00:00
url: /2018/05/10/hog-based-svm-for-detecting-vehicles-in-a-video-part-3/
categories:
  - Computer Vision
  - Machine Learning
tags:
  - HOG
  - SVM
  - image processing
  - object detection
  - OpenCV
  - Python

---
This post is part of a series on developing an SVM classifier for object
detection:

- [Part 1: SVMs, HOG features, and feature extraction][1]
- [Part 2: Sliding window technique and heatmaps][2]
- Part 3: Feature descriptor code and OpenCV vs scikit-image HOG functions
- [Part 4: Training the SVM classifier][3]
- [Part 5: Implementing the sliding window search][4]
- [Part 6: Heatmaps and object identification][5]

The previous posts provided a high-level overview of SVMs (support vector
machines), HOG (histogram of oriented gradients) features, and the basic
algorithm employed by the object detection pipeline to actually find objects in
images via a sliding window search and heatmap. If you&#8217;re not familiar
with those topics, read those posts first. In this post, we&#8217;ll begin to
look at the actual code, which is available on
[Github](https://github.com/nrsyed/svm-vehicle-detector) (as well as a
[readme](https://github.com/nrsyed/svm-vehicle-detector/blob/master/README.md) that summarizes the project and
[instructions](https://github.com/nrsyed/svm-vehicle-detector/blob/master/INSTRUCTIONS.md) on using the pipeline). Here&#8217;s what the code ultimately
ends up doing:

{{< youtube uOxkAF0iA3E >}}

I won&#8217;t go through every line of code, as that would be excessive, but I
will try to touch on key implementation details.

## Prerequisites

I&#8217;ll assume that you already have Python 3 and OpenCV installed.
Installing OpenCV is not trivial, so
[read the documentation](https://docs.opencv.org/3.4/df/d65/tutorial_table_of_content_introduction.html) and/or check out
[this helpful post by Adrian Rosebrock](https://www.pyimagesearch.com/2016/10/24/ubuntu-16-04-how-to-install-opencv/) for instructions.

You&#8217;ll need the following Python packages: numpy, scikit-image 0.14+,
scikit-learn, and scipy. As of this writing, scikit-image 0.14 is the
development version (not released).
[These are the instructions for installing it](http://scikit-image.org/docs/dev/install.html). The previous versions of
scikit-image don&#8217;t support multichannel images for HOG feature extraction.
If you don&#8217;t plan to use multichannel images or you don&#8217;t plan to
use the scikit-image HOG function (OpenCV also has this functionality, as
we&#8217;ll see below), the stable release of scikit-image should be fine.

This post also assumes some basic familiarity with Python and object-orientation
in Python (classes, etc.).

## Feature descriptor

### HOG features

The features we extract from the images form the basis of the object detection
pipeline, so let&#8217;s begin by looking at
[descriptor.py](https://github.com/nrsyed/svm-vehicle-detector/blob/master/descriptor.py), a file that defines a `Descriptor` class. This allows us to
create a `Descriptor` object that stores information about the features we wish
to extract. Any time we want to obtain a feature vector from an image, we can
simply pass it to the object&#8217;s `getFeatureVector()` method, which returns
the feature vector.

Referring to
[descriptor.py](https://github.com/nrsyed/svm-vehicle-detector/blob/master/descriptor.py), you&#8217;ll notice that the first item in this class
definition is another class definition for a nested class called
`_skHOGDescriptor`. The leading underscore in the name is meant to indicate that
it&#8217;s meant for internal use. This class simply serves as a wrapper for the
scikit-image HOG function, `skimage.feature.hog()`, which takes our desired HOG
parameters and returns the HOG features.
{{< highlight python "linenos=true,linenostart=12" >}}
class _skHOGDescriptor:

        """
        Wrapper subclass for skimage.feature.hog. Wrapping skimage.feature.hog
        in a class in which we also define a compute() function allows us to
        mirror the usage of OpenCV cv2.HOGDescriptor class method compute().
        """

        def __init__(self, hog_bins, pix_per_cell, cells_per_block,
                block_norm, transform_sqrt):

            """@see Descriptor.#__init__(...)"""

            self.hog_bins = hog_bins
            self.pix_per_cell = pix_per_cell
            self.cells_per_block = cells_per_block
            self.block_norm = block_norm
            self.transform_sqrt = transform_sqrt

        def compute(self, image):
            multichannel = len(image.shape) > 2
            sk_hog_vector = feature.hog(image, orientations=self.hog_bins,
                pixels_per_cell=self.pix_per_cell,
                cells_per_block=self.cells_per_block,
                block_norm=self.block_norm, transform_sqrt=self.transform_sqrt,
                multichannel=multichannel, feature_vector=True)
            return np.expand_dims(sk_hog_vector, 1)
{{< / highlight >}}

In the nested class, we store these parameters as instance variables (in the
`__init__()` method on **lines 20-29**), then define a method named `compute()`
on **line 31** that actually takes an image, feeds the stored HOG parameters to
`skimage.feature.hog()`, and returns the feature vector in the form of a 1D
numpy array&#8212;for example, if the HOG feature vector contained 1000
features, the shape of the returned array would be `(1000,)`. Before returning
the HOG feature vector on **line 38**, we add a dimension to this 1D array to
make it a 2D array via `np.expand_dims()`, which, for our 1000-feature feature
vector, gives the array a shape of `(1000, 1)` &#8212;same number of elements,
but an extra dimension.

What&#8217;s the point of this? Aside from scikit-image, OpenCV also provides a
way to compute the HOG features of an image via the
[cv2.HOGDescriptor](https://docs.opencv.org/3.1.0/d5/d33/structcv_1_1HOGDescriptor.html) class. A `cv2.HOGDescriptor` object is
instantiated with the desired HOG parameters, and it possesses a `compute()`
method that takes an image and returns the HOG feature vector in the form of a
2D array.

My program gives the user the opportunity to choose whether to use the
scikit-image HOG implementation or the OpenCV HOG implementation. By wrapping
the scikit-image HOG function in a nested class, we can instantiate a single HOG
descriptor object later based on whichever implementation the user selects,
e.g., `HOGDescriptor = _skHOGDescriptor()` for scikit-learn or
`HOGDescriptor = cv2.HOGDescriptor()` for OpenCV. We can then use the resulting
`HOGDescriptor` object the same way regardless of the library chosen. This can
be seen on **lines 88-114**:

{{< highlight python "linenos=true,linenostart=88" >}}
if hog_lib == "cv":
    winSize = size
    cellSize = pix_per_cell
    blockSize = (cells_per_block[0] * cellSize[0],
                 cells_per_block[1] * cellSize[1])

    if block_stride is not None:
        blockStride = self.block_stride
    else:
        blockStride = (int(blockSize[0] / 2), int(blockSize[1] / 2))

    nbins = hog_bins
    derivAperture = 1
    winSigma = -1.
    histogramNormType = 0   # L2Hys (currently the only available option)
    L2HysThreshold = 0.2
    gammaCorrection = 1
    nlevels = 64
    signedGradients = signed_gradient

    self.HOGDescriptor = cv2.HOGDescriptor(winSize, blockSize,
        blockStride, cellSize, nbins, derivAperture, winSigma,
        histogramNormType, L2HysThreshold, gammaCorrection,
        nlevels, signedGradients)
else:
    self.HOGDescriptor = self._skHOGDescriptor(hog_bins, pix_per_cell,
        cells_per_block, block_norm, transform_sqrt)
{{< / highlight >}}

What&#8217;s the difference between the two implementations? For starters, they
take different parameters, and the OpenCV implementation more closely follows
the original technique by Dalal and Triggs. Documentation for the OpenCV HOG
object is poor, and documentation for the Python version (as opposed to C++) is
nonexistent. For a concise and informative explanation of the OpenCV
version&#8217;s input arguments, see
[this post by Satya Mallick](https://www.learnopencv.com/handwritten-digits-classification-an-opencv-c-python-tutorial/). Note that, in the OpenCV implementation, block
size is in pixels (not cells), and the block stride for block normalization must
be set, also in pixels.

Three other major differences between the OpenCV and scikit-image HOG
implementations (and ones which I believe have the greatest practical impact for
our purposes) are as follows:

1) OpenCV HOG permits the use of both signed and unsigned gradients;
scikit-learn HOG is limited to unsigned gradients.

2) OpenCV HOG does not support 2-channel images (but 1-channel, 3-channel, and
4-channel are fine). scikit-learn 0.14 supports multichannel images with any
number of channels.

3) OpenCV&#8217;s HOG implementation is blazing fast compared to scikit-learn,
even though scikit-learn is written with Cython. During development and testing,
I found OpenCV HOG to be 4 to 5 times faster than its scikit-learn counterpart.

### Color channel histogram features and spatial features

Moving on, we obtain color channel histogram features on **lines 141-146** and
spatial features on **lines 148-152** in the `Descriptor` class&#8217;s
`getFeatureVector()` method:

{{< highlight python "linenos=true,linenostart=141" >}}
hist_vector = np.array([])
for channel in range(image.shape[2]):
    channel_hist = np.histogram(image[:, :, channel],
            bins=self.hist_bins, range=(0, 255))[0]
    hist_vector = np.hstack((hist_vector, channel_hist))
feature_vector = np.hstack((feature_vector, hist_vector))

elf.spatial_features:
spatial_image = cv2.resize(image, self.spatial_size,
        interpolation=cv2.INTER_AREA)
spatial_vector = spatial_image.ravel()
feature_vector = np.hstack((feature_vector, spatial_vector))
{{< / highlight >}}

Note how we make use of `np.histogram()` for the histogram of each channel,
being sure to specify the range `range=(0, 255)` since it&#8217;s assumed
we&#8217;re working with 8-bit images. For spatial features, the image is
resized, then flattened with `spatial_image.ravel()`. We utilize `np.hstack()`
to append features to the feature vector array.

That about sums up the feature descriptor. The next post will examine the
functions that extract features (via the `Descriptor` object discussed in this
post) from our sample images and train the SVM classifier.

[1]: {{< ref "2018-05-06-hog-based-svm-for-detecting-vehicles-in-a-video-part-1.md" >}}
[2]: {{< ref "2018-05-06-hog-based-svm-for-detecting-vehicles-in-a-video-part-2.md" >}}
[3]: {{< ref "2018-05-16-hog-based-svm-for-detecting-vehicles-in-a-video-part-4.md" >}}
[4]: {{< ref "2018-05-19-hog-based-svm-for-detecting-vehicles-in-a-video-part-5.md" >}}
[5]: {{< ref "2018-05-24-hog-based-svm-for-detecting-vehicles-in-a-video-part-6.md" >}}
