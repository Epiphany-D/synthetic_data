import json
import os
import numpy as np
import cv2
import scipy.fftpack as fp
from scipy import stats
from matplotlib import pyplot as plt
import copy
import label_file
from numpy import inf
import random
import threading
import time


def radial_profile(data, center):
    y, x = np.indices((data.shape))
    r = np.sqrt((x - center[0])**2 + (y - center[1])**2)
    r = r.astype(np.int)

    # sum over pixels the same radius away from center
    tbin = np.bincount(r.ravel(), data.ravel())

    # normalize by distance to center, since as radius grows the # of pixels in radius bin does also
    nr = np.bincount(r.ravel())
    radialprofile = tbin / nr
    return radialprofile 


# x,y now define a center
def check_slice(template_im,slice_shape,x,y,padding):

    threshold = 50

    template_slice = template_im[y-padding:y+slice_shape[0]+padding,x-padding:x+slice_shape[1]+padding,:]

    # if all pixels are the same, then don't even have to run the rest of check
    if np.all(template_slice == template_slice[0,0,0]):
        return True

    grey_slice = cv2.cvtColor(template_slice, cv2.COLOR_BGR2GRAY)
    f = np.fft.fft2(grey_slice)
    fshift = np.fft.fftshift(f)
    magnitude_spectrum = 20*np.log(np.abs(fshift))

    # x,y format
    center = (int(slice_shape[1] / 2),int(slice_shape[0] / 2))

    # get description of fft emitting from center
    radial_prof = radial_profile(magnitude_spectrum, center)

    radial_prof[radial_prof == -inf] = 0


    idx = range(0,radial_prof.shape[0])
    bin_means = stats.binned_statistic(idx, radial_prof, 'mean', bins=4)[0]
    
    if bin_means[-1] < threshold and bin_means[-2] < threshold:
        return True
    else:
        return False


# get image and json filepaths
directory = "/storage/hpc/data/jltmh3/datasets/processed_hardcases5"
images = []
json_files = []
for filename in os.listdir(directory):
    if filename.endswith(".png") or filename.endswith(".jpg"): 
        images.append(os.path.join(directory, filename))
        continue
    elif filename.endswith(".json"): 
        json_files.append(os.path.join(directory, filename))
        continue

images.sort()
json_files.sort()

print(images)
print(json_files)

def subimage(image, center, theta, width, height):

    ''' 
    Rotates OpenCV image around center with angle theta (in deg)
    then crops the image according to width and height.
    '''

    shape = ( image.shape[1], image.shape[0] ) # cv2.warpAffine expects shape in (length, height)

    matrix = cv2.getRotationMatrix2D( center=center, angle=theta, scale=1 )
    image = cv2.warpAffine( src=image, M=matrix, dsize=shape[::-1])

    x = int( center[0] - width/2  )
    y = int( center[1] - height/2 )

    image = image[ y:y+height, x:x+width ]
    return image, matrix


