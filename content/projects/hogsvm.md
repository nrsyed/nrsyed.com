---
title: SVM vehicle detector
description: HOG-based linear SVM for vehicle detection
link: 'https://github.com/nrsyed/svm-vehicle-detector'
author: Najam Syed
screenshot: 'hogsvm.gif'
layout: 'portfolio'
date: 2018-05-09
---

This is an end-to-end pipeline that uses scikit-learn to train a linear SVM
(support vector machine) on HOG (histogram of oriented gradients) features
extracted from images and perform inference on a video. The SVM was trained
on vehicles with the aim of detecting vehicles in a dashcam video.
