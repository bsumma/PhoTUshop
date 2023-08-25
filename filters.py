import numpy as np
from PIL import Image
from math import *


def histogram_equalization(image):
    return image


def pad_image_reflect(image, filter_size):
    return Image.fromarray(np.array(
        np.pad(image, ((filter_size // 2, filter_size // 2), (filter_size // 2, filter_size // 2)), mode='reflect')))


def pad_image_zero(image, filter_size):
    return Image.fromarray(np.array(
        np.pad(image, ((filter_size // 2, filter_size // 2), (filter_size // 2, filter_size // 2)), mode='constant')))


def grab_window(image, window_size, center_x, center_y):
    window = []
    return window


def gaussian_kernel(filter_size, sigma):
    kernel = []
    return kernel


def gaussian_filter(image, filter_size, sigma):
    return image


def sobel_filter(image):
    return image


def canny_edge(image):
    return image
