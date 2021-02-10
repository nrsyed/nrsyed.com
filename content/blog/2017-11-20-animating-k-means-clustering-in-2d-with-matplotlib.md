---
title: Animating K-means clustering in 2D with matplotlib
author: Najam Syed
type: post
date: 2017-11-21T03:02:29+00:00
url: /2017/11/20/animating-k-means-clustering-in-2d-with-matplotlib/
categories:
  - Machine Learning
tags:
  - K-means clustering
  - machine learning
  - matplotlib
  - Python

---
In the
[previous post]({{< ref "2017-11-12-visualizing-k-means-clustering-in-1d-with-python.md" >}}), we implemented K-means clustering in 1D from scratch with
Python and animated it (the &#8220;wrong&#8221; way) using matplotlib. In this
post, we&#8217;ll do two things: 1) develop an N-dimensional implementation of
K-means clustering that will also facilitate plotting/visualizing the algorithm,
and 2) utilize that implementation to animate the two-dimensional case with
matplotlib the correct way, using the matplotlib animation module.

As before, the aims of this post are twofold: to further explore K-means
clustering and to delve somewhat deeper into Python and matplotlib. In case it
isn&#8217;t clear from the previous post, the objective here is not to utilize
existing libraries for K-means clustering, which are more general, capable, and
optimized than what we&#8217;re doing here (the go-to implementation in Python
being the [scikit-learn][1] machine learning package, which includes, among
other things, [K-means clustering][2]). If your goal is to quickly set up a
robust implementation of K-means clustering, these posts will probably not be of
much help. On the other hand, if you&#8217;re looking to gain a better intuition
for the K-means clustering algorithm, as well as a better understanding of
Python and matplotlib, these posts are for you.

# The result

This is what our script will do by the time we&#8217;re done:

{{< youtube Rrxuq2vNwCM >}}

Read on for the details.

# The code, part 1

This post assumes you&#8217;ve read the last post. Consequently, I won&#8217;t
go into as much detail on some sections of the code that were already discussed
in greater depth previously. We&#8217;re going to create two files. The first
will define a class to perform K-means clustering in any number of dimensions,
and optionally return a generator function that we can use to animate the
algorithm in matplotlib. The second file will actually utilize this to animate
the algorithm in two dimensions. If you&#8217;d like, you can find the two
files, [KMeansND.py][3] and [animKMeans2D.py][4], on Github.

In your favorite text editor, create a file named `KMeansND.py` (or get it from
the Github link above).

{{< highlight python "linenos=true" >}}
import numpy as np

def assignPointsToCentroids(centroids, points):
    '''Determine the centroid to which each point is nearest, and
        store this as an int from 0 to K-1 in classifications.
    '''
    M = points.shape[0]
    K = centroids.shape[0]
    classifications = np.zeros((M,), dtype=np.int)

    for i in range(M):
        smallestDistance = 0
        for k in range(K):
            distance = np.linalg.norm(points[i,:] - centroids[k,:])
            if k == 0:
                smallestDistance = distance
                classifications[i] = k
            elif distance < smallestDistance:
                smallestDistance = distance
                classifications[i] = k
    return classifications
{{< / highlight >}}

The function `assignPointsToCentroids()` performs the first major task of the
K-means clustering algorithm. It accepts an array of centroids and an array of
data points. The `centroids` array must have dimensions K x N, i.e., K rows and
N columns, where K is the number of clusters (the "K" in "K-means") we'd like
the algorithm to find and N is the number of features or coordinates (the "N" in
"N-dimensional"). The `points` array consists of M data points described by the
same N features. Lines **11-20** iterate through each point in `points`, compute
its Euclidean distance from each centroid using the `numpy.linalg.norm()`
method, and assign it to the nearest centroid (cluster). Each of the K
centroids, or clusters, is represented by an integer from 0 to K-1. This is
stored in the array `classifications`, in which each element corresponds to a
data point in `points`.

