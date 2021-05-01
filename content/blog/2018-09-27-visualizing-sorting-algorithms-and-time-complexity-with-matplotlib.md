---
title: Visualizing sorting algorithms and time complexity with matplotlib
author: Najam Syed
type: post
date: 2018-09-28T00:37:03+00:00
url: /2018/09/27/visualizing-sorting-algorithms-and-time-complexity-with-matplotlib/
categories:
  - Algorithms
tags:
  - bubble sort
  - insertion sort
  - matplotlib
  - merge sort
  - Python
  - quicksort
  - selection sort
  - sorting
katex: true
markup: "mmark"

---
In this post, we&#8217;ll cover the use of the Python matplotlib package to
animate several traditional sorting algorithms. While I&#8217;ll briefly touch
on the sorting algorithms in question, there&#8217;s no shortage of resources
and tutorials on these topics floating around the internet, so the purpose of
this post is not necessarily to delve into the algorithms themselves, but to
focus on Python- and matplotlib-specific implementation details, supplemented
with a bit of discussion on algorithm complexity. As always, let&#8217;s begin
with the end result:

{{< youtube cgNFT4CadL4 >}}

# Time complexity

The performance of an algorithm is generally measured by its time complexity,
which is often expressed in Big O notation (not to be confused with The Big O,
an anime featuring a giant robot and [a catchy theme song][1] that I find myself
whistling whenever reading about algorithmic complexity). Big O notation tells
us the worst-case runtime of an algorithm that has $$n$$ inputs. For example, an
algorithm that takes the same amount of time regardless of the number of the
inputs is said to have constant, or $$O(1)$$, complexity, whereas an algorithm
whose runtime increases quadratically with the number of inputs has a complexity
of $$O(n^2)$$, and so on.

In this post, we&#8217;ll quantify the time complexity with the number of
operations performed, where I&#8217;ve defined &#8220;operations&#8221; to
include swaps (exchanging the position of one element with that of another
element in an array) and/or comparisons (checking if one element of an array is
larger than or smaller than another element). This metric will give us an idea
of how each sorting algorithm scales as the number of elements that must be
sorted increases.

# The code and the algorithms

