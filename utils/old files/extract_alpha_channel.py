from __future__ import print_function
import os, sys
from PIL import Image

image_path = "alphatesting.tga"
mask_path = "alphatesting_alpha.png"

# Open the image and convert it to RGBA, just in case it was indexed
image = Image.open(image_path).convert('RGBA')

# Extract just the alpha channel
alpha = image.split()[-1]

# Unfortunately the alpha channel is still treated as such and can't be dumped
# as-is

# Create a new image with an opaque black background
bg = Image.new("RGBA", image.size, (0,0,0,255))

# Copy the alpha channel to the new image using itself as the mask
bg.paste(alpha, mask=alpha)

# Since the bg image started as RGBA, we can save some space by converting it
# to grayscale ('L') Optionally, we can convert the image to be indexed which
# saves some more space ('P') In my experience, converting directly to 'P'
# produces both the Gray channel and an Alpha channel when viewed in GIMP,
# althogh the file sizes is about the same
bg.convert('L').convert('P', palette=Image.ADAPTIVE, colors=8).save(
                                                                mask_path,
                                                                optimize=True)