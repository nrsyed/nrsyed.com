---
title: A friendly introduction to rotation matrices
author: Najam Syed
type: post
date: 2017-11-29T03:37:20+00:00
url: /2017/11/28/a-friendly-introduction-to-rotation-matrices/
categories:
  - Kinematics/Dynamics
tags:
  - coordinate transformations
  - kinematics
katex: true
markup: "mmark"

---
Euclidean transformations are frequently utilized in dynamics, robotics, and
image processing, to name a few areas. In this post, we'll try to gain an
intuition for one type of Euclidean transformation: rotation, which is achieved
using rotation matrices. Specifically, we'll examine the simplest
case&#8212;the 2D rotation matrix.

{{< figure src=/img/rotation_1.png >}}

Suppose we're looking at the $$XY$$ plane (I'll use uppercase letters,
like $$X$$ and $$Y$$, to denote axes), and suppose there's a point on the
plane a distance $$a$$ from the origin that makes an angle $$\theta$$ with the $$X$$
axis&#8212;see the figure above. Trigonometry tells us that the $$x$$ and $$y$$
coordinates of this point (I'll use lowercase letters, like $$x$$ and $$y$$,
to denote coordinates along an axis) are given by $$x = a\cos{\theta}$$ and
$$y = a\sin{\theta}$$, respectively.

{{< figure src=/img/rotation_2.png >}}

Now, referring to the figure above, suppose we have a different point a distance
$$b$$ from the origin that makes the same angle $$\theta$$, as before, but this time
with the $$Y$$ axis. We can see that the $$x$$ and $$y$$ coordinates of this point are
given by $$x = -b\sin{\theta}$$ and $$y = b\cos{\theta}$$.

{{< figure src=/img/rotation_3.png >}}

In the figure above, left, we see the two points (and the lines extending toward
them from the origin) superimposed on one set of axes. Because they both lie at
an angle $$\theta$$ relative to the $$X$$ and $$Y$$ axes, respectively, the lines are
perpendicular to one another, just like a set of Cartesian axes. If we extend
each line in both directions, we can form a new set of axes, which we'll
draw in red and call $$X'$$ and $$Y'$$ (figure above, right). Notice how
this new set of primed axes, $$X'$$ and $$Y'$$, is the same as the $$X$$
and $$Y$$ axes (both sets of axes share an origin), but they're rotated
counterclockwise by angle $$\theta$$.

The purpose of coordinate rotations is, essentially, to express coordinates from
one coordinate system in a different coordinate system. When might this be
useful? Say, for example, you have a range sensor on a car that detects
obstacles near the car by reporting their location relative to the sensor, but
the sensor is mounted at an angle&#8212;in other words, the sensor's $$X$$
and $$Y$$ axes are at some angle relative to the car's $$X$$ and $$Y$$ axes. In
that case, we might utilize a coordinate transformation to put the sensor
feedback in terms of the vehicle coordinate system. Or, as another example, say
we have a robot arm with three joints, where each joint is rotated by a stepper
motor. We know the length of each segment and the angular displacement of each
motor, but not the overall orientation of the robot arm or the position of the
manipulator or gripper at the end of the arm. In this case, we might be working
with four coordinate systems&#8212;one for each joint, and a global coordinate
system (i.e., the one we're in, which physically describes the orientation
of the robot arm in space). In this example, we might use several sequential
coordinate rotations to determine the configuration of the robot arm, or to
determine how to move the manipulator/gripper to a specific location.

Along those lines, let's say we're looking at some point
that's defined in the $$X'Y'$$ coordinate system:

{{< figure src=/img/rotation_4.png >}}

In the $$X'Y'$$ coordinate system, the point has coordinates $$(x', y')$$
&#8212;see the figure above, right. Note how I've
indicated the $$x'$$ coordinate of the point with a white dot on the
$$X'$$ axis and the $$y'$$ coordinate of the point with a white dot on
the $$Y'$$ axis. However, let's say we're not interested in the
coordinates of this point in the $$X'Y'$$ coordinate system. Instead,
we'd like the coordinates of the point in terms of the $$XY$$ axes from
earlier:

{{< figure src=/img/rotation_5.png >}}

The figure above on the right is analogous to the first several figures where we
drew one point a distance $$a$$ from the origin and another point a distance $$b$$
from the origin. Here, $$a$$ corresponds to the $$x'$$ coordinate of the point
along the $$X'$$ axis, and $$b$$ corresponds to the $$y'$$ coordinate of
the point along the $$Y'$$ axis. Then, by analogy, we can say that the $$x$$
and $$y$$ coordinates of the $$x'$$ component of the point are given by:

<span style="text-align:left">
$$x = x'\cos{\theta}$$

$$y = x'\sin{\theta}$$
</span>

Similarly, the $$x$$ and $$y$$ coordinates of the $$y'$$ component are given by:

<span style="text-align:left">
$$x = -y'\sin{\theta}$$

$$y = y'\cos{\theta}$$
</span>

All we've done here is separate the point, which is defined in the
$$X'Y'$$ system, into its $$x'$$ and $$y'$$ components. Then,
we expressed the $$x'$$ component in terms of $$x$$ and $$y$$, and we expressed
the $$y'$$ component in terms of $$x$$ and $$y$$ (since our goal is to obtain
the $$x$$ and $$y$$ coordinates of the point). The overall coordinates of a point
are given by the sum of its components; if you're familiar with vectors,
this is akin to saying that the coordinates of a point can be found by adding
together its components. In this case, the coordinates of the point are found by
adding together its $$x'$$ and $$y'$$ components, i.e.,
$$x' + y' = (x'\cos{\theta}, x'\sin{\theta}) + (-y'\sin{\theta}, y'\cos{\theta})$$, or:

<span style="text-align:left">
$$x = x'\cos{\theta} - y'\sin{\theta}$$

$$y = x'\sin{\theta} + y'\cos{\theta}$$
</span>

These, finally, are the coordinates of the point in the $$XY$$ coordinate system.
How does all of this tie into rotation matrices? A rotation matrix is what
relates the $$(x', y')$$ coordinates to the $$(x, y)$$ coordinates.
It takes the expressions for $$x$$ and $$y$$ above and allows us to put them into
matrix form, like so:

$$
\left\{ \begin{matrix} x \\ y \end{matrix} \right\} =
\left[ \begin{matrix} cos\theta & -sin\theta \\
sin\theta & cos\theta \end{matrix} \right]
\left\{ \begin{matrix} x' \\ y' \end{matrix} \right\}
$$

Basically, the rotation matrix asks (and answers) the question, &#8220;What does
the $$x'$$ component contribute to $$x$$ and what does the $$y'$$
component contribute to $$x$$? What does the $$x'$$ component contribute to
$$y$$ and what does the $$y'$$ component contribute to $$y$$?&#8221; The end
result is the coordinates of the point in the $$XY$$ coordinate system:

{{< figure src=/img/rotation_6.png >}}

What if we want to go the other direction, i.e., convert the coordinates from a
point in the $$XY$$ coordinate system to the $$X'Y'$$ coordinate system?
This turns out to be the transpose of the matrix above. If it's not
apparent why this is the case, try applying the approach we employed in this
post to go the other way and see how it works out.

In the next post, we'll discuss Euclidean transformation matrices that
combine rotation and translation.
