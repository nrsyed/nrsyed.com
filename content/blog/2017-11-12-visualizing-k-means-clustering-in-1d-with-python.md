---
title: Visualizing K-means clustering in 1D with Python
author: Najam Syed
type: post
date: 2017-11-13T02:59:25+00:00
url: /2017/11/12/visualizing-k-means-clustering-in-1d-with-python/
categories:
  - Machine Learning
tags:
  - ffmpeg
  - K-means clustering
  - machine learning
  - matplotlib
  - Python
---
These first few posts will focus on K-means clustering, beginning with a brief
introduction to the technique and a simplified implementation in one dimension
to demonstrate the concept. In the next post, the concept will be extended to N
dimensions. These posts and, for that matter, probably most future posts, will
focus not only on the technique in question, but also on the code&#8211;Python,
in this case. In other words, this post is at least as much about
Python&#8211;or, perhaps, programming in general&#8211;as it is about K-means
clustering. To that end, we will go through the accompanying code, line by line,
to understand not only what the code is doing, but how and why.

# What is K-means clustering?

Without delving into too much detail (there are, after all, numerous resources
out there that discuss K-means clustering), K-means clustering is an
unsupervised machine learning technique whose purpose is to segment a data set
into K clusters. In other words, given a bunch of data, K-means clustering seeks
to divide it into distinct groups&#8211;usually without prior knowledge of where
to start and without feedback on whether the resulting grouping is correct. The
K-means clustering algorithm achieves this via several major steps:

1) Initialize K centroids, one for each cluster.
2) Assign each point in the data set to its nearest centroid.
3) After each point has been assigned to a cluster (based on its proximity to
the cluster centroids), recalculate the centroid of each cluster.
4) Repeat steps 2-3 until the centroids no longer change, or until a certain
number of iterations is reached.

K-means clustering isn&#8217;t usually used for one-dimensional data, but the
one-dimensional case makes for a relatively simple example that demonstrates how
the algorithm works. As the title suggests, the aim of this post is to visualize
K-means clustering in one dimension with Python, like so:

{{< youtube fGkGRoiBtKg >}}

We&#8217;ll take a look at the code used to create the animations in this video
in the following section.

# The code

[
The Python script used to create the animations in the video above can be found
on Github.](https://github.com/nrsyed/examples/blob/master/kmeans1d_demo.py) Some familiarity with Python, or at least with programming, is
assumed, but most of the content will be explained in detail below-this
particular script strives for clarity over brevity. The script should work in
both Python 2.x and Python 3.x, and requires you to have the numpy and
matplotlib packages installed.

OK, let&#8217;s get started. Open up your favorite IDE or text editor (I prefer
vim) and create a file named kmeans1d_demo.py, or download the script from the
Github link above and follow along.

{{< highlight python "linenos=true" >}}
import numpy as np
import matplotlib.pyplot as plt
import colorsys
import sys

K = 3   # number of centroids to compute
numClusters = 3 # actual number of clusters to generate
ptsPerCluster = 40  # number of points per actual cluster
xCenterBounds = (-2, 2) # limits within which to place actual cluster centers
{{< / highlight >}}