# get relation and element json objects with relative bbox coords and relation image slices 
count = 0
relations = []
relation_slices = []
relation_indicators = []
extra_indicators = []
relation_elements = []
extra_elements = []
for current_imagepath, json_file in zip(images,json_files):

    # read image and json
    current_image = cv2.imread(current_imagepath)
    with open(json_file) as f:
        data = json.load(f)
    
    # print(data)

    if data['shapes'] is None:
        continue


    # get relationships
    tmp_indicators = []
    tmp_relations = []
    tmp_elements = []
    for json_obj in data["shapes"]:

        if json_obj is None:
            continue

        if "activate_relation" in json_obj['label'] or "inhibit_relation" in json_obj['label']:

            tmp_relations.append(json_obj)
        
        elif "activate" in json_obj['label'] or "inhibit" in json_obj['label']:

            # save indicator json
            tmp_indicators.append(json_obj)

        else:
            tmp_elements.append(json_obj)

        
    # get elements for each relation
    for relation in tmp_relations:

        tmp_str = relation['label'].split("|")
        source_elements = tmp_str[0].split(":")[-1]
        if "[" in source_elements:
            tmp_str2 = source_elements[1:-1]
            source_elements = tmp_str2.split(",")
        else:
            source_elements = [source_elements]

        target_elements = tmp_str[-1]
        if "[" in target_elements:
            tmp_str2 = target_elements[1:-1]
            target_elements = tmp_str2.split(",")
        else:
            target_elements = [target_elements]

        # get all relation's elements and elements inside of relationship slice
        rel_pts = np.clip(np.array(relation['points']),0,np.inf)
        el_min_x = int(min(rel_pts[:,0]))
        el_min_y = int(min(rel_pts[:,1]))
        el_max_x = int(max(rel_pts[:,0]))
        el_max_y = int(max(rel_pts[:,1]))
        elements_to_save = []
        extra_elements_to_save = []
        for element in tmp_elements:

            el_pts = np.array(element['points'])

            # save relation's elements
            compare_str = element['label'].split(":")[0]
            if compare_str in source_elements:
                elements_to_save.append(copy.deepcopy(element))
            elif compare_str in target_elements:
                elements_to_save.append(copy.deepcopy(element))
            
            # # if an element is not a part of the relation, but is inside the relation slice, then we still want to save it
            # elif np.all(el_pts[:,0] > min_x) and np.all(el_pts[:,1] > min_y) and np.all(el_pts[:,0] < max_x) and np.all(el_pts[:,1] < max_y):
            #     extra_elements_to_save.append(copy.deepcopy(element))

        # if not all elements found, then skip relation
        if len(elements_to_save) != len(source_elements) + len(target_elements):
            continue


        # get relation's indicator
        indicator_json = None
        for indicator in tmp_indicators:
            temp_str = indicator['label'].split("|")
            indicator_source_el = temp_str[0].split(":")[-1]
            if "[" in indicator_source_el:
                tmp_str2 = indicator_source_el[1:-1]
                indicator_source_el = tmp_str2.split(",")
            else:
                indicator_source_el = [indicator_source_el]


            indicator_target_el = temp_str[-1]
            if "[" in indicator_target_el:
                tmp_str2 = indicator_target_el[1:-1]
                indicator_target_el = tmp_str2.split(",")
            else:
                indicator_target_el = [indicator_target_el]

            if indicator_source_el == source_elements and indicator_target_el == target_elements:
                indicator_json = indicator
                break

        if indicator_json is None:
            continue

        ind_pts = np.clip(np.array(indicator_json['points']),0,np.inf)
        ind_min_x = int(min(ind_pts[:,0]))
        ind_min_y = int(min(ind_pts[:,1]))
        ind_max_x = int(max(ind_pts[:,0]))
        ind_max_y = int(max(ind_pts[:,1]))

        min_x = min([el_min_x,ind_min_x])
        min_y = min([el_min_y,ind_min_y])
        max_x = max([el_max_x,ind_max_x])
        max_y = max([el_max_y,ind_max_y])

        # # find additional indicators inside of relationship slice
        # extra_indicators_to_save = []
        # for indicator in tmp_indicators:
        #     ind_pts = np.array(element['points'])
        #     if indicator != indicator_json:
        #         if np.all(ind_pts[:,0] > min_x) and np.all(ind_pts[:,1] > min_y) and np.all(ind_pts[:,0] < max_x) and np.all(ind_pts[:,1] < max_y):
        #             extra_indicators_to_save.append(copy.deepcopy(indicator))

        # get relation slice
        tmp_slice = current_image[min_y:max_y,min_x:max_x,:]
        tmp_slice_shape = tmp_slice.shape
        # cv2.imshow('dst_rt', tmp_slice)
        # cv2.waitKey(0)
        

        # adjust bbox for being relative ot the relation's bbox coords
        mask = np.empty(current_image[min_y:max_y,min_x:max_x,:].shape)
        mask[:] = np.nan
        rel_pts = np.clip(np.array(relation['points']),0,np.inf)
        ind_pts = np.array(indicator_json['points'])
        min_x = min(rel_pts[:,0])
        min_y = min(rel_pts[:,1])

        rel_pts[:,0] -= min_x
        rel_pts[:,1] -= min_y

        ind_pts[:,0] -= min_x
        ind_pts[:,1] -= min_y
        ind_min_x = np.clip(int(min(ind_pts[:,0])),0,tmp_slice_shape[1])
        ind_min_y = np.clip(int(min(ind_pts[:,1])),0,tmp_slice_shape[0])
        ind_max_x = np.clip(int(max(ind_pts[:,0])),0,tmp_slice_shape[1])
        ind_max_y = np.clip(int(max(ind_pts[:,1])),0,tmp_slice_shape[0])
        mask[ind_min_y:ind_max_y,ind_min_x:ind_max_x,:] = 1



        # adjust relationship elements
        adjusted_els = []
        for element in elements_to_save:
            el_pts = np.array(element['points'])
            el_pts[:,0] -= min_x
            el_pts[:,1] -= min_y
            el_min_x = np.clip(int(min(el_pts[:,0])),0,tmp_slice_shape[1])
            el_min_y = np.clip(int(min(el_pts[:,1])),0,tmp_slice_shape[0])
            el_max_x = np.clip(int(max(el_pts[:,0])),0,tmp_slice_shape[1])
            el_max_y = np.clip(int(max(el_pts[:,1])),0,tmp_slice_shape[0])
            mask[el_min_y:el_max_y,el_min_x:el_max_x,:] = 1
            element['points'] = el_pts.tolist()
            adjusted_els.append(element)

        # keep pixels inside of target regions, set other pixels to white
        tmp_slice = (tmp_slice * mask)
        tmp_slice = np.nan_to_num(tmp_slice,nan=255)

        # tmp_slice = tmp_slice / 255
        # cv2.imshow('dst_rt', tmp_slice)
        # cv2.waitKey(0)

        relation_slices.append(tmp_slice)
        relation['points'] = rel_pts.tolist()
        indicator_json['points'] = ind_pts.tolist()

        relations.append(relation)
        relation_elements.append(adjusted_els)
        relation_indicators.append(indicator_json)


