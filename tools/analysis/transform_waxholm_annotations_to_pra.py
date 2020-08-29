#!/usr/bin/env python3

# -*- coding: utf-8 -*-

"""

Created on Mon Jul 27 17:37:30 2020



@author: wanglab

"""


import os
import sys
import time

sys.path.append("/home/emilyjanedennis/Desktop/GitHub/rat_BrainPipe")
import tifffile as tif
from tools.utils.io import makedir
from tools.registration.register import change_interpolation_order
from tools.registration.register import transformix_command_line_call
from tools.registration.transform_list_of_points import modify_transform_files
from scipy.ndimage.interpolation import zoom


# setting paths
src = "/home/emilyjanedennis/Desktop/for_registration_to_lightsheet/"
ann = "/home/emilyjanedennis/Desktop/for_registration_to_lightsheet/10grid.tif"
# ann = os.path.join(src, "WHS_SD_rat_atlas_v3_annotation.tif")
fx = "/home/emilyjanedennis/Desktop/for_registration_to_lightsheet/median_image.tif"

# need to make MRI annotation larger (~140% of atlas?) to transform to PRA
schwarz = tif.imread(ann)
pra = tif.imread(fx)
zf, yf, xf = (pra.shape[0]/schwarz.shape[0])*1.4, (
    pra.shape[1] /
    schwarz.shape[1])*1.4, (pra.shape[2]/schwarz.shape[2])*1.4
print("\nzooming...")
schwarz_for_pra = zoom(schwarz, (zf, yf, xf), order=1)

# saved out annotation volume
print("\nsaving zoomed volume...")
tif.imsave(os.path.join(src, "10grid_mouserat.tif"),
           schwarz_for_pra.astype("uint16"))

# where are the parameter files
reg = os.path.join(src, "mouserat")
a2r = [os.path.join(reg, xx) for xx in os.listdir(reg) if "Transform" in xx]
a2r.sort()

dst = "/home/emilyjanedennis/Desktop/for_registration_to_lightsheet/mouserat_grid_affine"
makedir(dst)


# transformix
transformfiles = modify_transform_files(transformfiles=a2r, dst=dst)
[change_interpolation_order(xx, 0) for xx in transformfiles]

# change the parameter in the transform files that outputs 16bit images instead
for fl in transformfiles:  # Read in the file
    with open(fl, "r") as file:
        filedata = file.read()
    # Replace the target string
    filedata = filedata.replace(
        '(ResultImagePixelType "float")', '(ResultImagePixelType "short")')
    # Write the file out again
    with open(fl, "w") as file:
        file.write(filedata)

# run transformix
transformix_command_line_call(os.path.join(
    src, "10grid_mouserat.tif"),
    dst, transformfiles[-1])

# where are the parameter files
reg = os.path.join(src, "mouserat_affine_only")
a2r = [os.path.join(reg, xx) for xx in os.listdir(reg) if "Transform" in xx]
a2r.sort()

dst = "/home/emilyjanedennis/Desktop/for_registration_to_lightsheet/mouserat_grid"
makedir(dst)

# transformix
transformfiles = modify_transform_files(transformfiles=a2r, dst=dst)
[change_interpolation_order(xx, 0) for xx in transformfiles]

# change the parameter in the transform files that outputs 16bit images instead
for fl in transformfiles:  # Read in the file
    with open(fl, "r") as file:
        filedata = file.read()
    # Replace the target string
    filedata = filedata.replace(
        '(ResultImagePixelType "float")', '(ResultImagePixelType "short")')
    # Write the file out again
    with open(fl, "w") as file:
        file.write(filedata)

# run transformix
transformix_command_line_call(os.path.join(
    src, "10grid_mouserat.tif"),
    dst, transformfiles[-1])
