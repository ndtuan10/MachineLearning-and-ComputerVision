# import libraries
import cv2 # library of Python is designed to solve CV problems
import numpy as np # package for scientific computing with Python
from PIL import Image, ImageTk # aka pillow, Python Imaging Library
import tkinter as tk # Python interface to the Tk GUI toolkt
from tkinter import *
import tkinter.messagebox
import time
import PIL.Image

# initialize list of reference points and boolean indicating
# whether cropping is performed or not???
list_refPt = [] # list of two (x,y)-coordinates specifying the rectangular region that we are going to crop imgage
cropping = False

"""Crops the image into smaller image with defined dimensions
# five function:
# 1. event: event that took place
# 2. x: the x-coordinate of the event
# 3. y: the y-coordinate of the event
# 4. flags: any relevant flags passed by OpenCV
# 5. params: any extra parameters supplied by OpenCV"""
def crop_image(event, x, y, flags, param):
    global refPt, cropping, list_refPt #grabbing references to global vars

    # if left mouse button was clicked so we record the beginning of #(x,y) coordinates
    if event == cv2.EVENT_LBUTTONDOWN:
        refPt = [[x, y]]
        cropping = True

    # check if the left mouse button was released
    elif event == cv2.EVENT_LBUTTONUP:
        # next we record the finishing of #(x,y) coordinates and indicate that
        # the cropping operation is finished
        refPt.append([x, y])
        cropping = False
        # drawing image with rectangle shape around the RoI
        cv2.rectangle(param, tuple(refPt[0]), tuple(refPt[1]), (0, 255, 255), 1) # with RGB pixel (0,255,255) and line thickness is 1
        refPt[0][0] += 2
        refPt[0][1] += 2
        refPt[1][0] -= 2
        refPt[1][1] -= 2
        list_refPt.append(refPt)
        cv2.imshow('image', param) # display image

# choose rang of image, clone it, and setup the mouse callback function
def choose_range(image):
    clone = image.copy()
    cv2.namedWindow("image")
    cv2.setMouseCallback("image", crop_image, param=clone)

    # loop until the 'q' key is pressed
    while True:
        # display image and wait for a keypress
        cv2.imshow("image", clone)
        key = cv2.waitKey(1) & 0xFF

        # if the 'r' key is pressed, reset the cropping region
        if key == ord("r"):
            clone = image.copy()
        
        # if the 'c' key is pressed, break from the loop
        elif key == ord("c"):
            break


def roi_image(list_refPt, image):
    list_roi = []
    for refPt in list_refPt:
        clone = image.copy()
        list_roi.append(clone[refPt[0][1]:refPt[1][1], refPt[0][0]:refPt[1][0]])
    return list_roi


# to determine the color space, we perform the gaussian probability distribution
def gaussian(x):
    muy = np.mean(x) # expected value muy, aka mean value
    sigma = np.std(x) # standard deviation sigma

    # we find color space in the reliable range, here the standard deviation is 2 * sigma
    low = muy - 2 * sigma
    upper = muy + 2 * sigma
    return abs(int(low)), abs(int(upper))

# processing with color image
# we use HSV color system (HUE, SATURATION, VALUE)

# fine HUE (or color zone)
def find_H(low_lst, high_lst):
    min = 255
    max = 0
    for i in low_lst:
        if i[0] < min:
            min = i[0]
    for j in high_lst:
        if j[0] > max:
            max = j[0]
    return min, max

# fine SATURATION
def find_S(low_lst, high_lst):
    min = 255
    max = 0
    for i in low_lst:
        if i[1] < min:
            min = i[1]
    for j in high_lst:
        if j[1] > max:
            max = j[1]
    return min, max

# fine VALUE (or brightness of color)
def find_V(low_lst, high_lst):
    min = 255
    max = 0
    for i in low_lst:
        if i[2] < min:
            min = i[2]
    for j in high_lst:
        if j[1] > max:
            max = j[2]
    return min, max

# display image after crop the region of interest
def find_range(image, list_refPt):
    list_roi = roi_image(list_refPt, image)  # region of interest image
    low_lst = []
    high_lst = []
    for img in list_roi:
        img_hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

        # Separate region follow by H, S, V
        h, s, v = cv2.split(img_hsv)

        # Find min, max H, S, V
        low_h, high_h = gaussian(h)  
        low_s, high_s = gaussian(s)
        low_v, high_v = gaussian(v)

        low_lst.append([low_h, low_s, low_v])
        high_lst.append([high_h, high_s, high_v])
    return low_lst, high_lst