The code is
[available on my Github](https://github.com/nrsyed/sorts/blob/master/python/sorts.py). Download `sorts.py` and follow along. Note that this
script takes advantage of Python&#8217;s `yield from` feature, or generator
delegation, which was
[introduced by PEP 380 in Python 3.3](https://docs.python.org/3/whatsnew/3.3.html#pep-380). Therefore, you&#8217;ll need Python 3.3
or higher for this script to work.

First, the imports:

{{< highlight python "linenos=true" >}}
import random
import time
import matplotlib.pyplot as plt
import matplotlib.animation as animation
{{< / highlight >}}

The `random` and `time` modules will be used to generate a random array of
numbers to actually demonstrate the sorting algorithms (we&#8217;ll get the
current time from `time` to seed the random number generator). The matplotlib
`pyplot` and `animation` modules will allow us to animate the algorithms.

{{< highlight python "linenos=true,linenostart=8" >}}
def swap(A, i, j):
    """Helper function to swap elements i and j of list A."""

    if i != j:
        A[i], A[j] = A[j], A[i]
{{< / highlight >}}

We&#8217;ll also define a helper function to swap the positions of two elements
in an array. Note that we take advantage of Python&#8217;s
[assignment rules](https://docs.python.org/3/reference/simple_stmts.html#assignment-statements) and
[evaluation order](https://docs.python.org/3/reference/expressions.html#evaluation-order) for assignments to assign both elements on one line.

The subsequent subsections will detail the implementations of the different
sorting algorithms. For the purposes of this post, the goal is to sort an array
of integers in ascending order (smallest value to largest value).

## Bubble sort

In bubble sort, each element is compared to the next element. During each
iteration, if the next element sorts before the current element (i.e., if the
next element is greater than the current element), the two are swapped. This is
performed for all elements of the array, causing large elements to
&#8220;bubble&#8221; to the end of the array. It looks something like this:

{{< youtube I9U2I-Y_uNw >}}

This process (which involves $$n-1$$ comparisons on the first iteration, with
one less comparison/swap on each subsequent iteration) is repeated $$n-1$$ times
until all the elements are sorted, producing a time complexity of $$O(n^2)$$.
The function used to create the animation in the video above is as follows:

{{< highlight python "linenos=true,linenostart=14" >}}
def bubblesort(A):
    """In-place bubble sort."""

    if len(A) == 1:
        return

    swapped = True
    for i in range(len(A) - 1):
        if not swapped:
            break
        swapped = False
        for j in range(len(A) - 1 - i):
            if A[j] > A[j + 1]:
                swap(A, j, j + 1)
                swapped = True
            yield A
{{< / highlight >}}

On each iteration of the outer loop, we check to see if at least one swap was
performed on the previous iteration using the variable `swapped`. If no swaps
were performed, that means the array has been sorted. Also note that we use the
`yield` statement to turn this function into a generator. A generator is an
iterator, essentially a &#8220;frozen function&#8221; that remembers the state
of its variables between calls. In this case, the generator stops when the
`yield` statement is encountered and returns a reference to the list `A`. The
next time the generator is called, it runs through the loop(s) and stops again
at the `yield` statement. Another thing to keep in mind is that, in Python,
lists (like `A` in the code above) are passed by reference, not by value. So,
when we modify the input list `A` by swapping elements, we&#8217;re modifying
the original list, not a copy of the list. Thus, it&#8217;s not strictly
necessary for us to return `A` with `yield A` each time&#8212;we could simply
`yield`. However, it&#8217;s useful because it allows us to call the generator
from a function that may not have access to the original list `A`.

The exact time complexity of the algorithm can be found from the sequence

$$(n-1) + (n-2) + \dots + (n-(n-1))$$

which represents the number of operations performed at each iteration as a
function of the number of elements $$n$$ in the list (array) `A`. The sequence
can be written as the following sum:

$$T_n = \sum_{i=1}^{n-1} (n-i)$$

where $$T_n$$ is the time (or number of operations) required to sort $$n$$
elements. The sum above can be rewritten as two sums:

$$T_n = \sum_{i=1}^{n-1}n\ - \sum_{i=1}^{n-1}i$$

The first sum in the equation above simply evaluates to $$n(n-1)$$. The second
sum is a
[triangular number sum](https://en.wikipedia.org/wiki/Triangular_number),
which turns out to be $$\frac{1}{2}n(n-1)$$. Putting these together:

$$T_n = n(n-1)\ - \frac{n(n-1)}{2} = \frac{n(n-1)}{2} = \frac{n^2 - n}{2}$$

which is where $$O(n^2)$$ comes from (keeping only the highest order term and
ignoring coefficients). This can be seen in the video above, where bubble sort
took 43 operations (swaps) to sort 10 elements and 4291 operations (swaps) to
sort 100 elements&#8212;both of which match the theoretical worst-case values of
$$T_{10} = \frac{1}{2}(10)(10-1) = 45$$ and $$T_{100} = \frac{1}{2}(100)(100-1)
= 4950$$, respectively. The actual numbers can sometimes be lower than the
theoretical values because the Big O complexity provides an upper bound on the
complexity, and the array may end up being sorted before the maximum number of
iterations has been completed.

## Insertion sort

Insertion sort works by iterating through the array once, in the process
effectively dividing the array into a sorted portion and an unsorted portion. On
each iteration, it inserts the current element from the unsorted portion into
the correct position in the sorted portion via a series of swaps. Hopefully, a
visual helps (it is, after all, the entire point of this post).

{{< youtube PVFDaLcOx8c >}}

The code, shown below, is relatively simple. Like bubble sort, it only contains
one `yield` statement, which is encountered after each swap.

{{< highlight python "linenos=true,linenostart=31" >}}
def insertionsort(A):
    """In-place insertion sort."""

    for i in range(1, len(A)):
        j = i
        while j > 0 and A[j] < A[j - 1]:
            swap(A, j, j - 1)
            j -= 1
            yield A
{{< / highlight >}}

What's the time complexity of this algorithm? Up to one swap is performed on the
first iteration, up to two on the second, and so on, giving us the following:

$$T_n = \sum_{i=1}^{n-1}i = 1 + 2 + \dots + (n-1)$$

As with bubble sort, this sums to $$\frac{1}{2}(n^2-n)$$, for a complexity of
$$O(n^2)$$.

## Merge sort

In merge sort, the array to be sorted is subdivided into two subarrays. Each of
those subarrays is sorted by recursively calling the merge sort algorithm on
them, after which the final sorted array is produced by merging the two (now
sorted) subarrays. Here it is visually:

{{< youtube iNW9_Jog8hM >}}

The following code for merge sort is a little more interesting than the last
several functions because it relies on generator delegation, a relatively new
feature in Python that allows you to easily call and exhaust a generator from
within another generator via `yield from`.

{{< highlight python "linenos=true,linenostart=41" >}}
def mergesort(A, start, end):
    """Merge sort."""

    if end <= start:
        return

    mid = start + ((end - start + 1) // 2) - 1
    yield from mergesort(A, start, mid)
    yield from mergesort(A, mid + 1, end)
    yield from merge(A, start, mid, end)
    yield A
{{< / highlight >}}

Observe that, given an array, we split it down the middle into two subarrays,
call `mergesort()` on each of them, then call a helper function `merge()` to
combine the results of the two sorted subarrays. Each call to `mergesort()`
yields from additional calls to `mergesort()`, then yields from a call to the
helper function, and finally yields the sorted array. It might help to see what
`merge()` is doing.

{{< highlight python "linenos=true,linenostart=53" >}}
def merge(A, start, mid, end):
    """Helper function for merge sort."""

    merged = []
    leftIdx = start
    rightIdx = mid + 1

    while leftIdx <= mid and rightIdx <= end:
        if A[leftIdx] < A[rightIdx]:
            merged.append(A[leftIdx])
            leftIdx += 1
        else:
            merged.append(A[rightIdx])
            rightIdx += 1

    while leftIdx <= mid:
        merged.append(A[leftIdx])
        leftIdx += 1

    while rightIdx <= end:
        merged.append(A[rightIdx])
        rightIdx += 1

    for i, sorted_val in enumerate(merged):
        A[start + i] = sorted_val
        yield A
{{< / highlight >}}

In `merge()`, we're creating a new array (`merged`), then appending the next
smallest number from the correct subarray to `merged` until all the elements
from one of the subarrays have been appended to the new array. Then, we iterate
through the remaining subarray and add all its elements to `merged`, after which
the values are copied from the temporary array to the original array `A`.

In other words, the original array is first divided into two arrays, after which
each subarray is divided into two arrays, and so on. For example, if our
original array had 8 elements, it would be divided into two subarrays with 4
elements each, each of which would be divided into subarrays of 2 elements, and
finally 1 element, like this:

8<br>
4, 4<br>
2, 2, 2, 2<br>
1, 1, 1, 1, 1, 1, 1, 1

An array with 1 element is already sorted, so no work needs to be done on the
last (bottom) "layer." That leaves three layers containing arrays that must be
sorted. There's a pattern here&#8212;because we divide each (sub)array in half
each time, we end up with $$\mathrm{log}_2 n$$ layers, each of which contains
$$n$$ elements that must be sorted (one array in the top layer containing
$$n=8$$ elements, two arrays in the second layer each containing
$$\frac{1}{2}n=4$$ elements, and four arrays in the third layer each containing
$$\frac{1}{4}n=2$$ elements). Thus, this algorithm requires $$n\mathrm{log}_2
n$$ operations and is said to have a worst-case time complexity of
$$O(n\mathrm{log}n)$$, termed quasilinear time complexity, which is a
significant improvement over bubble sort and insertion sort.

## Quicksort

Like merge sort, quicksort is also usually implemented as a recursive algorithm
that divides an array into smaller subarrays (or sub-segments of the original
array) and sorts each subarray. Unlike merge sort, it achieves this by selecting
one element from the unsorted array, called the "pivot," then swapping values
such that all elements smaller than the pivot value are on one side of the array
and all elements larger than the pivot are on the other side. This process is
known as "partitioning." Quicksort is then applied again to each side. Here it
is animated:

{{< youtube NrrAKZMJ50c >}}

Here's the code for this implementation of quicksort.

{{< highlight python "linenos=true,linenostart=80" >}}
def quicksort(A, start, end):
    """In-place quicksort."""

    if start >= end:
        return

    pivot = A[end]
    pivotIdx = start

    for i in range(start, end):
        if A[i] < pivot:
            swap(A, i, pivotIdx)
            pivotIdx += 1
        yield A
    swap(A, end, pivotIdx)
    yield A

    yield from quicksort(A, start, pivotIdx - 1)
    yield from quicksort(A, pivotIdx + 1, end)
{{< / highlight >}}

As both the code above and the code for merge sort have shown, a generator can
contain any number and combination of `yield` statements and `yield from`
statements.

The time complexity of quicksort is, well, a little more complex than the
previous examples. In the worst-case scenario, the pivot ends up being the
largest (or smallest) value in the array, in which case partitioning hasn't
helped and, for an array or subarray of length $$n$$, has left us with one
subarray of length $$1$$ and one of length $$n-1$$ instead of two subarrays each
containing approximately $$\frac{1}{2}n$$ elements. Thus, the worst-case time
complexity for quicksort is $$O(n^2)$$. However, this depends on how the pivot
is chosen. It turns out that the average-case time complexity, in which
partitioning roughly splits each array or subarray in half like merge sort, is
$$\Theta(n\mathrm{log}n)$$ ("Big theta" notation, which uses $$\Theta$$, is
often used to describe the average-case complexity of an algorithm).

## Selection sort

We now arrive at selection sort, the last sorting algorithm we'll consider in
this post. Selection sort is similar to insertion sort in that there's a sorted
portion of the array and an unsorted portion. However, in selection sort, the
next element to add to the sorted portion is determined by finding the minimum
value from the unsorted portion, which looks like this:

{{< youtube HQpmr2peF0M >}}

And here is the code:

{{< highlight python "linenos=true,linenostart=100" >}}
def selectionsort(A):
    """In-place selection sort."""
    if len(A) == 1:
        return

    for i in range(len(A)):
        # Find minimum unsorted value.
        minVal = A[i]
        minIdx = i
        for j in range(i, len(A)):
            if A[j] < minVal:
                minVal = A[j]
                minIdx = j
            yield A
        swap(A, i, minIdx)
        yield A
{{< / highlight >}}

On the first iteration, the algorithm searches through $$n$$ elements to find
the minimum, then swaps it with the first element. On the second iteration, it
searches through $$n-1$$ elements to find the minimum, then swaps it with the
second, and so on for the remaining iterations. Counting each lookup/comparison
to find the minimum as one operation and each swap as one operation, we can
express the total number of operations with the following sum.

$$T_n = \sum_{i=1}^{n-1} (n-i+1) + 1$$

Rewriting this as two sums and using the results from earlier in this post:

$$\sum_{i=1}^{n-1}(n-i) + \sum_{i=1}^{n-1}2 = \frac{n^2-n}{2} + 2(n-1)$$

Rewriting and combining terms:

$$T_n = \frac{1}{2}n^2 + \frac{3}{2}n - 2 = \frac{n^2 + 3n - 4}{2}$$

Thus, this algorithm also has a time complexity of $$O(n^2)$$.

## Animating the algorithms with matplotlib

Finally, this brings us to the fun part: animating the algorithms. For brevity's
sake, I'll skip the part of the script that creates and randomizes a list `A` of
`N` unique, consecutive integers. Instead, let's jump to the part that
instantiates one of the generator functions defined above based on user input:

{{< highlight python "linenos=true,linenostart=131" >}}
if method == "b":
    title = "Bubble sort"
    generator = bubblesort(A)
elif method == "i":
    title = "Insertion sort"
    generator = insertionsort(A)
elif method == "m":
    title = "Merge sort"
    generator = mergesort(A, 0, N - 1)
elif method == "q":
    title = "Quicksort"
    generator = quicksort(A, 0, N - 1)
else:
    title = "Selection sort"
    generator = selectionsort(A)
{{< / highlight >}}

Having obtained the appropriate generator, let's create a matplotlib figure and
axis to serve as the canvas for our animation.

{{< highlight python "linenos=true,linenostart=148" >}}
fig, ax = plt.subplots()
ax.set_title(title)
{{< / highlight >}}

`fig` and `ax` are handles to our plot figure and axis, respectively, allowing
us to manipulate them in an object-oriented manner. Next, we'll initialize a bar
plot (incidentally, "bar plot" sounds like a scheme hatched at a pub by a couple
of friends who've had a few too many shots of tequila) in which each bar will
correspond to one element of the list, and the height of a given bar will
correspond to its value; the bar corresponding to the integer 7, for example,
will have a height of 7 units measured along the y axis.

{{< highlight python "linenos=true,linenostart=154" >}}
bar_rects = ax.bar(range(len(A)), A, align="edge")
{{< / highlight >}}

This is achieved by calling `bar()` on the axis. The argument `align="edge"`
causes the left side of the bars to line up with the x-axis indices (instead of
the middle of the bars being aligned with the x-axis indices). The method
returns a list of
[matplotlib  Rectangle objects](https://matplotlib.org/api/_as_gen/matplotlib.patches.Rectangle.html), which we store in `bar_rects`.
These `Rectangle` objects contain attributes like the height and width of each
bar (rectangle).

Next, we create a text label on the axis to display the number of operations.

{{< highlight python "linenos=true,linenostart=164" >}}
text = ax.text(0.02, 0.95, "", transform=ax.transAxes)
{{< / highlight >}}

The first two arguments to `text()` are the coordinates of the text label origin
as a decimal fraction of the lengths of the x and y axes, respectively. The
third argument is the text to display, which I've initialized to nothing via
`""`. The keyword argument `transform=ax.transAxes` specifies that the
coordinates given by the first two arguments should be interpreted as axis
fractions rather than data coordinates.

Next, we define a function, `update_fig()`, which, as the name suggests, will be
used to update the figure for each frame of the animation. Specifically, this
function will be passed to
[matplotlib.animation.FuncAnimation()](https://matplotlib.org/api/_as_gen/matplotlib.animation.FuncAnimation.html), the matplotlib animation
module class that calls it to update the figure.

{{< highlight python "linenos=true,linenostart=176" >}}
iteration = [0]
def update_fig(A, rects, iteration):
    for rect, val in zip(rects, A):
        rect.set_height(val)
    iteration[0] += 1
    text.set_text("# of operations: {}".format(iteration[0]))
{{< / highlight >}}

Observe that I've defined `update_fig()` to accept the list `A` as an input,
which it uses to update the height of each bar (rectangle) using its
`set_height()` method. Also observe that, though `update_fig()` receives no
reference to the plot axis the way we've defined it, it does take `rects`, which
is a reference to a list of bar plot rectangles.

Furthermore, notice how we define a list of one element (`0`) called
`iteration`. This will be passed to `update_fig()` as well. Its single element
will be used to keep track of the number of iterations, or operations, that the
algorithm has performed up to the current frame. Why a list with one element?
Because a simple integer like `iteration = 0` cannot be passed by reference,
only by value, unlike a list, which is passed by reference&#8212;thus, we can
preserve the number of iterations (number of operations) between frames. If this
were C++, we could simply pass `iteration` by reference or via a pointer, but
this is not possible in Python. We could have achieved the same result in Python
in other ways, as well (like use of the `global` or `nonlocal` statements).

{{< highlight python "linenos=true,linenostart=183" >}}
anim = animation.FuncAnimation(fig, func=update_fig,
    fargs=(bar_rects, iteration), frames=generator, interval=1,
    repeat=False)
plt.show()
{{< / highlight >}}

Finally, we instantiate the `FuncAnimation` object. We pass it the generator
function corresponding to the algorithm, conveniently named `generator`, as the
source for the frames via the `frames` keyword argument. Each frame of the
animation corresponds to one iteration of the generator, i.e., to one `yield`
statement in the generator function. After each `yield`, the animation object
passes the value returned by the generator (the list `A` from `yield A`) to
`update_fig()`. Optionally, the animation object can also pass other arguments
to `update_fig()`, which can be specified via the `fargs` keyword argument. In
this case, I've opted to pass `bar_rects` and `iteration` so `update_fig()` can
actually update the bar plot rectangles and the text label.

On the last line, we call `plt.show()` to show the plot and let the animation do
its thing.

# Final notes

The implementations of the algorithms discussed in this post have been written
specifically to expose a lot of the inner workings and, more importantly, to
`yield` at key operations, allowing us to count the total number of operations
required to sort a given array based on the number of generator iterations. Many
of them could be written more succinctly, but that wasn't the point of this
post. For example, selection sort can be rewritten into a two-line function
using Python's built-in `min()` method:

{{< highlight python >}}
def selectionsort(A):
    for i in range(len(A) - 1):
        swap(A, i, A.index(min(A[i:])))
{{< / highlight >}}

However, this wouldn't allow us to animate and count the number of operations
needed to actually sort the list.

Anyway, I hope this post has helped demonstrate the use of generators, the
`yield` statement, and the `yield from` statement to produce animations with
matplotlib, as well as provided a better understanding of the time complexity of
several sorting algorithms.

[1]: https://www.youtube.com/watch?v=s7_Od9CmTu0