`numClusters` is the number of clusters we&#8217;ll actually generate, each of
which will contain `ptsPerCluster` points. We&#8217;ll place the centers of
these clusters within the (min, max) values given by `xCenterBounds`
(&#8220;x&#8221; is our one dimension in this one-dimensional example). `K` is
the number of centroids, i.e., clusters, we&#8217;d like the algorithm to look
for&#8211;it&#8217;s the &#8220;K&#8221; in &#8220;K-means&#8221;. Note that the
number of clusters the algorithm searches for is independent of the number of
clusters we actually generate. In fact, this is an important point&#8211;in this
example, we are explicitly generating clusters of data before letting our
K-means algorithm have a go at it. In the real world, however, we won&#8217;t
usually be generating the data. We&#8217;ll be collecting or receiving it, we
won&#8217;t necessarily know how many clusters exist, if any, and it&#8217;ll be
up to us and/or our K-means algorithm to determine how many clusters to divide
the data into, i.e., what value of K to choose. There are methods for
determining the optimal value of K, but we&#8217;ll get into that later.

{{< highlight python "linenos=true,linenostart=11" >}}
# Randomly place cluster centers within the span of xCenterBounds.
centers = np.random.random_sample((numClusters,))
centers = centers * (xCenterBounds[1] - xCenterBounds[0]) + xCenterBounds[0]

# Initialize array of data points.
points = np.zeros((numClusters * ptsPerCluster,))

# Normally distribute ptsPerCluster points around each center.
stDev = 0.15
for i in range(numClusters):
    points[i*ptsPerCluster:(i+1)*ptsPerCluster] = (
        stDev * np.random.randn(ptsPerCluster) + centers[i])
{{< / highlight >}}

Line **12** utilizes the `random_sample` function of numpy&#8217;s random module
to generate an array of random floats in the interval [0.0, 1.0), sampled from a
continuous uniform distribution (as opposed to, say, a normal distribution).
Line **13** maps these values from the range [0.0, 1.0) to the range given by
`xCenterBounds`. These values constitute the centers of the clusters of points
we&#8217;ll generate, which is achieved by lines **19-22** (each iteration of
the loop generates a cluster of points and stores them in `points`). To do this,
we define a standard deviation `stDev`, and utilize the numpy function `randn`,
which draws from a normal distribution. Increasing the value of `stDev` will
cause the points to spread out, whereas decreasing its value results in more
tightly packed clusters. Play around with this to see how it affects the
algorithm&#8217;s ability to differentiate clusters from one another.

{{< highlight python "linenos=true,linenostart=24" >}}
# Randomly select K points as the initial centroid locations.
centroids = np.zeros((K,))
indices = []
while len(indices) < K:
    index = np.random.randint(0, numClusters * ptsPerCluster)
    if not index in indices:
        indices.append(index)
centroids = points[indices]

# Assign each point to its nearest centroid. Store this in classifications,
# where each element will be an int from 0 to K-1.
classifications = np.zeros((points.shape[0],), dtype=np.int)
def assignPointsToCentroids():
    for i in range(points.shape[0]):
        smallestDistance = 0
        for k in range(K):
            distance = abs(points[i] - centroids[k])
            if k == 0:
                smallestDistance = distance
                classifications[i] = k
            elif distance < smallestDistance:
                smallestDistance = distance
                classifications[i] = k

assignPointsToCentroids()
{{< / highlight >}}

