---
title: Moments of inertia, products of inertia, and the inertia tensor
author: Najam Syed
type: post
date: 2018-02-07T01:34:39+00:00
url: /2018/02/06/moments-of-inertia-products-of-inertia-and-the-inertia-tensor/
categories:
  - Kinematics/Dynamics
tags:
  - inertia tensor
katex: true
markup: "mmark"

---
If you&#8217;ve studied dynamics or modeled anything involving rotational
motion, you&#8217;ve probably come across the concept of
[mass moment of inertia](https://en.wikipedia.org/wiki/Moment_of_inertia),
most likely in the form of the equation $$T = I \alpha$$, which relates the torque
$$T$$ acting on an object to its angular acceleration $$\alpha$$ via its moment
of inertia $$I$$. In this type of
problem, the torque and angular acceleration act about a single axis, and the
moment of inertia implicitly refers to the moment of inertia about that same
axis. The moment of inertia essentially describes an object&#8217;s resistance
to rotational motion in response to a torque. It is the rotational analog of
mass. However, this is just a simplified case of 3D rotational motion. If
you&#8217;ve dealt with 3D rotational motion, you&#8217;ve probably heard of the
inertia tensor, also known as the inertia matrix, which contains the moments of
inertia and products of inertia about all three axes for an object, however you
choose to orient those axes. In this post, we&#8217;ll see where the inertia
tensor, moments of inertia, and products of inertia come from, as well as
attempt to gain some intuition for what they mean.

This post assumes that you&#8217;re familiar with cross products, basic
calculus, and matrix multiplication.

# Derivation

We start with Newton&#8217;s Second Law, $$\mathbf{F} = m \mathbf{a}$$, which should
look familiar to you (we&#8217;ll use **bold** letters to denote vectors and
matrices). We can write Newton&#8217;s Second Law a different way if we remember
that acceleration is the time rate of change of velocity:

$$\mathbf{F} = m \frac{d}{dt} \mathbf{v} = \frac{d}{dt} m \mathbf{v}$$

You might recognize $$m \mathbf{v}$$ as the definition of [linear momentum][1]:
$$\mathbf{p} = m \mathbf{v}$$. In other words, the total force acting on a particle is
equal to the time derivative of its linear momentum:

$$\mathbf{F} = \mathbf{\dot{p}}$$

where $$\mathbf{p}$$ is linear momentum. This is for a single particle; we can
extend this to any system of multiple particles or rigid bodies by summing the
time derivative of the linear momentum of each particle in the system:

$$\mathbf{F} = \sum\limits_{i}^{N} \frac{d}{dt} m_i \mathbf{v_i} =
\sum\limits_{i}^{N} \mathbf{\dot{p}_i}$$

where there are N particles, $$m_i$$ is the mass of the $$i^\text{th}$$ particle,
$$\mathbf{v_i}$$ is the velocity of the $$i^\text{th}$$ particle, and $$\mathbf{\dot{p}_i}$$ is
the time derivative of the linear momentum of the $$i^\text{th}$$ particle. How does this
relate to rotational motion? If you&#8217;ve taken a dynamics course, you might
remember that torque is equal to distance times force. Or, in 3D, torque is
equal to the cross product of position and force:

$$\mathbf{T} = \mathbf{r} \times \mathbf{F} = \sum\limits_{i}^{N} \mathbf{r_i} \times
\mathbf{\dot{p}_i} = \sum\limits_{i}^{N} \mathbf{r_i} \times \frac{d}{dt} m_i
\mathbf{v_i}$$

In fact, it turns out that the right-hand side of the equation above is the
definition of the time derivative of the angular momentum $$\mathbf{L}$$:

$$\mathbf{\dot{L}} = \sum\limits_{i}^{N} \mathbf{r_i} \times \frac{d}{dt} m_i
\mathbf{v_i}$$

Or, written more succinctly:

$$\mathbf{T} = \mathbf{\dot{L}}$$ <span id="equation1" style="float:right;">**(Equation 1)**</span>

OK, so that&#8217;s the time derivative of angular momentum. However,
let&#8217;s take a step back and consider just the angular momentum, not its
time derivative:

$$\mathbf{L} = \sum\limits_{i}^{N} \mathbf{r_i} \times m_i \mathbf{v_i}$$

Since the objective here is to characterize rotational motion, let&#8217;s
rewrite the linear velocity in terms of angular velocity, which you might
remember from dynamics as the cross product of position and angular velocity:
$$\mathbf{v} = \mathbf{\omega} \times \mathbf{r}$$:

$$\mathbf{L} = \sum\limits_{i}^{N} m_i \mathbf{r_i} \times (\mathbf{\omega} \times
\mathbf{r_i})$$ <span id="equation2" style="float:right;">**(Equation 2)**</span>

Note that I&#8217;ve moved $$m_i$$ to the beginning of the sum, since
it&#8217;s a scalar and cross product multiplication is distributive (i.e., it
doesn&#8217;t matter where we put $$m_i$$). Also note how $$\mathbf{\omega}$$ is
not notated with a subscript, i.e., we didn&#8217;t write $$\mathbf{\omega_i}$$.
That&#8217;s because we&#8217;re assuming the entire system, and every particle
in it, has the same angular velocity.

The next step is to compute the cross products. To do this, we must remember
that these are vectors. We&#8217;ll consider the position vector of each
particle in the system to be defined by its x, y, and z components in Cartesian
coordinates: $$\mathbf{r_i} = x \pmb{\hat{\imath}} + y \pmb{\hat{\jmath}} + z
\mathbf{\hat{k}}$$. Similarly, the angular velocity also has $$x$$, $$y$$, and $$z$$
components: $$\pmb{\omega} = \omega_x \pmb{\hat{\imath}} + \omega_y
\pmb{\hat{\jmath}} + \omega_z \mathbf{\hat{k}}$$. Then, writing the
[determinant form](https://en.wikipedia.org/wiki/Cross_product#Matrix_notation)
of the cross product, we have:

$$(\pmb{\omega} \times \mathbf{r_i}) =
\begin{vmatrix} \pmb{\hat{\imath}} & \pmb{\hat{\jmath}} & \mathbf{\hat{k}} \\
\omega_x & \omega_y & \omega_z \\
x & y & z \end{vmatrix}$$

If we do the math, this cross product turns out to be:

$$(\pmb{\omega} \times \mathbf{r_i}) =
\begin{bmatrix} \omega_y z - \omega_z y \\
&#8211; \omega_x z + \omega_z x \\
\omega_x y - \omega_y x \end{bmatrix}$$

Approaching the cross product of this with position the same way, we find:

$$\mathbf{r_i} \times (\pmb{\omega} \times \mathbf{r_i}) =
\begin{vmatrix} \pmb{\hat{\imath}} & \pmb{\hat{\jmath}} & \mathbf{\hat{k}} \\
x & y & z \\
\omega_y z &#8211; \omega_z y & &#8211; \omega_x z + \omega_z x & \omega_x
y &#8211; \omega_y x
\end{vmatrix}$$

Performing the multiplication and grouping like terms:

$$\mathbf{r_i} \times (\pmb{\omega} \times \mathbf{r_i}) = \begin{bmatrix}
\omega_x (y^2 + z^2) - \omega_y xy - \omega_z xz \\ -
\omega_x xy + \omega_y (x^2 + z^2) - \omega_z yz \\ - \omega_x
xz - \omega_y yz + \omega_z (x^2 + y^2) \end{bmatrix}$$
<span id="equation3a" style="float:right;">**(Equation 3a)**</span>

If you have experience with linear algebra, you might see that the previous
equation, Equation 3a, lends itself nicely to being written as a matrix and a
vector, where the vector is simply the angular velocity vector mentioned in the
last paragraph:

$$\mathbf{r_i} \times (\pmb{\omega} \times \mathbf{r_i}) =
\begin{bmatrix}(y^2 + z^2) & -xy & -xz \\
-xy & (x^2 + z^2) & -yz \\
-xz & -yz & (x^2 + y^2) \end{bmatrix}
\begin{bmatrix} \omega_x \\ \omega_y \\ \omega_z \end{bmatrix}$$
<span id="equation3b" style="float:right;">**(Equation 3b)**</span>

Having computed the cross products, let&#8217;s put [Equation 3b][2] back into
[Equation 2][3]:

$$\mathbf{L} =
\sum\limits_{i}^{N} m_i \mathbf{r_i} \times (\pmb{\omega} \times \mathbf{r_i})
= \sum\limits_{i}^{N} m_i
\begin{bmatrix}(y^2 + z^2) & -xy & -xz \\
-xy & (x^2 + z^2) & -yz \\
-xz & -yz & (x^2 + y^2) \end{bmatrix}
\begin{bmatrix} \omega_x \\ \omega_y \\ \omega_z \end{bmatrix}$$
<span id="equation4" style="float:right;">**(Equation 4)**</span>

In Equation 4 above, summing a matrix is the same as summing each element of the
matrix. The same is true of the scalar $$m_i$$, which is multiplied with each
element of the matrix:

$$\mathbf{L} = \sum\limits_{i}^{N} m_i \mathbf{r_i} \times (\pmb{\omega} \times \mathbf{r_i})
= \begin{bmatrix}\sum\limits_{i}^{N}(y^2 + z^2)m_i &
\sum\limits_{i}^{N}(-xy)m_i & \sum\limits_{i}^{N}(-xz)m_i \\
\sum\limits_{i}^{N}(-xy)m_i & \sum\limits_{i}^{N}(x^2 + z^2)m_i &
\sum\limits_{i}^{N}(-yz)m_i \\
\sum\limits_{i}^{N}(-xz)m_i & \sum\limits_{i}^{N}(-yz)m_i &
\sum\limits_{i}^{N}(x^2 + y^2)m_i \end{bmatrix}
\begin{bmatrix} \omega_x \\ \omega_y \\ \omega_z \end{bmatrix}$$

At this point, it&#8217;s important to note that a &#8220;system of
particles&#8221; doesn&#8217;t necessarily mean a bunch of separate particles or
separate objects. Generally speaking, any rigid body or object can be thought of
as a system of particles, if we think of it as being comprised of $$N$$ smaller
connected pieces (or &#8220;particles&#8221;). Those of you who know your
calculus probably see where I&#8217;m going with this. If we think of a rigid
body as being made up of an infinite number of infinitely small pieces, i.e.,
$$N\to\infty$$, with each piece having a differential mass $$dm$$, the sums in
the equation above simply become integrals:

$$\mathbf{L} = \begin{bmatrix}\int\limits_{m}(y^2 + z^2)dm &
\int\limits_{m}(-xy)dm & \int\limits_{m}(-xz)dm \\ \int\limits_{m}(-xy)dm
& \int\limits_{m}(x^2 + z^2)dm & \int\limits_{m}(-yz)dm \\
\int\limits_{m}(-xz)dm & \int\limits_{m}(-yz)dm & \int\limits_{m}(x^2 + y^2)dm
\end{bmatrix}
\begin{bmatrix} \omega_x \\ \omega_y \\ \omega_z \end{bmatrix}$$
<span id="equation5" style="float:right;">**(Equation 5)**</span>

This matrix is the inertia tensor, a.k.a., the inertia matrix. The diagonal
elements of the matrix are termed the &#8220;moments of inertia.&#8221; For
convenience, the moments of inertia are abbreviated as follows:

$$I_{xx} = \int\limits_{m}(y^2 + z^2)dm$$


$$I_{yy} = \int\limits_{m}(x^2 + z^2)dm$$


$$I_{zz} = \int\limits_{m}(x^2 + y^2)dm$$

The off-diagonal elements of the matrix are termed the &#8220;products of
inertia.&#8221; Although there are six off-diagonal elements, there are only
three distinct products of inertia. This is because the matrix is symmetric,
i.e., $$I_{ij} = I_{ji}$$. These products of inertia are abbreviated as
follows:

$$I_{xy} = I_{yx} = -\int\limits_{m}(xy)dm$$


$$I_{xz} = I_{zx} = -\int\limits_{m}(xz)dm$$


$$I_{yz} = I_{zy} = -\int\limits_{m}(yz)dm$$

Rewriting the inertia tensor (inertia matrix) $$\mathbf{I}$$ using these
abbreviated definitions:

$$\mathbf{I} = \begin{bmatrix}I_{xx} & I_{xy} & I_{xz} \\
I_{yx} & I_{yy} & I_{yz} \\
I_{zx} & I_{zy} & I_{zz} \end{bmatrix}$$
<span id="equation6" style="float:right;">**(Equation 6)**</span>

Now, rewriting [Equation 2][3], the equation for angular momentum, with the
definition from Equation 6 above:

$$\mathbf{L} = \mathbf{I}\pmb{\omega} =
\begin{bmatrix}I_{xx} & I_{xy} & I_{xz} \\
I_{yx} & I_{yy} & I_{yz} \\
I_{zx} & I_{zy} & I_{zz} \end{bmatrix}
\begin{bmatrix} \omega_x \\ \omega_y \\ \omega_z \end{bmatrix}$$
<span id="equation7" style="float:right;">**(Equation 7)**</span>

Finally, substituting Equation 7 above back into [Equation 1][4], we come full
circle:

$$\mathbf{T} = \mathbf{\dot{L}} = \frac{d}{dt}\mathbf{I} \pmb{\omega}$$


$$\mathbf{T} = \mathbf{I} \pmb{\dot{\omega}} = \mathbf{I} \pmb{\alpha}$$
<span id="equation8" style="float:right;">**(Equation 8)**</span>

Hopefully, Equation 8 seems familiar, if you&#8217;ve studied dynamics. It is
the rotational analog of $$\mathbf{F} = m \mathbf{a}$$, derived using the definition
of torque, with the inertia tensor (and the moments of inertia and products of
inertia therein) being obtained along the way.

# What is the physical significance of the moments of inertia and products of inertia?

The math is all well and good, but what does it actually mean? Let&#8217;s
expand [Equation 8][5]:

$$\mathbf{T} = \mathbf{I} \pmb{\alpha}$$


$$\begin{bmatrix} T_x \\ T_y \\ T_z \end{bmatrix} =
\begin{bmatrix}I_{xx} & I_{xy} & I_{xz} \\
I_{yx} & I_{yy} & I_{yz} \\
I_{zx} & I_{zy} & I_{zz}\end{bmatrix}
\begin{bmatrix} \alpha_x \\ \alpha_y \\ \alpha_z \end{bmatrix}$$

where $$\pmb{\alpha} = \alpha_x \pmb{\hat{\imath}} + \alpha_y
\pmb{\hat{\jmath}} + \alpha_z \mathbf{\hat{k}}$$ is the angular acceleration. Note
how we&#8217;ve also split the torque into its respective components. As an
example, consider the result of multiplying the first row of the inertia matrix
with the angular acceleration vector:

$$T_x = I_{xx} \alpha_x + I_{xy} \alpha_y + I_{xz} \alpha_z$$

Essentially, the moments of inertia tell us how an object rotates about an axis
when a torque is applied about that same axis, e.g., if you apply torque about
the x axis, $$I_{xx}$$ tells us how that affects the angular acceleration about
the x axis, based on the mass distribution of the object. The products of
inertia tell us how an object rotates about an axis when a torque is applied
about a _different axis_. In the example above, the product of inertia
$$I_{xy}$$ tells us how a torque about the x axis affects angular acceleration
about the y axis, based on the mass distribution of the object. Similarly,
$$I_{xz}$$ tells us how a torque about the x axis affects angular acceleration
about the z axis.

With this in mind, it becomes easier to interpret the notation for a moment or
product of inertia. A moment of inertia or product of inertia $$I_{ij}$$ (where
$$i$$ can be x, y, or z, and $$j$$ can be x, y, or z) tells us how a torque
applied to axis $$i$$ affects the angular acceleration about axis $$j$$.

Because moments of inertia and products of inertia depend entirely on the mass
distribution of an object relative to the axis of rotation, they can change if
either a) the mass distribution changes or b) the object is rotated about a
different set of xyz axes. In fact, for any object, it&#8217;s possible to find
a set of axes for which the mass distribution is symmetric about every axis.
These are called the &#8220;principal axes,&#8221; and when you compute the
elements of the inertia tensor using the principal axes, the products of inertia
all come out to zero:

$$\mathbf{I} = \begin{bmatrix}I_{xx} & 0 & 0 \\
0 & I_{yy} & 0 \\
0 & 0 & I_{zz}\end{bmatrix}$$ <span style="float:right;">**(principal axes)**</span>

Generally speaking, this is the case for most problems&#8212;you&#8217;ll
usually be dealing with rotation about axes that pass through the center of mass
and about which the object is symmetric. However, when deviating from such
cases, a working knowledge of the inertia tensor can be invaluable.

[1]: https://en.wikipedia.org/wiki/Momentum
[2]: #equation3b
[3]: #equation2
[4]: #equation1
[5]: #equation8
