#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Wed Oct  3 11:39:37 2018

@author: wanglab
"""

from __future__ import division
import os, numpy as np, sys, multiprocessing as mp, time
from scipy import ndimage
from skimage.external import tifffile
from tools.utils.io import load_dictionary, load_np
from scipy.ndimage.morphology import generate_binary_structure
import h5py
import subprocess as sp
from tools.conv_net.functions.bipartite import pairwise_distance_metrics

#%%
if __name__ == '__main__':
    
    #transfer from globus
    src = '/tigress/zmd/wang/zahra/3dunet_cnn/experiments/20181001_zd_train/forward'
    dest = '/jukebox/LightSheetTransfer/cnn/zmd'
    label = 'model_20181001'
    transfer(src, dest, label, other_endpoint = False)
        
    
#    test = ['20170116_tp_bl6_lob7_ml_08_647_010na_z7d5um_150msec_10povlp_ch00_C00_440-475_02', #for 20181001 net
#            'JGANNOTATION_20170116_tp_bl6_lob7_ml_08_647_010na_z7d5um_150msec_10povlp_ch00_C00_750-785_00', 
#            '20170116_tp_bl6_lob45_500r_12_647_010na_z7d5um_150msec_10povlp_ch00_C00_275-310_01', 
#            '20170116_tp_bl6_lob7_500r_09_647_010na_z7d5um_75msec_10povlp_ch00_z200-400_y4500-4850_x3450-3800', 
#            '20170115_tp_bl6_lob6a_1000r_647_010na_z7d5um_125msec_10povlp_ch00_03_500-550', 
#            '20170116_tp_bl6_lob7_ml_08_647_010na_z7d5um_150msec_10povlp_ch00_C00_440-475_00', 
#            '20170115_tp_bl6_lob6a_1000r_647_010na_z7d5um_125msec_10povlp_ch00_04_500-550', 
#            'JGANNOTATION_20170115_tp_bl6_lob6a_500r_01_647_010na_z7d5um_75_msec_10povlp_ch00_C00_425-460_00', 
#            '20170204_tp_bl6_cri_1000r_02_1hfds_647_0010na_25msec_z7d5um_10povlap_ch00_z200-400_y1350-1700_x3100-3450']

#%%    
    #after transfer, set relevant paths
    pth = '/jukebox/wang/zahra/conv_net/training/experiment_dirs/20181115_zd_train/forward'
    points_dict = load_dictionary('/jukebox/wang/pisano/conv_net/annotations/all_better_res/h129/filename_points_dictionary.p')
    
#******************************************************************************************************************************************    
    #initialise empty vectors
    tps = []; fps = []; fns = []    
    #iterates through forward pass output
    for dset in os.listdir(pth):
        impth = os.path.join(pth, dset)
        predicted = probabiltymap_to_centers_thresh(impth, threshold = (0.7, 1))
        
        print '\n   Finished finding centers for {}, calculating statistics\n'.format(dset)
        
        ground_truth = points_dict[dset[:-21]+'.npy'] #modifying file names so they match with original data
        
        paired,tp,fp,fn = pairwise_distance_metrics(ground_truth, predicted, cutoff = 30) #returns true positive = tp; false positive = fp; false negative = fn
       
        tps.append(tp); fps.append(fp); fns.append(fn) #append matrix to save all values to calculate f1 score
       
    tp = sum(tps); fp = sum(fps); fn = sum(fns) #sum all the elements in the lists
    precision = tp/(tp+fp); recall = tp/(tp+fn) #calculating precision and recal
    f1 = 2*( (precision*recall)/(precision+recall) ) #calculating f1 score
    
    print '\n   Finished calculating statistics for set params\n\nF1 score: {} \nTrue pos, false pos, false neg: {} \n'.format(f1, (tp,fp,fn))
    
#%%
def transfer(src, dest, label, other_endpoint = False):
    '''Tranfers diretories from tigress to local/jukebox locations.
    Inputs:
        src = tigress source path
        dest = destination path
        label = name of transfer
        other_endpoint = False; assumes transfer to LightSheetTransfer unless jukebox/other endpoint keys specified
    '''    
    #for globus transfer, endpoint keys: 
    #tigress = 'a9df83d2-42f0-11e6-80cf-22000b1701d1' #transferring from
    #wanglab = 'f7949748-c728-11e8-8c57-0a1d4c5c824a' #transferring to
    #jukebox = '6ce834d6-ff8a-11e6-bad1-22000b9a448b'    
    
    tigress_pth = 'a9df83d2-42f0-11e6-80cf-22000b1701d1:'+src
    if not other_endpoint:
        lst_pth = '6ce834d6-ff8a-11e6-bad1-22000b9a448b:'+dest
    else:
        lst_pth = other_endpoint+':'+dest
    
    sp.call(['globus', 'transfer', tigress_pth, lst_pth, '--recursive', '--label', label]) #run command line call
    
    
def probabiltymap_to_centers_thresh(src, threshold = (0.1,1), numZSlicesPerSplit = 200, overlapping_planes = 40, cores = 4, return_pixels = False, verbose = False, structure_rank_order = 2):
    '''
    by tpisano
    
    Function to take probabilty maps generated by run_cnn and output centers based on center_of_mass

    Inputs:
    --------------
    memmapped_paths: (optional, str, or list of strs) pth(s) to memmapped array
    threshold: (tuple) lower and upper bounds to keep. e.g.: (0.1, 1) - note this assumes input from a CNN and thus data will
    numZSlicesPerSplit: chunk of zplanes to process at once. Adjust this and cores based on memory constraints.
    cores: number of parallel jobs to do at once. Adjust this and numZSlicesPerSplit based on memory constraints
    overlapping_planes: number of planes on each side to overlap by, this should be comfortably larger than the maximum z distances of a single object
    structure_rank_order: Optional. If true provides the structure element to used in ndimage.measurements.labels, 2 seems to be the most specific
    save (optional) 'True', 'False', str of path and file name to save with extension .p. If multiple cell /jukebox/LightSheetTransfer/cnn/zmd/20180929_395000chkpnt_xy160z20/channels.
    return_pixels, if True return centers and all pixels associated with that center

    Returns single list of
    ------------
    centers: list of zyx coordinates of centers of mass
    (IF RETURN PIXELS = True, dictionary consisting of k=centers, v=indices determined by cnn with k's center)
    save_location (if saving)

    OUTPUTS ZYX

    '''
    #handle inputs
    if type(src) == str:
        if src[-2:] == 'h5':
            f = h5py.File(src)
            src = f['/main'].value
            f.close()
        if src[-3:] == 'tif': src = tifffile.imread(src)
        if src[-3:] == 'npy': src = load_np(src)

    src = np.squeeze(src)
    zdim, ydim, xdim = src.shape

    #run
    if cores > 1: 
        start = time.time()
        if verbose: sys.stdout.write('\n   Thesholding, determining connected pixels, identifying center of masses\n\n'); sys.stdout.flush()
        p = mp.Pool(cores)
        iterlst=[(src, z, numZSlicesPerSplit, overlapping_planes, threshold, return_pixels, structure_rank_order) for z in range(0, zdim, numZSlicesPerSplit)]
        centers = p.map(helper_labels_centerofmass_thresh, iterlst)
        p.terminate()
    else:
        start = time.time()
        if verbose: sys.stdout.write('\n   Thesholding, determining connected pixels, identifying center of masses\n\n'); sys.stdout.flush()
        iterlst=[(src, z, numZSlicesPerSplit, overlapping_planes, threshold, return_pixels, structure_rank_order) for z in range(0, zdim, numZSlicesPerSplit)]
        centers = []
        for i in iterlst: 
            centers.append(helper_labels_centerofmass_thresh(i))
        

    #unpack
    if not return_pixels: centers = [zz for xx in centers for zz in xx]
    if return_pixels:
        center_pixels_dct = {}; [center_pixels_dct.update(xx[1]) for xx in centers]
        centers = [zz for xx in centers for zz in xx[0]]
        

    if verbose: print ('Total time {} minutes'.format(round((time.time() - start) / 60)))
    if verbose: print('{} objects found.'.format(len(centers)))

    if return_pixels: return center_pixels_dct
    return centers


def helper_labels_centerofmass_thresh((array, start, numZSlicesPerSplit, overlapping_planes, threshold, return_pixels, structure_rank_order)):
    '''
    by tpisano
    
    '''
    zdim, ydim, xdim = array.shape

    structure = generate_binary_structure(array.ndim, structure_rank_order) if structure_rank_order else None

    #process
    if start == 0:
        arr = array[:numZSlicesPerSplit+overlapping_planes]
        #thresholding
        arr[arr<threshold[0]] = 0
        arr[arr>threshold[1]] = 0
        #find labels
        labels = ndimage.measurements.label(arr, structure); lbl_len = labels[1]
        centers = ndimage.measurements.center_of_mass(arr, labels[0], range(1, labels[1]+1)); 
        #return pixels associated with a center
        if return_pixels: dct = return_pixels_associated_w_center(centers, labels)
        del labels, arr
        assert lbl_len == len(centers), 'Something went wrong, center of mass missed labels'
        #filter such that you only keep centers in first half
        centers = [center for center in centers if (center[0] <= numZSlicesPerSplit)]
        if return_pixels: dct = {c:dct[c] for c in centers}

    else: #cover 3x
        arr = array[start - overlapping_planes : np.min(((start + numZSlicesPerSplit + overlapping_planes), zdim))]
        #thresholding
        arr[arr<threshold[0]] = 0
        arr[arr>threshold[1]] = 0
        #find labels
        labels = ndimage.measurements.label(arr)
        centers = ndimage.measurements.center_of_mass(arr, labels[0], range(1, labels[1]))
        #return pixels associated with a center
        if return_pixels: dct = return_pixels_associated_w_center(centers, labels)
        del labels, arr
        #filter such that you only keep centers within middle third
        centers = [center for center in centers if (center[0] > overlapping_planes) and (center[0] <= np.min(((numZSlicesPerSplit + overlapping_planes), zdim)))]
        if return_pixels: dct = {c:dct[c] for c in centers}
        
    #adjust z plane to accomodate chunking
    centers = [(xx[0]+start, xx[1], xx[2]) for xx in centers]
    if return_pixels: 
        dct = {tuple((kk[0]+start, kk[1], kk[2])):v for kk,v in dct.iteritems()}
        return centers, dct

    return centers


def return_pixels_associated_w_center(centers, labels, size = (15,100,100)):
    '''
    by tpisano
    
    Function to return dictionary of k=centers, v=pixels of a given label
    size is the search window from center - done to speed up computation
    ''' 
    dct = {}
    zz,yy,xx = size
    for cen in centers:
        z,y,x = [aa.astype('int') for aa in cen]
        dct[cen] = np.asarray(np.where(labels[0][z-zz:z+zz+1, y-yy:y+yy+1, x-xx:x+xx+1]==labels[0][z,y,x])).T    
    return dct