Several methods exist for choosing the initial locations for our K centroids.
This is important, since our choice of initial locations affects the outcome.
There are many ways in which we can cluster any given set of data. The K-means
algorithm does not guarantee that we will arrive at the best solution (the
&#8220;global optimum&#8221;), only that we will arrive at _a_ solution
(&#8220;local optimum&#8221;). Regardless, as a rule of thumb, a good way to
initialize the centroid locations is to randomly choose K unique points from our
data set and use those as the initial centroid locations. This is what lines
**25-31** accomplish by choosing K unique indices from the `points` array and
storing the values at those indices in the `centroids` array. During each
iteration of the algorithm, we&#8217;ll update `centroids` with the new centroid
locations.

Finally, we will assign each point in `points` to the cluster whose centroid the
point is closest to, with the function `assignPointsToCentroids()`. In other
words, we&#8217;ll iterate through `points` and, for each point, we will
determine which of the K centroids in `centroids` that point is closest to, then
store the index corresponding to that centroid/cluster in the array
`classifications` (since we&#8217;re &#8220;classifying&#8221; the point as
belonging to one of the K clusters). Each element in `classifications`
corresponds to a point in `points`. So, if `classifications[3] = 0`, that would
signify that the fourth point, i.e., `points[3]`, is closest to centroid 0,
whose location is given by `centroids[0]`. Since we&#8217;re only dealing with
one dimension in this example, the distance between a given point and a given
centroid can be obtained with the built-in absolute value function `abs()`.
After defining our function `assignPointsToCentroids()`, we run it once to group
the points into clusters based on the initial centroid locations currently in
`centroids`.

{{< highlight python "linenos=true,linenostart=50" >}}
# Define a function to recalculate the centroid of a cluster.
def recalcCentroids():
    for k in range(K):
        if sum(classifications == k) > 0:
            centroids[k] = sum(points[classifications == k]) / sum(classifications == k)
{{< / highlight >}}

Lines **51-54** define a function, `recalcCentroids()`, that carries out the
other major part of the algorithm: recalculating each cluster&#8217;s centroid
location. For each cluster, we first check whether or not any points are
actually assigned to that cluster with `if sum(classifications == k) > 0`. The
comparative statement `classifications == k` returns an array containing 1s at
the indices where `classifications` equals `k` and 0s where it doesn&#8217;t; if
the sum of the elements is at least 1, then that means at least one point is
assigned to that cluster. The next statement on line **54**, which actually
computes the centroid, involves dividing by the number of points in the cluster.
Ensuring there&#8217;s at least one point in the cluster preempts division by
zero.

{{< highlight python "linenos=true,linenostart=56" >}}
# Generate a unique color for each of the K clusters using the HSV color scheme.
# Simultaneously, initialize matplotlib line objects for each centroid and cluster.
hues = np.linspace(0, 1, K+1)[:-1]

fig, ax = plt.subplots()
clusterPointsList = []
centroidPointsList = []
for k in range(K):
    clusterColor = tuple(colorsys.hsv_to_rgb(hues[k], 0.8, 0.8))

    clusterLineObj, = ax.plot([], [], ls='None', marker='x', color=clusterColor)
    clusterPointsList.append(clusterLineObj)

    centroidLineObj, = ax.plot([], [], ls='None', marker='o',
        markeredgecolor='k', color=clusterColor)
    centroidPointsList.append(centroidLineObj)
iterText = ax.annotate('', xy=(0.01, 0.01), xycoords='axes fraction')
{{< / highlight >}}

Our goal in this exercise is to visualize the algorithm, which means we&#8217;ll
want a different color to represent each cluster. A nifty way to achieve this
for any arbitrary number of clusters is to take advantage of the
[
HSV color space](https://en.wikipedia.org/wiki/HSL_and_HSV), which classifies colors by **h**ue, **s**aturation, and
lightness **v**alue. These parameters can be represented by a cone or cylinder.
The hue changes as we travel around the cylinder. 0&#176; represents red,
120&#176; represents green, 240&#176; represents blue, and 360&#176; marks a
return to red. In the Python `colorsys` module, the range 0&#176;-360&#176; is
represented by a float from 0 to 1. On line **58**, to get K distinct colors, we
divide the hue range [0, 1] into K+1 equally spaced numbers and use all except
the last one. This is because the first number will be 0 and the last will be 1,
which, in the HSV color space, both represent red.

Line **60** creates a figure with an axis using the pyplot function
`subplots()`, and returns handles to the figure and axis objects, which we can
use to get or set figure and axis properties later. To visualize the algorithm,
we want to plot each cluster, as well as the centroid for that cluster, in a
unique color. We also need to be able to update each cluster after each
iteration of the algorithm. To do this, we&#8217;ll utilize a for-loop to
initialize an empty matplotlib line object for each cluster and for each
centroid (lines **63-71**) by calling the `plot()` function of our axis.
Basically, for each of the K clusters, we add a &#8220;line object&#8221; to the
axis `ax` using `plot()`. The properties of our line object are determined by
the arguments we pass to `plot()`.

The first two arguments to `plot()` are the x and y coordinates of the points
we&#8217;d like to plot. By passing in empty arrays with `ax.plot([], [], ...)`,
we&#8217;re initializing a line that doesn&#8217;t have any x or y data. The
keyword argument `ls` sets the linestyle; `ls='None'` tells matplotlib that we
want to plot the points without a line connecting them. The keyword argument
`marker` sets the marker style. The keyword argument `color` takes any
matplotlib color specification. In this case, we&#8217;re feeding it an RGB
tuple crafted from our HSV colors using the `colorsys` function `hsv_to_rgb()`
(note that matplotlib also has a colors module, `matplotlib.colors`, which can
convert HSV to RGB, but I used `colorsys` to show that Python has a built-in
package to handle this functionality). `plot()` returns a handle to the line
object it just created, so we can modify any of the aforementioned properties
later. Of course, we need to be able to access these line object handles later
each time we want to update our plot. We do this by adding the cluster and
centroid line object handles to the lists `clusterPointsList` and
`centroidPointsList`, respectively. This maintains a reference to the objects
from our for-loop after the loop has completed.

Line **72** adds a blank text annotation to the lower left corner of the plot.
We&#8217;ll use this text to display the number of iterations the algorithm has
performed, and we&#8217;ll update it at every iteration using its handle, which
I&#8217;ve named `iterText`.

{{< highlight python "linenos=true,linenostart=74" >}}
# Define a function to update the plot.
def updatePlot(iteration):
    for k in range(K):
        xDataNew = points[classifications == k]
        clusterPointsList[k].set_data(xDataNew, np.zeros((len(xDataNew),)))
        centroidPointsList[k].set_data(centroids[k], 0)
    iterText.set_text('i = {:d}'.format(iteration))
    plt.savefig('./{:d}.png'.format(iteration))
    plt.pause(0.5)

dataRange = np.amax(points) - np.amin(points)
ax.set_xlim(np.amin(points) - 0.05*dataRange, np.amax(points) + 0.05*dataRange)
ax.set_ylim(-1, 1)
iteration = 0
updatePlot(iteration)
plt.ion()
plt.show()
{{< / highlight >}}

We&#8217;re almost done. We just need a function to update the plot during each
iteration of the algorithm, which is defined on lines **75-82**. Our
`updatePlot()` function takes one argument&#8211;the current iteration&#8211;and
uses it to set the value of the `iterText` annotation. For each cluster `k`, the
function determines which points belong to the cluster (line **77**), then uses
that to set the x data of the line object corresponding to the cluster (which it
pulls from `clusterPointsList`) using the line object&#8217;s `set_data()`
method. The `set_data()` method takes two arguments: an array of x coordinates
and an array of y coordinates. Since this is a one-dimensional example, we
don&#8217;t care about the y values, so we set them all to 0. Note that we
don&#8217;t have to worry about setting the line object colors or marker styles,
because we already did that when we created the line objects (line **66**). On
line **79**, we do the same thing for the cluster centroid. Since each cluster
only has one centroid value, we pass a single x value and a single y value to
the centroid line object&#8217;s `set_data()` method.

On line **81**, we use the `savefig()` method to save the plot in its current
state as an image, which will occur on every iteration of the while loop that
we&#8217;ll use to animate the algorithm. Afterward, we&#8217;ll use the images
to create a video of the animation. You can comment this line out if you
don&#8217;t want to save images of the animation.

_**IMPORTANT NOTE: A WHILE LOOP IS NOT THE BEST WAY TO ANIMATE IN MATPLOTLIB OR
TO CREATE VIDEOS OF THE ANIMATION!**_ Using a while loop to animate things in
matplotlib works, but it&#8217;s not a good way to animate things. There&#8217;s
an `animation` module in matplotlib that does a better job of this. Saving
individual frames and manually creating a video is also unnecessary&#8211;the
`matplotlib.animation` module does that, too. For this example, though,
I&#8217;d like to keep things simple by avoiding the animation module.
Furthermore, I&#8217;d like to demonstrate the &#8220;hard way&#8221; before
demonstrating the correct way. Plus, we&#8217;ll get to see an example of how to
create videos from the terminal with ffmpeg, which, really, is what the
matplotlib animation module does behind the scenes, anyway. We will, however,
use the animation module in the next post.

Getting back to the current exercise: lines **84-86** set the axis limits of our
plot to ensure all our data points will be visible. On line **88**, we run the
`updatePlot()` function defined above to initialize the plot. On line **89**, we
turn on interactive plotting with `plt.ion()`. This, ironically, allows us to
continuously update the plot without user interaction, by permitting the rest of
the code to continue executing while the plot is open. Finally, a call to
`plt.show()` is necessary to actually show the plot.

{{< highlight python "linenos=true,linenostart=92" >}}
# Execute and animate the algorithm with a while loop. Note that this is not the
# best way to animate a matplotlib plot--the matplotlib animation module should be
# used instead, but we will use a while loop here for simplicity.
lastCentroids = centroids + 1
while not np.array_equal(centroids, lastCentroids):
    lastCentroids = np.copy(centroids)
    recalcCentroids()
    assignPointsToCentroids()
    iteration += 1
    updatePlot(iteration)

pythonMajorVersion = sys.version_info[0]
if pythonMajorVersion < 3:
    raw_input("Press Enter to continue.")
else:
    input("Press Enter to continue.")
{{< / highlight >}}

At last, we execute the algorithm. The end condition is met when the centroid
locations no longer change. To accomplish this, we create the array
`lastCentroids` and initialize it with an arbitrary set of values that&#8217;s
different from `centroids` to ensure the while loop executes at least once. Note
that we use `np.copy()` on line **97** because the statement
`lastCentroids = centroids` wouldn&#8217;t create a copy of `centroids`
&#8211;instead, it would point to it (i.e., if we used
`lastCentroids = centroids`, `lastCentroids` and `centroids` would point to the
same object; modifying one would modify the other and, since they&#8217;d both
point to the same object, they would always be equal, meaning the loop would
only execute once). This is a quirk of numpy arrays that&#8217;s important to
keep in mind.

That&#8217;s it. Run the script and see what happens. Try running it multiple
times to see how different centroid initializations impact the results. Play
around with the parameters: try different values for K, different numbers of
clusters, and different cluster standard deviations.

# Create a video using ffmpeg

Optionally, we can now combine the saved images (from line **81** in our
`updatePlot()` function) to create a video. There are many ways to do this, but
I&#8217;m going to use ffmpeg. _**REMINDER: THIS IS NOT THE BEST WAY TO CREATE A
VIDEO OF THE ANIMATION!**_ As I mentioned above, using the
`matplotlib.animation` module is a better method. Saving images and manually
creating a video with ffmpeg is a purely instructional exercise.

Open a terminal or command prompt in the same directory as the images and type
the following command:

{{< highlight bash >}}
ffmpeg -r 1 -i %d.png -vcodec h264 -pix_fmt yuv420p output.mp4
{{< / highlight >}}

The `-r` option sets the framerate. `-i` sets the input file name or
pattern&#8211;in this case, we use the pattern `%d.png` to specify that the
input file names contain an integer with a .png extension. `-vcodec` tells
ffmpeg which video codec to utilize for encoding the file. You can view the
ffmpeg codecs available on your system by running the command `ffmpeg -codecs`.
`-pix_fmt` sets the pixel format to use. In this example, we use a format called
yuv420p. YUV is simply a color space like RGB or HSV, and our selection of a YUV
pixel format determines how colors are mapped to produce the video. The command
`ffmpeg -pix_fmts` will list all available pixel formats. The last argument is
the name of the output file, `output.mp4`. ffmpeg uses the file extension of the
output file to properly encode the video. Note that most of the arguments to
ffmpeg are optional, with the exception of your input file(s) and output file,
but the optional arguments provide more control over how your input is processed
and how your output is encoded. There are many other options you can specify, as
well. I&#8217;m by no means an expert on ffmpeg, so I&#8217;ll
[ refer
you to the official ffmpeg documentation](https://ffmpeg.org/ffmpeg.html) if you&#8217;d like to learn more.

In the next post, we&#8217;ll generalize the K-means clustering algorithm to any
arbitrary number of dimensions, and we&#8217;ll animate the result using the
`matplotlib.animation` module, as well as tackle several other Python concepts.