{{< highlight python "linenos=true,linenostart=23" >}}
def recalcCentroids(centroids, points, classifications):
    '''Recalculate centroid locations for each cluster.'''
    K = centroids.shape[0]
    N = points.shape[1]
    M = points.shape[0]

    newCentroids = np.zeros((K, N))
    for k in range(K):
        if sum(classifications == k) > 0:
            newCentroids[k,:] = (
                np.sum(points[classifications == k,:], axis=0)
                / sum(classifications == k))
        else:
            newCentroids[k,:] = centroids[k,:]
    return newCentroids
{{< / highlight >}}

The function `recalcCentroids()` performs the second major task, which is to use
those cluster classifications to recalculate the centroid of each cluster. This
is done for each cluster `k` by considering only the data points from `points`
belonging to that cluster, which is accomplished by the statement
`points[classifications == k,:]`, then summing each of the N columns (which is
what the option `axis=0` of the numpy function `np.sum()` denotes). Finally, we
divide by the number of points belonging to cluster `k` (equal to
`sum(classifications == k)`). The `if` statement preempts the case where the
_k_th cluster contains zero points, in which case the centroid doesn't change
and we set it equal to the existing value, given by `centroids[k,:]`. Note that,
in some implementations of the algorithm, a cluster with no points assigned to
it is removed, reducing the number of clusters by 1 each time this occurs.

Having defined these functions external to the class (in case we want to use
them by importing this file but without utilizing the class), we now define the
class, named `KMeansND`:

{{< highlight python "linenos=true,linenostart=39" >}}
class KMeansND:
    '''KMeansND(initialCentroids, points)

    PARAMETERS:

    initialCentroids: K x N array of K initial centroids with N
        features/coordinates.

    points: M x N array of M points with N features/coordinates.

    METHODS:

    (centroids, classifications, iterations) = getCentroids()
        Perform K-means clustering. Return a tuple containing the
        array of centroid coordinates, an M x 1 array of point
        classifications, and number of iterations required.

    getGenerator()
        Return a generator function to step through K-means iterations.
        Each call of the generator returns the current centroids,
        classifications, and iteration, beginning with the initial
        centroids and classifications.
    '''
    def __init__(self, initialCentroids, points):
        if initialCentroids.shape[1] != points.shape[1]:
            raise RuntimeError('Dimension mismatch. Centroids and data points'
                + ' must be described by the same number of features.')
        else:
            self.initialCentroids = initialCentroids
            self.points = points
{{< / highlight >}}

`__init__` is a special function in a Python class that's executed whenever an
instance of the class is created. The arguments supplied when creating an
instance of the class are passed to `__init__` &#8212;in this case, those
arguments are `initialCentroids` and `points`. `self` is a special argument used
to identify which instance of the class is being referenced, and is passed
automatically by Python when you create an instance of the class or run a
function that's part of the class (the latter being the reason every function in
our class will take `self` as an argument). Each instance also has its own
"instance variables" or "instance attributes". Instance variables must be
prefixed with `self.` for the same reason&#8212;to identify which instance we're
referring to. Note that the inputs to `__init__` will disappear after the
function completes, just like any other function. Consequently, we have to
assign them to instance variables, identified by `self`, which will be stored in
the instance as long as that instance is alive. This is achieved by the
statements `self.initialCentroids = initialCentroids` and
`self.points = points`. In a way, this is sort of like modifying a global
variable from within a function; anything you do with the function's input
arguments disappears after the function completes, unless the changes are
captured in global variables (or unless they're returned by the function and
used by the caller). Here, instead of modifying global variables, we're using
instance variables.

{{< highlight python "linenos=true,linenostart=70" >}}
def getCentroids(self):
    centroids = np.copy(self.initialCentroids)
    # Initialize lastCentroids to arbitrary value different from centroids
    # to ensure loop executes at least once.
    lastCentroids = centroids + 1
    iteration = 0
    while not np.array_equal(centroids, lastCentroids):
        lastCentroids = np.copy(centroids)
        classifications = assignPointsToCentroids(centroids, self.points)
        centroids = recalcCentroids(centroids, self.points, classifications)
        iteration += 1
    return (centroids, classifications, iteration)
{{< / highlight >}}

