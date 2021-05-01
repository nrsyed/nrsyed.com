---
title: HOG-based SVM for detecting vehicles in a video (part 5)
author: Najam Syed
type: post
date: 2018-05-20T00:06:48+00:00
url: /2018/05/19/hog-based-svm-for-detecting-vehicles-in-a-video-part-5/
categories:
  - Computer Vision
  - Machine Learning
tags:
  - HOG
  - SVM
  - object detection
  - OpenCV
  - Python

---
This is the fifth post in a series on implementing an SVM object detection
pipeline for video with OpenCV-Python.

- [Part 1: SVMs, HOG features, and feature extraction][1]
- [Part 2: Sliding window technique and heatmaps][2]
- [Part 3: Feature descriptor code and OpenCV vs scikit-image HOG functions][3]
- [Part 4: Training the SVM classifier][4]
- Part 5: Implementing the sliding window search
- [Part 6: Heatmaps and object identification][5]

The previous posts touched on the foundations of SVMs, HOG features, and the
sliding window plus heatmap approach to find objects in an image, then discussed
the code from portions of the pipeline responsible for extracting features from
sample images and training an SVM classifier to differentiate between vehicles
and non-vehicles. In this post, we&#8217;ll discuss the portions of the code
that implement the sliding window to determine which parts of an image contain
an object. The Python source code and project
[are available on Github](https://github.com/nrsyed/svm-vehicle-detector).

As in the previous posts, let&#8217;s start with a video of the final result to
see what we&#8217;re working towards:

{{< youtube uOxkAF0iA3E >}}

## Sliding window search

Although we&#8217;ve trained our SVM classifier on nice 64&#215;64 images, an
actual dashcam video will not be a 64&#215;64 image that neatly contains or
doesn&#8217;t contain an entire vehicle. Instead, vehicles may be present in
different parts of the image at different scales. One way to tackle this is with
a sliding window search in which a window of fixed size is slid across and down
the image. This is performed at several scales by scaling the image
down&#8212;this repeated downscaling is called an &#8220;image pyramid.&#8221;

The results I obtained with the aforementioned approach were inconsistent, so I
tried something different. My alternative approach was to 1) scan only the
portion of the image below the horizon and above the dash, since there should be
no vehicles outside this region, and 2) use a window of variable size
that&#8217;s relatively small near the horizon and larger toward the bottom of
the image, the rationale being that vehicles near the horizon are farther away
and will appear smaller whereas vehicles near the bottom of the image are closer
and will appear larger. A sample demonstration of this approach can be seen in
the following video:

{{< youtube 6e8XB-bKsZ4 >}}

