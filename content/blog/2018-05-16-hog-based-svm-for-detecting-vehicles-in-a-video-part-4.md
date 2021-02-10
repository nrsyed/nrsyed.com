---
title: HOG-based SVM for detecting vehicles in a video (part 4)
author: Najam Syed
type: post
date: 2018-05-16T22:59:27+00:00
url: /2018/05/16/hog-based-svm-for-detecting-vehicles-in-a-video-part-4/
categories:
  - Computer Vision
  - Machine Learning
tags:
  - computer vision
  - HOG
  - machine learning
  - object detection
  - OpenCV
  - Python
  - SVM

---
This post is the fourth in a series on developing a HOG-based SVM with
OpenCV-Python for detecting objects in a video.

- [Part 1: SVMs, HOG features, and feature extraction][1]
- [Part 2: Sliding window technique and heatmaps][2]
- [Part 3: Feature descriptor code and OpenCV vs scikit-image HOG functions][3]
- Part 4: Training the SVM classifier
- [Part 5: Implementing the sliding window search][4]
- [Part 6: Heatmaps and object identification][5]

With this post, we&#8217;ll continue to look at the code, which is available on
[Github](https://github.com/nrsyed/svm-vehicle-detector). Once again, this is the final result after all is said and done:

{{< youtube uOxkAF0iA3E >}}

Specifically, this post will focus on extracting features from the training
images to train the SVM classifier.

## Extracting feature vectors

First, we&#8217;ll extract features from the sample images and split the sample
data into training, cross-validation, and test sets. The training set is what
we&#8217;ll use to initially train the classifier, and will consist of most of
our sample data. The cross-validation set set will be used to evaluate the
trained classifier. Based on the accuracy with which the classifier evaluates
images in the cross-validation set, we can tune the parameters of the classifier
or, as I&#8217;ve done in my implementation, retrain the classifier with samples
from the cross-validation set that it misclassified. Finally, to get a true
measure of the classifier&#8217;s accuracy, we evaluate its performance on the
test set. The reason for reserving a small amount of data for use in a test set
is that it&#8217;s data the classifier has not seen, been trained on, or been
tuned for, unlike the cross-validation set. Consequently, it gives us an
unbiased measure of the classifier&#8217;s accuracy, ideally.

Before getting started, we need sample images to work with. I used the
[Udacity dataset](https://github.com/udacity/CarND-Vehicle-Detection) (scroll down to find links for vehicle and non-vehicle
data), which contains about 8800 images of vehicles, taken from a variety of
angles, and about 9000 images of non-vehicles&#8212;things like the road and
objects that might be found around the road, like street signs, guardrails, etc.
The Udacity dataset actually contains images taken from the
[GTI](http://www.gti.ssr.upm.es/data/Vehicle_database.html) and
[KITTI](http://www.cvlibs.net/datasets/kitti/eval_tracking.php) datasets, in case you&#8217;re looking for more images.

The functions we need can both be found in
[train.py](https://github.com/nrsyed/svm-vehicle-detector/blob/master/train.py) in the Github project. To extract features from our sample images,
we&#8217;ll use the first function, named `processFiles()`, whose input
signature looks like this:

{{< highlight python "linenos=true,linenostart=13" >}}
def processFiles(pos_dir, neg_dir, recurse=False, output_file=False,
        output_filename=None, color_space="bgr", channels=[0, 1, 2],
        hog_features=False, hist_features=False, spatial_features=False,
        hog_lib="cv", size=(64,64), hog_bins=9, pix_per_cell=(8,8),
        cells_per_block=(2,2), block_stride=None, block_norm="L1",
        transform_sqrt=True, signed_gradient=False, hist_bins=16,
        spatial_size=(16,16)):
{{< / highlight >}}

The first two arguments, `pos_dir` and `neg_dir`, specify the paths to the
directories containing the positive and negative sample images, respectively.
The `recurse` argument specifies whether or not to look in sub-directories
within those directories for images. `color_space`, as the name implies, sets
the color space to which images will be converted before feature extraction; the
supported color spaces can be found later in the file on **lines 71-97**. Note
that OpenCV&#8217;s default behavior for reading and displaying images is to use
the BGR color space. The `channels` argument is a list specifying the color
channel indices to use. For example, `color_space="bgr", channels=[0, 2]` would
indicate that we wish to use the B and R channels of the BGR representation of
the image. `color_space="hls", channels=[1, 2]` would indicate that we wish to
use the L and S channels of the HLS representation of the image. Beyond that,
the remaining arguments will be supplied to the
[Descriptor](https://github.com/nrsyed/svm-vehicle-detector/blob/master/descriptor.py) object, which actually extracts features from an image after
it&#8217;s been converted to the desired color space and channels. See the
[previous post][3] for more information on the Descriptor class.

We make use of some calls to Python&#8217;s built-in `os` library to build lists
of positive and negative file names from the positive and negative sample
directories, respectively:

{{< highlight python "linenos=true,linenostart=57" >}}
if recurse:
    pos_files = [os.path.join(rootdir, file) for rootdir, _, files
        in os.walk(pos_dir) for file in files]
    neg_files = [os.path.join(rootdir, file) for rootdir, _, files
        in os.walk(neg_dir) for file in files]
else:
    pos_files = [os.path.join(pos_dir, file) for file in
        os.listdir(pos_dir) if os.path.isfile(os.path.join(pos_dir, file))]
    neg_files = [os.path.join(neg_dir, file) for file in
        os.listdir(neg_dir) if os.path.isfile(os.path.join(neg_dir, file))]
{{< / highlight >}}

After building the file lists and parsing input arguments specifying the color
space and desired channels, we iterate through the lists, load each file,
convert it to the desired color space if not BGR, keep only the desired
channels, get the feature vector by feeding the image to our `Descriptor`
object, and append it to the appropriate list.

{{< highlight python "linenos=true,linenostart=137" >}}
# Iterate through files and extract features.
for i, filepath in enumerate(pos_files + neg_files):
    image = cv2.imread(filepath)
    if cv_color_const > -1:
        image = cv2.cvtColor(image, cv_color_const)

    if len(image.shape) > 2:
        image = image[:,:,channels]

    feature_vector = descriptor.getFeatureVector(image)

    if i < len(pos_files):
        pos_features.append(feature_vector)
    else:
        neg_features.append(feature_vector)
{{< / highlight >}}

## Scaling features

It is very important that the features be scaled, i.e., normalized. Different
types of features are not necessarily measured along the same scale&#8212;for
example, how do you compare a HOG bin value from HOG features to a color
histogram bin value between 0 and 255? Without scaling or normalizing our
features, features with large values can overshadow features with smaller
values. I've utilized scikit-learn's
[sklearn.preprocessing.StandardScaler](http://scikit-learn.org/stable/modules/generated/sklearn.preprocessing.StandardScaler.html), which, for each column
in our list of feature vectors (i.e., each feature), removes the mean so that
all values are centered around zero and scales the variance to one, so different
features can be directly compared:

{{< highlight python "linenos=true,linenostart=159" >}}
# Instantiate scaler and scale features.
print("Scaling features.\n")
scaler = StandardScaler().fit(pos_features + neg_features)
pos_features = scaler.transform(pos_features)
neg_features = scaler.transform(neg_features)
{{< / highlight >}}

Notice how we fit the scaler to the complete set of feature vectors, then
actually scale the features with `StandardScaler.transform()`. After training
the classifier on these scaled features, we must remember to apply the same
scaler to any feature vectors we wish to classify later.

## Training, cross-validation, and test sets

Next, we shuffle and split our data into a training set, cross-validation set,
and test set. The training set is the data on which the classifier will be
initially trained. The cross-validation set will be used to evaluate the trained
classifier. We can use the classifier's performance on the cross-validation set
to retrain it or tune its parameters as we see fit, until we're satisfied with
its performance. Finally, the classifier is evaluated on data it hasn't seen
before, i.e., the test set, to quantify its ultimate accuracy.

70/20/10 is a common split, i.e., putting 70% of the original data in the
training set, 20% in the cross-validation set, and 10% in the test set. I ended
up going with 75/20/5 based on the fact that the classifier's performance on the
test set seemed to have little correlation with its performance on actual video.

### Training the classifier

To train the classifier, we supply it with the training data and a list of
"labels" to tell it which class each training example belongs to:

{{< highlight python "linenos=true,linenostart=277" >}}
train_set = np.vstack((pos_train, neg_train))
train_labels = np.concatenate(
    (np.ones(pos_train.shape[0],), np.zeros(neg_train.shape[0],)))

print("Training classifier...")
start_time = time.time()
classifier = svm.LinearSVC(C=C, loss=loss, penalty=penalty, dual=dual,
    fit_intercept=fit_intercept)
classifier.fit(train_set, train_labels)
{{< / highlight >}}

In this case, the classes can simply be represented by numbers, where "1"
represents a positive example (corresponding to an image that contains the
object) and "0" represents a negative example (corresponding to an image that
doesn't contain the object). Here, I've used scikit-learn's
[sklearn.svm.LinearSVC](http://scikit-learn.org/stable/modules/generated/sklearn.svm.LinearSVC.html), which is initialized with the desired
hyperparameters on **lines 283-284**. The actual training occurs on **line 285**
via the `LinearSVC.fit()` method, which we supply with the training data and
corresponding labels.

Next, we evaluate its performance on the cross-validation set positive and
negative samples:

{{< highlight python "linenos=true,linenostart=288" >}}
# Run classifier on cross-validation set.
pos_val_predicted = classifier.predict(pos_val)
neg_val_predicted = classifier.predict(neg_val)
{{< / highlight >}}

A perfect classifier would return all 1s for the positive cross-validation
samples and all 0s for the negative cross-validation samples. However, there
will inevitably be misclassified samples. To improve the performance of our
classifier, we specifically add the misclassified samples from the
cross-validation set to the original training set, then retrain the classifier
as follows:

{{< highlight python "linenos=true,linenostart=310" >}}
pos_train = np.vstack((pos_train, pos_val[pos_val_predicted != 1, :]))
neg_train = np.vstack((neg_train, neg_val[neg_val_predicted == 1, :]))
train_set = np.vstack((pos_train, neg_train))
train_labels = np.concatenate(
    (np.ones(pos_train.shape[0],), np.zeros(neg_train.shape[0],)))

classifier.fit(train_set, train_labels)
{{< / highlight >}}

The classifier is now completely trained! If we wanted to, we could have
continued to tune the classifier and its hyperparameters based on its
performance on the cross-validation set. Scikit-learn offers a class to
facilitate this,
[sklearn.model_selection.GridSearchCV](http://scikit-learn.org/stable/modules/generated/sklearn.model_selection.GridSearchCV.html). In this case, I didn't
do any tuning beyond retraining with the incorrectly classified samples from the
cross-validation set, since I found the SVM to attain high accuracy (often >99%)
without additional tuning.

To determine the final accuracy, we simply run the trained classifier on the
test set:

{{< highlight python "linenos=true,linenostart=318" >}}
pos_test_predicted = classifier.predict(pos_test)
neg_test_predicted = classifier.predict(neg_test)
{{< / highlight >}}

In the next post, we'll see how to utilize the trained classifier to find
vehicles in a video.

[1]: {{< ref "2018-05-06-hog-based-svm-for-detecting-vehicles-in-a-video-part-1.md" >}}
[2]: {{< ref "2018-05-06-hog-based-svm-for-detecting-vehicles-in-a-video-part-2.md" >}}
[3]: {{< ref "2018-05-10-hog-based-svm-for-detecting-vehicles-in-a-video-part-3.md" >}}
[4]: {{< ref "2018-05-19-hog-based-svm-for-detecting-vehicles-in-a-video-part-5.md" >}}
[5]: {{< ref "2018-05-24-hog-based-svm-for-detecting-vehicles-in-a-video-part-6.md" >}}
