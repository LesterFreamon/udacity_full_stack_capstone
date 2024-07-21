from typing import List, Dict, Any

import cv2
import numpy as np


def create_segmentation_layer(masks: List[Dict[str, Any]], original_image: np.ndarray) -> np.ndarray:
    """Create a segmentation layer from the masks provided."""
    # Assuming masks_info provides masks in a compatible format, else convert them.
    if len(masks) == 0:
        # return a blank image if no masks to process
        return np.zeros((original_image.shape[0], original_image.shape[1], 4)).astype(np.uint8)

    sorted_masks = sorted(masks, key=(lambda x: x['area']), reverse=True)

    img = np.zeros((sorted_masks[0]['segmentation'].shape[0], sorted_masks[0]['segmentation'].shape[1], 4)).astype(
        np.uint8)

    img[:, :, 3] = 0
    for mask in sorted_masks:
        m = mask['segmentation']
        color_mask = np.concatenate([[np.random.randint(0, 256) for _ in range(3)], [255]])
        img[m] = color_mask

    return img


def create_rgba_image(rgb_image: np.ndarray) -> np.ndarray:
    """Create an RGBA image from an RGB image."""
    alpha_channel = np.ones((rgb_image.shape[0], rgb_image.shape[1]), dtype=np.uint8) * 255
    return np.dstack((rgb_image, alpha_channel))


def combine_two_images(image1: np.ndarray, image2: np.ndarray) -> np.ndarray:
    """Combine two images."""
    # add a dimension to image1
    return cv2.addWeighted(image1, 0.7, image2, 0.3, 0)