The function `getCentroids()` executes the K-means clustering algorithm by
alternately calling `assignPointsToCentroids()` and `recalcCentroids()` until
the centroids no longer change. The function returns a tuple containing the
final centroids, the final cluster classifications, and the number of iterations
required to converge to the solution. We would use this function if we only
cared about the solution.

However, our goal is to animate the algorithm. This means we're at least as
interested in the journey as we are in the destination. We need to be able to
return not just the solution, but also the state of the algorithm (centroids and
classifications) at every iteration. Normally, a function returns a single value
or set of values via the `return` statement. Instead of the `return` statement,
we can use a `yield` statement in a function. The `yield` statement interrupts
the function, gives control back to the caller, and returns the variables we
specify (if any) in their current state. This is called a generator. Consider
the function `_generatorFunc()` below.

{{< highlight python "linenos=true,linenostart=83" >}}
def _generatorFunc(self):
    centroids = np.copy(self.initialCentroids)
    lastCentroids = centroids + 1
    iteration = 0
    initialIteration = True
    while not np.array_equal(centroids, lastCentroids):
        if initialIteration:
            classifications = assignPointsToCentroids(centroids, self.points)
            initialIteration = False
        else:
            lastCentroids = np.copy(centroids)
            classifications = assignPointsToCentroids(centroids, self.points)
            centroids = recalcCentroids(centroids, self.points, classifications)
            iteration += 1
        yield (centroids, classifications, iteration)
{{< / highlight >}}

It looks pretty similar to `getCentroids()`, right? That's because it's running
the exact same K-means clustering routine. The major difference is that, instead
of placing a `return` statement at the end of the function after the while loop,
we've placed a `yield` statement _in_ the while loop. By doing this, we're
telling Python that, after each iteration of the loop, the code in the function
should yield control to the caller, freeze the state of all the variables in
`_generatorFunc()`, and return the "frozen" values of
`(centroids, classifications, iteration)` to the caller. Each time the generator
is called, it resumes running the code in the function from the state in which
it was last frozen. This way, we can step through individual iterations of the
while loop by repeatedly calling the generator.

Note that I've used the terms "generator function" and "generator."
`_generatorFunc()` is an example of a generator function, which is essentially
any function that contains a `yield` statement. When you call a generator
function, it returns a generator, also known as a generator object. This
generator object is what actually steps through the function code. Each time the
generator object is called, it "generates" the next value. If the number of
values that can be generated is finite, as with a for loop or a while loop that
reaches its end condition, then the generator object cannot be used anymore
after returning its final value&#8212;i.e., it is possible for a generator
object to be exhausted, after which it cannot be reused. The generator function,
though, can be called any number of times, and will return a fresh generator
object each time.

The other difference in `_generatorFunc()`, as opposed to `getCentroids()`, is
the use of an if-else statement, which, on the first iteration (i = 0), returns
the initial centroids and initial classifications. This way, the generator
captures the initial state of the system on the first iteration, then proceeds
with the changes to the centroids and classifications in all subsequent
iterations. A final note on this function has to do with the name:
`_generatorFunc()`. It starts with a single underscore, which, in Python,
indicates that it's meant for internal use within the class and is not intended
to be accessed from outside the class, although this is not strictly enforced by
the language. What's the point of this, in this case? Well, the
`matplotlib.animation` module can take a generator _function_ as an input, so
we'll create a second function within the `KMeans2D` class that returns the
generator function we just defined:

{{< highlight python "linenos=true,linenostart=99" >}}
def getGeneratorFunc(self):
    return self._generatorFunc
{{< / highlight >}}

This isn't strictly necessary (you could just access the generator function
directly), but this way, our class only contains (public) methods that return
exactly what we need.

# The code, part 2

Now, create a file named `animKMeans2D.py`, or get it from the Github link
above.

{{< highlight python "linenos=true" >}}
from __future__ import division
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import colorsys
import sys
from datetime import datetime
from KMeansND import *
{{< / highlight >}}