# print('ah')
# print(relations[0]['label'])
# print('elements')
# for ele in relation_elements[0]:
#     print(ele['label'])
# print('indicator')
# print(relation_indicators[0]['label'])



# TODO:: revisit process this process and placing in image
# remove backgrounds and artifacts from relation slices
# processed_slices = []
# masks = []
# for img in relation_slices:

#     # greyscale and filter threshold
#     gray_img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
#     # _, thresh = cv2.threshold(gray_img, 100, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
#     ret, thresh = cv2.threshold(gray_img, 120, 255, cv2.THRESH_BINARY_INV)

#     # detect contours based on thresholded pixels
#     contours, hierarchy = cv2.findContours(thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

#     # draw contours on base zero mask
#     mask = np.zeros(img.shape[:2], np.uint8)
#     cv2.drawContours(mask, contours,-1, 255, -1)

#     # get mask to whiten parts that are not detected contours
#     mask = np.repeat(mask[:, :, np.newaxis], 3, axis=2)
#     invert_mask = np.invert(mask)
#     new_img = cv2.bitwise_or(img, invert_mask)

#     masks.append(mask)
#     processed_slices.append(new_img)

#     cv2.imshow('dst_rt',mask)
#     cv2.waitKey(0)


processed_slices = relation_slices

print(str(len(processed_slices)))