The colors don&#8217;t signify anything, they&#8217;re simply meant to help
differentiate adjacent windows from one another; I wrote a simple little utility
called
[uniquecolors.py](https://github.com/nrsyed/utilities/blob/master/uniquecolors.py) to generate any arbitrary number of unique colors, which I
used to create the above clip.

The actual sliding window search is facilitated by the `slidingWindow()` helper
function defined in the file
[slidingwindow.py](https://github.com/nrsyed/svm-vehicle-detector/blob/master/slidingwindow.py). The function has the following signature:

{{< highlight python "linenos=true,linenostart=3" >}}
def slidingWindow(image_size, init_size=(64,64), x_overlap=0.5, y_step=0.05,
        x_range=(0, 1), y_range=(0, 1), scale=1.5)
{{< / highlight >}}

Note that the function doesn&#8217;t actually operate on an image. Instead, we
feed it `image_size`, a tuple containing the width and height of an image, from
which it determines the coordinates of all the windows to search (based on the
remaining input parameters). This allows us to call the function once, store the
list of window coordinates to be searched, then refer to this list for every
frame.

As demonstrated in the video, the window traverses the image from top to bottom
and left to right. `init_size` sets the initial size of the window. `x_overlap`
sets the overlap between adjacent windows while moving left to right, as a
fraction of the current window width; in other words, if the current window
width were 100 pixels, `x_overlap=0.5` would cause the window to step 50 pixels
to the right for each left-to-right step. `y_step` determines the amount by
which the top of the window slides down for each step in the top-to-bottom
direction, as a fraction of total image height. If the image were 600 pixels
tall, `y_step=0.05` would cause the window to step 30 pixels toward the bottom
at each vertical step. `x_range` and `y_range` set the portion of the image to
search as a fraction of the image width and height, respectively. For example,
`x_range=(0, 0.5)` would cause only the left half of the image to be searched.
Similarly, `y_range=(0.67, 1.0)` would cause only the bottom third of the image
to be searched. Finally, `scale` sets the ratio by which to increase the size of
the window with each vertical step toward the bottom of the image. If
`scale > 1`, the window gets larger with each step in the y direction. If
`scale < 1`, the window gets smaller with each step in the y direction. If
`scale = 1`, the window size remains fixed.

The actual implementation of these parameters is fairly short:

{{< highlight python "linenos=true,linenostart=35" >}}
windows = []
h, w = image_size[1], image_size[0]
for y in range(int(y_range[0] * h), int(y_range[1] * h), int(y_step * h)):
    win_width = int(init_size[0] + (scale * (y - (y_range[0] * h))))
    win_height = int(init_size[1] + (scale * (y - (y_range[0] * h))))
    if y + win_height > int(y_range[1] * h) or win_width > w:
        break
    x_step = int((1 - x_overlap) * win_width)
    for x in range(int(x_range[0] * w), int(x_range[1] * w), x_step):
        windows.append((x, y, x + win_width, y + win_height))

return windows
{{< / highlight >}}

Observe that each window is added to the list in the form of a tuple containing
the x and y coordinates of the window's upper left corner and the x and y
coordinates of the window's lower right corner, in that order.

## Building the detector

Having established our sliding window function, we can move on to making use of
it in the object detector, for which I've defined a `Detector` class in a file
aptly named
[detector.py](https://github.com/nrsyed/svm-vehicle-detector/blob/master/detector.py). The `__init__()` method of this class, found on **lines
19-30**, sets the sliding window parameters we just discussed in the previous
section. Next, the classifier dictionary produced by the `trainSVM()` function
in
[train.py](https://github.com/nrsyed/svm-vehicle-detector/blob/master/train.py) is loaded via the `loadClassifier()` method on **lines 32-75**.
From the dict, we extract the scikit-learn `LinearSVC` on **line 50** (which
actually classifies feature vectors as containing or not containing the object
on which it was trained), the scikit-learn `StandardScaler` on **line 51**
(which scales feature vectors before they're fed to the classifier), and the
color space and color channels for which we wish to extract features on **lines
52-53**:

{{< highlight python "linenos=true,linenostart=50" >}}
self.classifier = classifier_data["classifier"]
self.scaler = classifier_data["scaler"]
self.cv_color_const = classifier_data["cv_color_const"]
self.channels = classifier_data["channels"]
{{< / highlight >}}

Note that we use an
[OpenCV color space conversion constant](https://docs.opencv.org/3.1.0/d7/d1b/group__imgproc__misc.html#ga4e0972be5de079fed4e3a10e24ef5ef0), which was determined by the
`processFiles()` function in train.py. Since OpenCV uses the BGR color space by
default and no color conversion is required if the user has chosen to use this
color space, I've assigned -1 as a default value, which doesn't correspond to an
actual OpenCV color conversion constant.

Then we re-instantiate a `Descriptor`, which will produce the feature vector for
each window, using the original descriptor parameters on **lines 59-73**.
Originally, I'd packaged the `Descriptor` object into the dictionary, but found
that, if the dictionary was pickled (saved to file), attempting to load the
pickle file produced errors if the pickled dictionary included a `Descriptor`.

The last helper method we define for the `Detector` class is `classify()` on
**lines 77-99**. The signature for the function is simply:

{{< highlight python "linenos=true,linenostart=77" >}}
def classify(self, image):
{{< / highlight >}}

It takes an image in the form of a 3D numpy array, converts it to the
appropriate color space (**lines 84-85**) and keeps only the desired channels
(**lines 87-90**):

{{< highlight python "linenos=true,linenostart=84" >}}
if self.cv_color_const > -1:
    image = cv2.cvtColor(image, self.cv_color_const)

if len(image.shape) > 2:
    image = image[:, :, self.channels]
else:
    image = image[:, :, np.newaxis]
{{< / highlight >}}

We check that the array is three-dimensional even if it contains only a single
channel, adding a third dimension via `np.newaxis` on **line 90** if necessary.
Having preprocessed the image, the next step is to obtain the feature vector for
each window from the sliding window (**lines 92-94**), which we store in a list
called `feature_vectors`.

{{< highlight python "linenos=true,linenostart=92" >}}
feature_vectors = [self.descriptor.getFeatureVector(
        image[y_upper:y_lower, x_upper:x_lower, :])
    for (x_upper, y_upper, x_lower, y_lower) in self.windows]
{{< / highlight >}}

Then we scale the feature vectors and run them through the SVM classifier, which
returns an array of 0s and 1s, where each element corresponds to a window, 0
signifies that the window does not contain the object, and 1 signifies that it
does. Lastly, on **line 99**, we use a list comprehension to return only the
window coordinates of windows predicted to contain an object.

{{< highlight python "linenos=true,linenostart=97" >}}
feature_vectors = self.scaler.transform(feature_vectors)
predictions = self.classifier.predict(feature_vectors)
return [self.windows[ind] for ind in np.argwhere(predictions == 1)[:,0]]
{{< / highlight >}}

We're now ready to actually apply the sliding window search and classification
to a video, which will be the topic of the next post.

[1]: {{< ref "2018-05-06-hog-based-svm-for-detecting-vehicles-in-a-video-part-1.md" >}}
[2]: {{< ref "2018-05-06-hog-based-svm-for-detecting-vehicles-in-a-video-part-2.md" >}}
[3]: {{< ref "2018-05-10-hog-based-svm-for-detecting-vehicles-in-a-video-part-3.md" >}}
[4]: {{< ref "2018-05-16-hog-based-svm-for-detecting-vehicles-in-a-video-part-4.md" >}}
[5]: {{< ref "2018-05-24-hog-based-svm-for-detecting-vehicles-in-a-video-part-6.md" >}}