Among our imports is the `KMeansND` file we just wrote, as well as `__future__`,
a special module that provides functionality from future releases, allowing for
compatibility between different versions of Python. A discussion of the
`__future__` module is outside the scope of this post, but the [Python
documentation][5] may be helpful. In this case, we import `division`. In Python
2, the `/` operator performs integer division, e.g., `3 / 2` produces `1`. In
Python 3, the `/` operator performs float division, so `3 / 2` returns `1.5`.
Importing `division` from `__future__` makes the second case the default, so
code written for Python 3 will work in Python 2.

{{< highlight python "linenos=true,linenostart=10" >}}
K = 12   # Number of clusters (centroids) to compute
numClusters = 12     # Number of clusters to generate
ptsPerCluster = 100
varianceCoeff = 0.01    # This controls the spread of clustered points

xCenterBounds = (-4, 4)
yCenterBounds = (-4, 4)

covariance = np.array([[varianceCoeff * (xCenterBounds[1] - xCenterBounds[0]), 0],
                       [0, varianceCoeff * (yCenterBounds[1] - yCenterBounds[0])]])
{{< / highlight >}}

First, we set some initial parameters. Since we're working in multiple
dimensions this time, we'll use the numpy method
`np.random.multivariate_normal()`, which requires a [covariance matrix][6],
rather than a scalar standard deviation, as one of its inputs.

{{< highlight python "linenos=true,linenostart=21" >}}
def generateClusters():
    centers = np.random.random_sample((numClusters, 2))
    centers[:,0] = (
        centers[:,0] * (xCenterBounds[1] - xCenterBounds[0]) + xCenterBounds[0])
    centers[:,1] = (
        centers[:,1] * (yCenterBounds[1] - yCenterBounds[0]) + yCenterBounds[0])

    points = np.zeros((numClusters * ptsPerCluster, 2))
    for i in range(numClusters):
        points[i*ptsPerCluster : (i+1)*ptsPerCluster,:] = (
            np.random.multivariate_normal(centers[i,:], covariance, ptsPerCluster))
    return points

def initializeCentroids(K, points):
    '''Randomly select K points as the initial centroid locations'''
    M = points.shape[0] # number of points
    indices = []
    while len(indices) < K:
        index = np.random.randint(0, M)
        if not index in indices:
            indices.append(index)
    initialCentroids = points[indices,:]
    return initialCentroids
{{< / highlight >}}

Next, we create two functions to initialize the data points and the centroids.
`generateClusters()` randomly selects `numClusters` sets of (x, y) coordinates
within the space defined by `xCenterBounds` and `yCenterBounds`, using the numpy
function `np.random.random_sample()` to select actual cluster centers and
`np.random.multivariate_normal()` to distribute the desired number of data
points around each center. The data points are returned in the `points` array,
where each row corresponds to a single data point and each column to a feature
or coordinate&#8212;in this case, column 0 contains the x coordinates and column
1 contains the y coordinates. The second function, `initializeCentroids()`,
selects K unique data points from our array of points to serve as the initial
centroids.

{{< highlight python "linenos=true,linenostart=45" >}}
def animate(clusterInfo):
    (currentCentroids, classifications, iteration) = clusterInfo
    for k in range(K):
        updatedClusterData = points[classifications == k,:]
        clusterObjList[k].set_data(updatedClusterData[:,0], updatedClusterData[:,1])
        centroidObjList[k].set_data(currentCentroids[k,0], currentCentroids[k,1])
    iterText.set_text('i = {:d}'.format(iteration))
{{< / highlight >}}

The `animate()` function will be called by matplotlib's animation module to draw
each frame of the animation. In our case, each frame corresponds to one
iteration of the while loop in our implementation of the algorithm. Our
`animate()` function takes one argument, `clusterInfo`, which, from line **46**,
you might surmise is an iterable containing three elements: an array of centroid
coordinates, the classifications that pair each point with a cluster, and the
current iteration. It's no coincidence that these three elements are exactly
what the generator from our `KMeansND` class yields. After each iteration of the
algorithm, the output of the generator will serve as the input to `animate()`,
which unpacks the tuple containing the centroids, classifications, and
iteration, and then uses these to update the plot. Note that this function
references global variables that haven't been defined yet: `clusterObjList`,
which contains references to the line object for the data points of each
cluster, `centroidObjList`, which contains references to the line object for
each cluster centroid, and `iterText`, which is the handle for the iteration
text annotation.