class template_thread(threading.Thread):
    def __init__(self, threadID,name,template_list,directory):
        threading.Thread.__init__(self)
        self.threadID = threadID
        self.name = name
        self.template_list = template_list
        self.directory = directory

    def run(self):

        filename = self.template_list[self.threadID]
        
        # how many images per template
        stop_child_flag = False
        # num_copies = 372
        num_copies = 93
        for copy_idx in range(num_copies):

            copy_idx *= 4
            copy_idx = self.threadID*num_copies + copy_idx

            if stop_child_flag:
                break

            # thread0 = template_thread(template_idx+0,"thread-0",template_list,directory)
            child_thread0 = copy_thread(copy_idx,"child0",self.directory,filename)
            child_thread1 = copy_thread(copy_idx+1,"child1",self.directory,filename)
            child_thread2 = copy_thread(copy_idx+2,"child2",self.directory,filename)
            child_thread3 = copy_thread(copy_idx+3,"child3",self.directory,filename)


            child_thread0.start()
            if template_idx + 1 > len(template_list):
                stop_child_flag = True
                continue
            else:
                child_thread1.start()
            if template_idx + 2 > len(template_list):
                stop_child_flag = True
                continue
            else:
                child_thread2.start()
            if template_idx + 3 > len(template_list):
                stop_child_flag = True
                continue
            else:
                child_thread3.start()

            child_thread0.join()
            child_thread1.join()
            child_thread2.join()
            child_thread3.join()
                    
            


