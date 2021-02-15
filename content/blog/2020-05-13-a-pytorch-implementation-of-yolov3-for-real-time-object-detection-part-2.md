---
title: A PyTorch implementation of YOLOv3 for real-time object detection (part 2)
author: Najam Syed
type: post
date: 2020-05-14T02:21:41+00:00
url: /2020/05/13/a-pytorch-implementation-of-yolov3-for-real-time-object-detection-part-2/
categories:
  - Algorithms
  - Computer Vision
  - Deep Learning
  - Machine Learning
tags:
  - neural networks
  - object detection
  - Python
  - yolo

---
**Link to code**:
[https://github.com/nrsyed/pytorch-yolov3](https://github.com/nrsyed/pytorch-yolov3)

- [Part 1 (Background)][1]
- Part 2 (Initializing the network)
- [Part 3 (Inference)][2]
- [Part 4 (Real-time multithreaded detection)][3]
- [Part 5 (Command-line interface)][4]

The last post went over some of the theory behind YOLOv3. In this post,
we&#8217;ll dig into the code (see the link at the top of this post). The repo
is set up as a Python package named `yolov3`, which can be called from the
terminal with a command of the same name (`yolov3`). Usage details and examples
can be found in the repo README, and we&#8217;ll touch on that a bit later, but
I&#8217;m going to start by focusing on the core of the code. The first thing
that happens is instantiating the `Darknet` class, initializing it with the
appropriate network configuration file, and loading the weights. An example of
this is found in
[_\_main__.py](https://github.com/nrsyed/pytorch-yolov3/blob/master/yolov3/__main__.py):

{{< highlight python >}}
net = yolov3.Darknet(args["config"], device=device)
net.load_weights(args["weights"])
{{< / highlight >}}

# Defining the network

Most of the magic happens in
[darknet.py](https://github.com/nrsyed/pytorch-yolov3/blob/master/yolov3/darknet.py),
where the `Darknet` class and its supporting functions reside.
The Darknet class&#8217;s
[_\_init__() method](https://github.com/nrsyed/pytorch-yolov3/blob/ed929c26e6d68777f89acae6feedda721cf80e00/yolov3/darknet.py#L319) takes two parameters&#8212;the path to the Darknet model
config file and optionally the device on which to run the model (e.g.,
&#8220;cpu&#8221;, &#8220;cuda&#8221;, &#8220;cuda:0&#8221;,
[torch.device()](https://pytorch.org/docs/stable/tensor_attributes.html#torch.torch.device)). Here are the first several lines of Darknet._\_init__():

{{< highlight python "linenos=true" >}}
class Darknet(torch.nn.Module):
    def __init__(self, config_fpath, device="cpu"):
        """
        Args:
            config_path (str): Path to Darknet .cfg file.
            device (str): Where to allocate tensors (e.g., "cpu", "cuda", etc.)
        """
        super().__init__()
        self.blocks, self.net_info = parse_config(config_fpath)
        self.modules_ = blocks2modules(
            self.blocks, self.net_info, device=device
        )
        self.device = device
{{< / highlight >}}

Note that it subclasses
[torch.nn.Module](https://pytorch.org/docs/stable/nn.html#torch.nn.Module), which gives it the methods and properties of a PyTorch
module necessary for the model to work, and calls the _\_init__() method of this
superclass. Next, we call
[parse_config(), a custom function also defined in darknet.py](https://github.com/nrsyed/pytorch-yolov3/blob/ed929c26e6d68777f89acae6feedda721cf80e00/yolov3/darknet.py#L125).

{{< highlight python >}}
def parse_config(fpath):
    """
    Parse Darknet config file and return a list of network blocks and
    pertinent information for each block.

    Args:
        fpath (str): Path to Darknet .cfg file.
    Returns:
        blocks (List[dict]): List of blocks (as dicts). Each block from the
            .cfg file is represented as a dict, e.g.:
            {
                'type': 'convolutional', 'batch_normalize': 1, 'filters': 32,
                'size': 3, 'stride': 1, 'pad': 1, 'activation': 'leaky'
            }
        net_info (dict): Dict of info from '[net]' block of .cfg file.
    """
{{< / highlight >}}

It takes a path to a Darknet config file, which contains information on the
network architecture and parameters. The config file defines the network using
blocks such as this one, taken from the yolov3 config file
[yolov3.cfg](https://github.com/nrsyed/pytorch-yolov3/blob/master/models/yolov3.cfg):

{{< highlight plain >}}
[convolutional]
batch_normalize=1
filters=32
size=3
stride=1
pad=1
activation=leaky
{{< / highlight >}}

The first line of each block (each layer) contains the block type (e.g.,
&#8220;convolutional&#8221;) in square brackets. Each subsequent line contains
the parameters for the block. The parse_config() helper function reads the
config file and returns a list of dicts (one for each block, i.e., one for each
layer in the table from the last post) containing the relevant info needed to
construct that block as a PyTorch module. The dict for the convolutional layer
above would look like this:

{{< highlight python >}}
{'activation': 'leaky',
 'batch_normalize': 1,
 'filters': 32,
 'pad': 1,
 'size': 3,
 'stride': 1,
 'type': 'convolutional'}
{{< / highlight >}}

The other block types are &#8220;shortcut,&#8221; &#8220;route,&#8221;
&#8220;upsample,&#8221; &#8220;maxpool,&#8221; and &#8220;yolo.&#8221; Note that
the full YOLOv3 model doesn&#8217;t contain any maxpool layers, but yolov3-tiny
and yolov3-spp do. A shortcut block looks like this in the config file:

{{< highlight plain >}}
[shortcut]
from=-3
activation=linear
{{< / highlight >}}

The `from` value of -3 indicates that the output of layer n-1 (the layer before
the shortcut layer) and the output of layer n-3 should be summed. The dict for
this layer would look like as follows:

{{< highlight python >}}
{'activation': 'linear',
 'from': -3,
 'type': 'shortcut'}
{{< / highlight >}}

A route block contains a `layers` field consisting of at least one integer. A
few examples are shown below.

{{< highlight plain >}}
[route]
layers = -4

[route]
layers = -1, 61

[route]
layers=-1,-3,-5,-6
{{< / highlight >}}

A route layer concatenates the outputs of the specified layers. The first
example would simply bring the output of layer n-4 to the current layer
unchanged. The latter example would concatenate the outputs of layer n-1 and
layer 61. parse_config() turns the layer indices in the `layers` field into a
list for easy consumption by subsequent functions. The `layers` field of the
route blocks in the original yolov3 model contain at most two values, but
there&#8217;s at least one block in yolov3-spp that contains four.

The full YOLOv3 model has three yolo blocks, of which an example is shown below.

{{< highlight plain >}}
[yolo]
mask = 6,7,8
anchors = 10,13,  16,30,  33,23,  30,61,  62,45,  59,119,  116,90,  156,198,  373,326
classes=80
num=9
jitter=.3
ignore_thresh = .7
truth_thresh = 1
random=1
{{< / highlight >}}

The only things we really care about here are `anchors`, which consists of
width/height pairs of anchor box sizes, and the 0-indexed `mask`, which tells us
which anchor boxes this yolo layer will make predictions for (in this case,
`116,90`, `156,198`, and `373,326`). `classes` indicates the number of classes
on which the model was trained and `num` simply indicates the number of anchors,
but we don&#8217;t really need these pieces of information&#8212;the number of
classes can be introspected later from the shape of the input tensor and the
number of anchors can be determined from the `anchors` field. The rest of the
parameters are for training and irrelevant to inference. Descriptions of all
block parameters can be found on
[Alexey Bochkovskiy’s Darknet fork](https://github.com/AlexeyAB/darknet/wiki/CFG-Parameters-in-the-different-layers). parse_config() turns the `anchors`
field values into a list of lists and the `mask` indices into a list for
convenience:

{{< highlight python >}}
{'anchors': [[10, 13],
             [16, 30],
             [33, 23],
             [30, 61],
             [62, 45],
             [59, 119],
             [116, 90],
             [156, 198],
             [373, 326]],
 'classes': 80,
 'ignore_thresh': 0.7,
 'jitter': 0.3,
 'mask': [6, 7, 8],
 'num': 9,
 'random': 1,
 'truth_thresh': 1,
 'type': 'yolo'}
{{< / highlight >}}

There&#8217;s also a special &#8220;net&#8221; block at the beginning of the
config file:

<span id="net-block" />
{{< highlight plain >}}
[net]
# Testing
# batch=1
# subdivisions=1
# Training
batch=64
subdivisions=16
width=608
height=608

...
{{< / highlight >}}

All of its fields except `width` and `height` are irrelevant for inference,
since the anchor box dimensions are relative to this width and height.
parse_config() returns this &#8220;net info&#8221; separate from the list of
blocks, as the function&#8217;s docstring indicates:

Let&#8217;s return to Darknet._\_init__(), which takes the return values from
parse_config(), stores them as instance variables, and plugs them into another
helper function named blocks2modules():

{{< highlight python "linenos=true,linenostart=9" >}}
        self.blocks, self.net_info = parse_config(config_fpath)
        self.modules_ = blocks2modules(
            self.blocks, self.net_info, device=device
        )
        self.device = device
{{< / highlight >}}

Note that I&#8217;ve named the instance variable that captures the return value
`self.modules_` (with an underscore at the end) to avoid conflict with the
instance attribute `self.modules`, which is a method inherited from
torch.nn.Module that returns a generator of PyTorch modules contained in the
instance. blocks2modules() translates the list of blocks into a list of PyTorch
modules. Each module (layer) is implemented as a
[torch.nn.Sequential](https://pytorch.org/docs/stable/nn.html#torch.nn.Sequential)
container, as a given module can consist of multiple
sub-modules (e.g., a convolutional block consists of a 2D convolutional layer, a
batch normalization layer if specified by the config file, and an activation layer).

Route and shortcut blocks, which utilize the output from other layers, are
handled by adding a dummy layer to the module list. The actual logic for these
layers is handled in the Darknet.forward() method. This way, the structure of
the PyTorch module list (and the indices of modules within the list) continue to
match that of the block list, simplifying things. The dummy layer is literally
just an empty class, which is also defined in darknet.py:

{{< highlight python >}}
class DummyLayer(torch.nn.Module):
    def __init__(self):
        """
        Empty dummy layer to serve as placeholder for shortcut and route
        layers, which provide connections to previous layers. Actual logic
        is handled in Darknet.forward().
        """
        super().__init__()
{{< / highlight >}}

I&#8217;ve implemented maxpool blocks (which are present in yolov3-tiny and
yolov3-spp but not in yolov3) with a custom monkey-patched MaxPool2d class also
defined in darknet.py, which looks like this:

{{< highlight python >}}
class MaxPool2d(torch.nn.MaxPool2d):
    """
    Monkey-patched MaxPool2d class to replicate "same" padding; refer to
    https://github.com/eriklindernoren/PyTorch-YOLOv3/pull/48/files#diff-f219bfe69e6ed201e4bdfdb371dc0c9bR49
    """
    def forward(self, input_):
        if self.kernel_size > 1 and self.stride == 1:
            padding = self.kernel_size - 1
            zero_pad = torch.nn.ZeroPad2d((0, padding, 0, padding))
            input_ = zero_pad(input_)
        return F.max_pool2d(
            input_, self.kernel_size, self.stride, self.padding,
            self.dilation, self.ceil_mode, self.return_indices
        )
{{< / highlight >}}

As the docstring indicates, unlike the original Darknet max pooling
implementation, the PyTorch implementation of
[torch.nn.MaxPool2d](https://pytorch.org/docs/stable/nn.html#torch.nn.MaxPool2d) doesn&#8217;t allow for &#8220;same&#8221; padding
functionality (at least as of PyTorch 1.4). Same padding refers to padding the
input tensor such that the output has the same shape as the original input. The
monkey-patched class above, which subclasses torch.nn.MaxPool2d, zero pads the
right and bottom edges of the input via torch.nn.ZeroPad2d if certain conditions
are fulfilled before performing max pooling.

Lastly, there are yolo blocks, for which we use the custom YOLOLayer class also
defined in darknet.py. The YOLO classification layer of a network transforms the
output tensor into predicted bounding boxes. This is a somewhat involved
process, so we&#8217;ll come back to it later when examining Darknet.forward().
For now, let&#8217;s continue with the rest of Darknet._\_init__().

{{< highlight python "linenos=true,linenostart=10" >}}
        self.modules_ = blocks2modules(
            self.blocks, self.net_info, device=device
        )
        self.device = device

        # Determine the indices of the layers that will have to be cached
        # for route and shortcut connections.
        self.blocks_to_cache = set()
        for i, block in enumerate(self.blocks):
            if block["type"] == "route":
                # Replace negative values with absolute block index.
                for j, block_idx in enumerate(block["layers"]):
                    if block_idx < 0:
                        block["layers"][j] = i + block_idx
                        self.blocks_to_cache.add(i + block_idx)
                    else:
                        self.blocks_to_cache.add(block_idx)
            elif block["type"] == "shortcut":
                # "shortcut" layer concatenates the feature map from the
                # previous block with the feature map specified by the shortcut
                # block's "from" field (which is a negative integer/offset).
                self.blocks_to_cache.add(i - 1)
                self.blocks_to_cache.add(i + block["from"])
{{< / highlight >}}

Because shortcut and route layers involve outputs from previous layers, we need
to cache the outputs of those previous layers. The easy way to do this is to
simply cache the output of every layer in Darknet.forward(), but that seems
wasteful and unnecessary, so instead I've opted to determine which layers need
to be cached and only cache those. This is done by iterating through the blocks
and adding the indices of the layers specified by the route and shortcut blocks
to a set, as demonstrated in the code above.

# Loading the weights

Finally, let's return to the original two lines in \_\_main__.py at the beginning
of this post:

{{< highlight python >}}
net = yolov3.Darknet(args["config"], device=device)
net.load_weights(args["weights"])
{{< / highlight >}}

The second line of this snippet calls
[Darknet.load_weights()](https://github.com/nrsyed/pytorch-yolov3/blob/ed929c26e6d68777f89acae6feedda721cf80e00/yolov3/darknet.py#L407). To write this method, I largely drew upon
[Ayoosh Kathuria's own blog post on implementing YOLOv3 in PyTorch](https://blog.paperspace.com/how-to-implement-a-yolo-v3-object-detector-from-scratch-in-pytorch-part-3/#understandingtheweightsfile).

To start, the method loads the weights and stores the first several bytes, which
form the header for the weights file.

{{< highlight python >}}
    def load_weights(self, weights_path):
        """
        Args:
            weights_path (str): Path to Darknet .weights file.
        """
        with open(weights_path, "rb") as f:
            header = np.fromfile(f, dtype=np.int32, count=5)
            self.header = header
            weights = np.fromfile(f, dtype=np.float32)
{{< / highlight >}}

The header is irrelevant to inference, but information on the values it
comprises can be found
[here](https://github.com/AlexeyAB/darknet/issues/2914#issuecomment-496675346). The rest of the method iterates through the FP32 weight values using
the `blocks` structure derived above as a reference, since only convolutional
blocks have weights associated with them.

{{< highlight python >}}
            # Index (pointer) to position in weights array.
            p = 0

            for block, module in zip(self.blocks, self.modules_):
                # Only "convolutional" blocks have weights.
                if block["type"] == "convolutional":
                    conv = module[0]
{{< / highlight >}}

Referring back to the blocks2modules() function, we see that a convolutional
block consists of a convolutional layer, a batch normalization layer _if one was
specified in the config_, and finally an activation layer, in that
order&#8212;hence the line `conv = module[0]`, which grabs the first layer of
the block, i.e., the convolutional layer. The weights for a convolutional block
with a batch normalization layer are stored in the following order: batch norm
biases, batch norm weights, batch norm mean, batch norm variance, and finally
the convolutional layer weights (there are no convolutional biases). The weights
for a convolutional block without a batch normalization layer simply store the
convolutional layer biases followed by the convolutional layer weights. The rest
of the method utilizes this to correctly load the weights.

{{< highlight python >}}
                    if "batch_normalize" in block and block["batch_normalize"]:
                        # Convolutional blocks with batch norm have weights
                        # stored in the following order: bn biases, bn weights,
                        # bn running mean, bn running var, conv weights.

                        bn = module[1]
                        bn_len = bn.bias.numel()

                        bn_biases = torch.from_numpy(weights[p:p+bn_len])
                        bn.bias.data.copy_(bn_biases.view_as(bn.bias.data))
                        p += bn_len

                        bn_weights = torch.from_numpy(weights[p:p+bn_len])
                        bn.weight.data.copy_(
                            bn_weights.view_as(bn.weight.data)
                        )
                        p += bn_len

                        bn_running_mean = torch.from_numpy(weights[p:p+bn_len])
                        bn.running_mean.copy_(
                            bn_running_mean.view_as(bn.running_mean)
                        )
                        p += bn_len

                        bn_running_var = torch.from_numpy(weights[p:p+bn_len])
                        bn.running_var.copy_(
                            bn_running_var.view_as(bn.running_var)
                        )
                        p += bn_len

                    else:
                        # Convolutional blocks without batch norm store weights
                        # in the following order: conv biases, conv weights.
                        num_conv_biases = conv.bias.numel()
                        conv_biases = torch.from_numpy(
                            weights[p:p+num_conv_biases]
                        )
                        conv.bias.data.copy_(
                            conv_biases.view_as(conv.bias.data)
                        )
                        p += num_conv_biases

                    num_weights = conv.weight.numel()
                    conv_weights = torch.from_numpy(weights[p:p+num_weights])
                    conv.weight.data.copy_(
                        conv_weights.view_as(conv.weight.data)
                    )
                    p += num_weights
{{< / highlight >}}

We simply go block by block until all weights have been loaded.

# Summary

In this post, we've followed all the code responsible for constructing the
network from a Darknet config file and loading the model weights. The next post
will examine the code for inference and making predictions on images and video.

[1]: {{< ref "2020-04-28-a-pytorch-implementation-of-yolov3-for-real-time-object-detection-part-1.md" >}}
[2]: {{< ref "2020-06-30-a-pytorch-implementation-of-yolov3-for-real-time-object-detection-part-3.md" >}}
[3]: {{< ref "2020-09-11-a-pytorch-implementation-of-yolov3-for-real-time-object-detection-part-4.md" >}}
[4]: {{< ref "2020-09-20-a-pytorch-implementation-of-yolov3-for-real-time-object-detection-part-5.md" >}}