{{< highlight python "linenos=true,linenostart=53" >}}
# Create figure and axes. Initialize cluster and centroid line objects.
fig, ax = plt.subplots()
clusterObjList = []
centroidObjList = []
for k in range(K):
    clusterColor = tuple(colorsys.hsv_to_rgb(k / K, 0.8, 0.8))

    clusterLineObj, = ax.plot([], [], ls='None', marker='x', color=clusterColor)
    clusterObjList.append(clusterLineObj)

    centroidLineObj, = ax.plot([], [], ls='None', marker='o',
        markeredgecolor='k', color=clusterColor)
    centroidObjList.append(centroidLineObj)
iterText = ax.annotate('', xy=(0.01, 0.01), xycoords='axes fraction')

{{< / highlight >}}

Now, we initialize the plot. This involves setting the color, marker, and
linestyle for each cluster and each cluster centroid. We streamline the process
of setting the color, compared to the previous post, with the one-line statement
on line **58**.

{{< highlight python "linenos=true,linenostart=68" >}}
def setAxisLimits(ax, points):
    xSpan = np.amax(points[:,0]) - np.amin(points[:,0])
    ySpan = np.amax(points[:,1]) - np.amin(points[:,1])
    pad = 0.05
    ax.set_xlim(np.amin(points[:,0]) - pad * xSpan,
        np.amax(points[:,0]) + pad * xSpan)
    ax.set_ylim(np.amin(points[:,1]) - pad * ySpan,
        np.amax(points[:,1]) + pad * ySpan)
{{< / highlight >}}

We'll also box up the task of setting axis limits based on the span of the data
points into a dedicated function. The value we choose for `pad` simply provides
a little white space at the edges of the plot window so that the data points
aren't located right at the edges of the plot. This will also ensure that the
iteration text annotation is readable and isn't shrouded by data points.

{{< highlight python "linenos=true,linenostart=77" >}}
# Initialize data and K-means clustering. Show and animate plot.
points = generateClusters()
initialCentroids = initializeCentroids(K, points)
genFunc = KMeansND(initialCentroids, points).getGeneratorFunc()
setAxisLimits(ax, points)
animObj = animation.FuncAnimation(fig, animate, frames=genFunc,
    repeat=True, interval=500)
plt.ion()
plt.show()
{{< / highlight >}}

At last, the main event. We generate the data points on line **78**, then
initialize the centroids. On line **80**, we assign our generator function to
the variable `genFunc`. Finally, on line **82**, we create an animation object
from the `FuncAnimation()` class of the matplotlib `animation` module.
`FuncAnimation()` utilizes a function to update the plot at every frame. In this
case, we've conveniently named that function `animate()`, and it's the second
positional argument to `FuncAnimation()`, the first argument being the handle
for the figure that contains the animation, which we named `fig` on line **54**.
The optional `frames` argument supplies data to `animate()`. `frames` doesn't
have to be a generator function; it can simply be a scalar value, or an array of
integers, or nothing (see the [matplotlib documentation][7] for more
information). In this case, our `animate()` function needs the values from the
generator to correctly update the plot. The `repeat` argument sets whether or
not the animation loops after completion, and `interval` sets the time, in
milliseconds, between frame updates.

As in the previous post, we turn on interactive plotting with `plt.ion()` to
allow other code to execute while the plot is open. In this case, the other code
is the following command line user interface:

{{< highlight python "linenos=true,linenostart=87" >}}
# Construct interactive terminal interface.
inputMessage = ('\nMake a selection:\n'
    + '(1) Randomize clusters and centroids\n'
    + '(2) Randomize centroids only\n'
    + '(3) Save animation to mp4\n'
    + '(4) Exit\n')
