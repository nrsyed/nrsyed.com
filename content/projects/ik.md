---
title: Simulated n-DOF robot arm
description: Inverse kinematics of a robot arm
link: '/2017/12/17/animating-the-jacobian-inverse-method-with-an-interactive-matplotlib-plot'
author: Najam Syed
screenshot: 'ik.gif'
layout: 'portfolio'
date: 2017-12-18
---

This is a Python program that defines a 2D robot arm with an arbitrary number
of revolute joints placed at arbitrary distances from one another and solves,
via the Jacobian inverse method, the inverse kinematics of the system that
enable the robot arm's end effector to reach a target position. An interactive
matplotlib plot is used to animate and demonstrate the result, with the arm
tracking a user-defined or moving target.