def chroma_pro(image, background, low_lst, high_lst, index = 1):
    min, max = find_H(low_lst, high_lst)
    # S, V usually with min max 100,255 20,255

    LOW = np.array([min - 10, 50, 50])
    HIGH = np.array([max + 10, 255, 255])

    # Test, convert images to images with HSV color system
    obj = image
    bg = background
    bg = cv2.resize(bg, (obj.shape[1], obj.shape[0]), interpolation=cv2.INTER_AREA)
    obj_hsv = cv2.cvtColor(obj, cv2.COLOR_BGR2HSV)

    # Finding mask object and background
    mask_bg = cv2.inRange(obj_hsv, LOW, HIGH)
    mask_obj = cv2.bitwise_not(mask_bg, mask=None)

    kernel = np.ones((5, 5), np.uint8)

    # reduction noise with morphology
    mask_obj = cv2.morphologyEx(mask_obj, cv2.MORPH_CLOSE, kernel)
    mask_bg = cv2.bitwise_not(mask_obj, mask=None)

    # object image and background
    # image_obj = image object
    # image_bg = image background
    image_obj = cv2.bitwise_and(obj, obj, mask=mask_obj) # Chroma Key object in the source image with background using BITWISE_AND method

    image_bg = cv2.bitwise_and(bg, bg, mask=mask_bg)

    chroma_image = cv2.bitwise_or(image_obj, image_bg)
    # cv2.imshow("chroma_image", chroma_image) to display chroma image
    # cv2. waitKey(0) to wait until any key is pressed
    if index == 1:
        cv2.imshow('mask background', mask_bg)
        cv2.waitKey(0)
        cv2.imshow('mask object', mask_obj)
        cv2.waitKey(0)
        cv2.imshow('mask background', mask_bg)
        cv2.waitKey(0)
        cv2.imshow('image object', image_obj)
        cv2.waitKey(0)
        cv2.imshow('image background', image_bg)
        cv2.waitKey(0)
        cv2.destroyAllWindows()

    return chroma_image


def image_process(file_img, file_bgr):
    img = cv2.imread(file_img) # read image
    bgr = cv2.imread(file_bgr) # read background
    choose_range(img) # allow to select the range to be merged
    low_lst, high_lst = find_range(img, list_refPt)
    chroma_img = chroma_pro(img, bgr, low_lst, high_lst,1)
    cv2.imshow('Result', chroma_img) 
    cv2.waitKey(0) # wait for a keypress
    cv2.destroyAllWindows() # close all




def close_window():
    root.destroy()

# choose image = 'human_3.jpg' and background = 'background_2.jpg'
file_img = 'human_3.jpg'
file_bgr = 'background_2.jpg'



root = tk.Tk()
root.geometry('720x360')


subBG = PIL.Image.open('background_2.jpg')
subBG.resize((720, 360))
subBG = ImageTk.PhotoImage(subBG)

frameMain = Frame(root)
frameMain.pack()

# main tilte of the program that runs result
varMain = StringVar()
labelMain = Label(frameMain, textvariable=varMain, relief=RAISED, height=100, width=720, padx=20, pady=20)
labelMain.config(font=("Time New Roman", 16, "bold"))
labelMain.config(image=subBG, compound='center')
varMain.set("Chroma Key Visual Effect")

# sub tilte of the program that runs result
varSub = StringVar()
labelSub = Label(frameMain, textvariable=varSub, relief=RAISED, bd=0)
labelSub.config(font=("Time New Roman", 12), pady=10)
varSub.set("Processing with: ")

labelMain.pack()
labelSub.pack()

frameSub = Frame(root)
frameSub.pack()

frameBottom = Frame(root)
frameBottom.pack(side=BOTTOM, fill='x')


A = Button(frameSub, text='Image', command = lambda : image_process(file_img, file_bgr), padx=10, pady=10)
A.config(font=("Courier", 12))




list_refPt = []
D = Button(frameBottom, text='End', command=close_window, padx=10, pady=10)
D.config(font=("Courier", 12))

A.grid(column=0, row=0, padx=10, pady=20)

D.pack(side=RIGHT)
root.mainloop()