while 1:
    if sys.version_info[0] < 3:
        selection = raw_input(inputMessage)
    else:
        selection = input(inputMessage)

    if selection == '1':
        animObj._stop()
        print('\nRandomizing clusters and centroids...')
        points = generateClusters()
        initialCentroids = initializeCentroids(K, points)
        genFunc = KMeansND(initialCentroids, points).getGeneratorFunc()
        setAxisLimits(ax, points)
        animObj = animation.FuncAnimation(fig, animate, frames=genFunc,
            repeat=True, interval=500)
    elif selection == '2':
        animObj._stop()
        print('\nRandomizing centroids...')
        initialCentroids = initializeCentroids(K, points)
        genFunc = KMeansND(initialCentroids, points).getGeneratorFunc()
        animObj = animation.FuncAnimation(fig, animate, frames=genFunc,
            repeat=True, interval=500)
        fig.canvas.draw()
    elif selection == '3':
        time = datetime.now()
        timeStr = (str(time.year) + str(time.month) + str(time.day)
            + str(time.hour) + str(time.minute) + str(time.second))
        ffmpegWriterClass = animation.writers['ffmpeg']
        ffmpegWriterObj = ffmpegWriterClass(fps=1, extra_args=['-vcodec', 'h264'])
        filename = timeStr + '_KMeans2D.mp4'
        print('\nSaving file ./' + filename)
        animObj.save(filename, writer=ffmpegWriterObj)
    elif selection == '4':
        exit()
    else:
        print('\nInvalid selection.\n')
{{< / highlight >}}

This interface is optional, but it's nifty because it allows you to 1) choose a
new set of randomly selected data points (with new initial centroids), 2) choose
a new set of initial centroids for the current set of data points, and 3) save
the current animation to an mp4 file with ffmpeg, all without re-running or
modifying the script. The if-else statement on lines **94-97** checks whether
the interpreter is running from Python 2 or Python 3; in Python 2, the method
used to process user input is `raw_input()`, but in Python 3, that functionality
has been replaced by `input()`. If the user opts to save the animation (by
entering '3'), we first use the built-in `datetime` module to construct a
unique, timestamped filename. Lines **120-124** utilize [matplotlib's
`MovieWriter` class][8] to help write the animation to a video file. First, we
assign a reference to a matplotlib MovieWriter class on line **120**. You can
see the writers available on your system with the command
`animation.writers.list()`. In this case, we've chosen ffmpeg. Next, we
instantiate the ffmpeg writer class on line **121**; the constructor for [this
class][9] has one required input argument, the framerate, given by `fps`. We can
also supply additional options to ffmpeg via the `extra_args` keyword argument,
which takes a list of sequential option-value pairs in the form of strings. We
could also supply any of the options from [the previous post][10] to ffmpeg
here, if we wanted to. Here, I've only provided the video codec to be used for
encoding the video. See the previous post for more information on the use of
ffmpeg. Lastly, to actually create the video, we call the `save()` method of the
animation object and supply it with the writer object we just created so it
knows what parameters and options to use for saving the video.

That's it&#8212;one implementation of 2D K-means clustering with matplotlib. Try
playing around with the algorithm parameters to visualize how the results change
when the parameters are varied, or try messing around with the code to see what
else you can do with matplotlib.

[1]: http://scikit-learn.org/stable/
[2]: http://scikit-learn.org/stable/modules/generated/sklearn.cluster.KMeans.html
[3]: https://github.com/nrsyed/examples/blob/master/KMeansND.py
[4]: https://github.com/nrsyed/examples/blob/master/animKMeans2D.py
[5]: https://docs.python.org/2/library/__future__.html
[6]: https://en.wikipedia.org/wiki/Covariance_matrix
[7]: https://matplotlib.org/api/_as_gen/matplotlib.animation.FuncAnimation.html
[8]: https://matplotlib.org/api/_as_gen/matplotlib.animation.MovieWriter.html#matplotlib.animation.MovieWriter
[9]: https://matplotlib.org/api/_as_gen/matplotlib.animation.FFMpegWriter.html#matplotlib.animation.FFMpegWriter
[10]: {{< ref "2017-11-12-visualizing-k-means-clustering-in-1d-with-python.md" >}}