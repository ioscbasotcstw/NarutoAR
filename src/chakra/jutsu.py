import time 
import cv2
import numpy as np
from utils import overlay_image, load_gif_frames, get_animated_frame
from .technique_interface import TechniqueInterface

class JutsuPerformedInsideHandEffect(TechniqueInterface):
    """Represents a Jutsu that is performed with hand signs and has an associated GIF animation (e.g. Chidori)."""
    def __init__(self, jutsu_path):
        self.jutsu_path = jutsu_path
        self.gif_frames = load_gif_frames(jutsu_path)
        self.frame_idx = 0
        self.last_frame_time = time.time()

        self.scale = 0
        self.x = 0
        self.y = 0

    def update(self, scale, x, y):
        """Updates the position and scale of the Jutsu effect."""
        self.scale = scale
        self.x = x
        self.y = y

    def apply(self, frame: cv2.Mat):
        """Applies the Jutsu effect to the given frame."""
        if self.scale <= 0 or self.gif_frames is None:
            return frame
        
        jutsu_frame, self.frame_idx, self.last_frame_time = get_animated_frame(
            self.gif_frames, 
            self.frame_idx, 
            self.last_frame_time, 
            fps=15
        )
        if jutsu_frame is None:
            return frame

        resized = cv2.resize(jutsu_frame, (self.scale, self.scale))
        frame = overlay_image(frame, resized, self.x, self.y)
        return frame, None
    
class JutsuPerformedAsBackgroundEffect(TechniqueInterface):
    """Represents a Jutsu that is performed without hand and changes the entire background (e.g. Death Reaper)."""
    def __init__(self, bg_image, bg_resized):
        self.bg_image = bg_image
        self.bg_resized = bg_resized

    def apply(self, frame: cv2.Mat, segmenter_results):
        """Applies the non-hand Jutsu effect (full background change) to the given frame."""
        if segmenter_results is None or segmenter_results.segmentation_mask is None:
            return frame, None
        
        h, w = frame.shape[:2]

        if not self.bg_resized or self.bg_image.shape[:2] != (h, w):
            self.bg_image = cv2.resize(self.bg_image, (w, h))
            self.bg_resized = True

        mask = segmenter_results.segmentation_mask
        condition = np.stack((mask, ) * 3, axis=-1) > 0.95
        frame = np.where(condition, frame, self.bg_image).astype(np.uint8)
        return frame, None
    
class WaterPrisonJutsuEffect(TechniqueInterface):
    """Represents a Jutsu that is performed without hand and uses OpenCV effects (e.g. Water Prison)."""
    def __init__(self, center_x, center_y, radius, precomputed_data):
        self.center_x = center_x
        self.center_y = center_y
        self.radius = int(radius)
        self.precomputed_data = precomputed_data
        50, 170, 255
        self.color = np.array([50, 170, 255], dtype=np.float32) # RGB format (Cyan/Blue)

    def apply(self, frame: cv2.Mat):
        """Applies the precomputed water effects to a specific spot on the frame."""
        map_x, map_y, shading, highlight, circle_mask = self.precomputed_data
        padded_frame = cv2.copyMakeBorder(frame, self.radius, self.radius, self.radius, self.radius, cv2.BORDER_REFLECT)
        cx = self.center_x + self.radius
        cy = self.center_y + self.radius
        y1, y2 = cy - self.radius, cy + self.radius
        x1, x2 = cx - self.radius, cx + self.radius
        roi = padded_frame[y1:y2, x1:x2]
        distorted = cv2.remap(roi, map_x, map_y, interpolation=cv2.INTER_LINEAR)
        alpha = 0.15 + (0.65 * shading)
        tinted = (distorted * (1 - alpha)) + (self.color * alpha)
        tinted += highlight
        np.clip(tinted , 0, 255, out=tinted)
        result_roi = (tinted * circle_mask) + (roi * (1 - circle_mask))
        padded_frame[y1:y2, x1:x2] = result_roi.astype(np.uint8, copy=False)
        h, w = frame.shape[:2]
        final_frame = padded_frame[self.radius:self.radius+h, self.radius:self.radius+w].copy()
        return final_frame, None