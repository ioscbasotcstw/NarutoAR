import random 
import os
import cv2 
import numpy as np

from constants import BACKGROUNDS

class Backgrounds:
    def __init__(self, bg_resized):
        random_index = random.randint(0, len(BACKGROUNDS) - 1)
        randomly_choose_bg = BACKGROUNDS[random_index]

        if not os.path.exists(randomly_choose_bg):
            raise FileNotFoundError(f"Image file '{randomly_choose_bg}' not found in 'src/assets/backgrounds/' directory.")
                
        self.bg_image = cv2.imread(randomly_choose_bg)
        self.bg_image = cv2.cvtColor(self.bg_image, cv2.COLOR_BGRA2RGB)
        self.bg_resized = bg_resized

    def apply(self, frame: cv2.Mat, segmenter_results):
        """Applies the background to the given frame."""
        if segmenter_results is None or segmenter_results.segmentation_mask is None:
            return frame
                
        h, w = frame.shape[:2]

        if not self.bg_resized or self.bg_image.shape[:2] != (h, w):
            self.bg_image = cv2.resize(self.bg_image, (w, h))
            self.bg_resized = True

        mask = segmenter_results.segmentation_mask
        condition = np.stack((mask, ) * 3, axis=-1) > 0.99
        frame = np.where(condition, frame, self.bg_image).astype(np.uint8)
        return frame