class copy_thread(threading.Thread):
    def __init__(self,copyID,name,directory,filename):
        threading.Thread.__init__(self)
        self.copyID = copyID
        self.name = name
        self.directory = directory
        self.filename = filename

    def run(self):

        # loop through templates
        # read template and get query coords
        template_im = cv2.imread(os.path.join(self.directory, self.filename))
        
        # TODO this doesn't have to be repeated
        tmp_template_im = np.reshape(template_im,(-1,3))
        template_mode_pix = stats.mode(tmp_template_im)[0]


        # put relations on template and generate annotation
        element_indx = 0
        shapes = []
        # for relation_idx in range(30):
        for relation_idx in range(30):
            slice_idx = random.randint(0,len(processed_slices)-1)

            current_slice = processed_slices[slice_idx]

            # current_mask = masks[slice_idx]
            relation = relations[slice_idx]
            els_json = relation_elements[slice_idx]
            indicator_json = relation_indicators[slice_idx]

            # check if queried coords are a valid location
            for idx in range(50):

                padding = 0

                # subtracted max bounds to ensure valid coords
                slice_shape = current_slice.shape
                x_target = np.random.randint(0+padding,template_im.shape[1]-slice_shape[1]-padding)
                y_target = np.random.randint(0+padding,template_im.shape[0]-slice_shape[0]-padding)
                
                # check if selected template area is good
                if check_slice(template_im,slice_shape,x_target,y_target,padding):

                    template_im[y_target:y_target+slice_shape[0],x_target:x_target+slice_shape[1],:] = current_slice

                    # reindex labels and adjust bboxes
                    current_relation = copy.deepcopy(relation)
                    current_els = copy.deepcopy(els_json)
                    current_indicator_json = copy.deepcopy(indicator_json)

                    # reindex elements
                    reindexed_els = []
                    for el_json in current_els:

                        split1 = el_json['label'].split(":")
                        split1[0] = str(element_indx)
                        el_json['id'] = element_indx
                        el_json['label'] = ":".join(split1)
                        element_indx += 1
                        reindexed_els.append(el_json)


                    # reindex relation and replace reindex elements
                    # get num of source and tar elements
                    tmp_str = current_relation['label'].split("|")
                    source_elements = tmp_str[0].split(":")[-1]
                    if "[" in source_elements:
                        tmp_str2 = source_elements[1:-1]
                        source_elements = tmp_str2.split(",")
                    else:
                        source_elements = [source_elements]

                    target_elements = tmp_str[-1]
                    if "[" in target_elements:
                        tmp_str2 = target_elements[1:-1]
                        target_elements = tmp_str2.split(",")
                    else:
                        target_elements = [target_elements]


                    # use num of source and tar elements as indices to reindexed_source_ids
                    reindexed_source_ids = []
                    for idx in range(len(source_elements)):
                        reindexed_source_ids.append(str(reindexed_els[idx]['id']))
                    
                    reindexed_tar_ids = []
                    for idx in range(len(target_elements)):
                        idx += len(source_elements)
                        reindexed_tar_ids.append(str(reindexed_els[idx]['id']))

                    # turn lists into strings
                    source_str = ",".join(reindexed_source_ids)
                    target_str = ",".join(reindexed_tar_ids)
                    if len(reindexed_source_ids) > 1:
                        source_str = "[" + source_str + "]"
                    if len(reindexed_tar_ids) > 1:
                        target_str = "[" + target_str + "]"

                    # set relation label to new reindexed values
                    split3 = current_relation['label'].split("|")
                    activation_type = split3[0].split(":")[1]
                    current_relation['label'] = str(element_indx) + ":" + activation_type + ":" + source_str + "|" + target_str
                    element_indx += 1

                    # reindex indicator
                    split3 = current_indicator_json['label'].split("|")
                    activation_type = split3[0].split(":")[1]
                    current_indicator_json['label'] = str(element_indx) + ":" + activation_type + ":" + source_str + "|" + target_str
                    element_indx += 1



                    # correct bbox values for slice
                    rel_pts = np.array(current_relation['points'])
                    ind_pts = np.array(current_indicator_json['points'])

                    rel_pts[:,0] += x_target
                    rel_pts[:,1] += y_target
                    ind_pts[:,0] += x_target
                    ind_pts[:,1] += y_target

                    # correct bbox values for relationship elements
                    output_els = []
                    for element in reindexed_els:
                        tmp_pts = np.array(element['points'])
                        tmp_pts[:,0] += x_target
                        tmp_pts[:,1] += y_target
                        element['points'] = tmp_pts.tolist()
                        output_els.append(element)



                    current_relation['points'] = rel_pts.tolist()
                    current_indicator_json['points'] = ind_pts.tolist()

                    for element in output_els:
                        shapes.append(element)


                    shapes.append(current_relation)
                    shapes.append(current_indicator_json)

                    break



            # tmp_template_im = copy.deepcopy(template_im)
            # tmp_template_im[np.all(tmp_template_im >= (245, 245, 245), axis=-1)] = template_mode_pix

            # # save json and new image
            # im_dir = "output_test"
            # image_path = str(self.copyID)+ "_" + str(relation_idx) + ".png"
            # cv2.imwrite(os.path.join(im_dir, image_path), tmp_template_im)
            # imageHeight = tmp_template_im.shape[0]
            # imageWidth = tmp_template_im.shape[1]
            # template_label_file = label_file.LabelFile()
            # template_label_file.save(os.path.join(im_dir,str(self.copyID) + ".json"),shapes,image_path,imageHeight,imageWidth)

        

        template_im[np.all(template_im >= (245, 245, 245), axis=-1)] = template_mode_pix


        # save json and new image
        im_dir = "/storage/hpc/data/jltmh3/output/output_training_data4"
        image_path = str(self.copyID) + ".png"
        cv2.imwrite(os.path.join(im_dir, image_path), template_im)
        imageHeight = template_im.shape[0]
        imageWidth = template_im.shape[1]
        template_label_file = label_file.LabelFile()
        template_label_file.save(os.path.join(im_dir,str(self.copyID) + ".json"),shapes,image_path,imageHeight,imageWidth)




# loop through all templates
stop_flag = False
directory = "/storage/hpc/data/jltmh3/datasets/templates"
template_list = os.listdir(directory)
# TODO:: make this more clean
for template_idx in range(len(template_list)):

    if stop_flag:
        break

    template_idx *= 4

    thread0 = template_thread(template_idx+0,"thread-0",template_list,directory)
    thread1 = template_thread(template_idx+1,"thread-1",template_list,directory)
    thread2 = template_thread(template_idx+2,"thread-2",template_list,directory)
    thread3 = template_thread(template_idx+3,"thread-3",template_list,directory)


    thread0.start()
    if template_idx + 1 > len(template_list):
        stop_flag = True
        continue
    else:
        thread1.start()
    if template_idx + 2 > len(template_list):
        stop_flag = True
        continue
    else:
        thread2.start()
    if template_idx + 3 > len(template_list):
        stop_flag = True
        continue
    else:
        thread3.start()

    thread0.join()
    thread1.join()
    thread2.join()
    thread3.join()
