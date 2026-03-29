import os
import time 
import math
import cv2
import numpy as np
from constants import MANGEKYOU_PATH
from utils import overlay_image, load_gif_frames, get_animated_frame, draw_eye_bleeding
from .technique_interface import TechniqueInterface

class AmaterasuEffect(TechniqueInterface):
    def __init__(self):
        self.amaterasu_idx = 0
        self.amaterasu_time = time.time()
        self.blindness_counter = 0
        amaterasu_path = os.path.join(MANGEKYOU_PATH, "techniques/amaterasu.gif")
        if not os.path.exists(amaterasu_path):
            raise ValueError(f"Not such a file like {amaterasu_path}")
        self.gif_frames = load_gif_frames(amaterasu_path)

    def apply(self, frame: cv2.Mat, results):
        """Applies the Amaterasu effect to the given frame if the conditions are met."""       
        self.blindness_counter += 1
        amaterasu, self.amaterasu_idx, self.amaterasu_time = get_animated_frame(
            self.gif_frames, 
            self.amaterasu_idx, 
            self.amaterasu_time, 
            fps=15
        )
        if amaterasu is None:
            return frame, self.blindness_counter

        h, w = frame.shape[:2]
        resized = cv2.resize(amaterasu, (w, h))
        frame = overlay_image(frame, resized, w // 2, h // 2)
        frame = draw_eye_bleeding(frame, results, "amaterasu")
        return frame, self.blindness_counter
    
class TsukuyomiEffect(TechniqueInterface):
    def __init__(self):
        self.blindness_counter = 0

    def apply(self, frame: cv2.Mat, results):
        """Applies the Tsukuyomi effect to the given frame if the conditions are met."""
        self.blindness_counter += 1
        random_factor = np.random.uniform(0.01, 0.10)  # Random factor to vary the intensity of the effect
        random_factor = round(random_factor, 2)  # Round to 2 decimal places for consistency
        height, width = frame.shape[:2]
        inversed = frame.copy()
        inversed = cv2.bitwise_not(inversed) # Invert colors

        red_tint = frame.copy()
        red_tint[:, :, 0] = red_tint[:, :, 0] * 0.3 # Reduce Blue
        red_tint[:, :, 1] = red_tint[:, :, 1] * 0.3 # Reduce Green
        red_tint[:, :, 2] = np.clip(red_tint[:, :, 2] * 20.0, 0, 255) # Boost Red

        mask1d = np.linspace(1, 0, height) 
        mask3d = np.tile(mask1d[:, None, None], (1, width, 3)) 

        frame = (red_tint * mask3d) + (inversed * (1 - mask3d))
        frame = frame.astype(np.uint8)

        frame = draw_eye_bleeding(frame, results, "tsukuyomi")
        time.sleep(random_factor) 
        return frame, self.blindness_counter
    
class KamuiEffect(TechniqueInterface):
    def __init__(self, center, radius=250, strength=10.0):
        self.center = center
        self.radius = radius
        self.strength = strength

        self.map_x = None
        self.map_y = None
        self.prev_center = None
        self.prev_shape = None
        self.blur_mask = None
        self.blindness_counter = 0

    def apply(self, frame):
        rows, cols = frame.shape[:2]
        
        if (self.map_x is None or 
            self.center != self.prev_center or 
            (rows, cols) != self.prev_shape):
            
            self._generate_map(rows, cols)
            self.prev_center = self.center
            self.prev_shape = (rows, cols)

        frame = cv2.remap(frame, self.map_x, self.map_y, interpolation=cv2.INTER_LINEAR)
        blured_swirl = cv2.GaussianBlur(frame, (15, 15), 0)
        mask_3ch = np.dstack([self.blur_mask] * 3)
        frame = blured_swirl * mask_3ch + frame * (1.0 - mask_3ch)
        frame = frame.astype(np.uint8)
        return frame, self.blindness_counter

    def _generate_map(self, rows, cols):
        cent_x, cent_y = self.center
        y_coords, x_coords = np.indices((rows, cols), dtype=np.float32)
        delta_x = x_coords - cent_x
        delta_y = y_coords - cent_y
        r, theta = cv2.cartToPolar(delta_x, delta_y)
        mask = r < self.radius
        # Swirl Math
        # twist = strength * (1 - distance / radius)
        swirl_amount = self.strength * (1.0 - (r[mask] / self.radius))
        theta[mask] += swirl_amount
        # Лінзування (Suction) ефект
        # r[mask] = r[mask] ** 0.9
        map_x, map_y = cv2.polarToCart(r, theta)
        map_x += cent_x
        map_y += cent_y
        
        self.map_x = map_x
        self.map_y = map_y
        
        normalized_r = r / self.radius
        blur_mask = 1.0 - normalized_r
        blur_mask[blur_mask < 0] = 0
        self.blur_mask = blur_mask

class SusanooEffect(TechniqueInterface):
    def __init__(self, susanoo_scale_factor: float):
        self.susanoo_scale_factor = susanoo_scale_factor
        susanoo_path = os.path.join(MANGEKYOU_PATH, "techniques/susanoo.png")
        if not os.path.exists(susanoo_path):
            raise ValueError(f"Not such a file like {susanoo_path}")
        self.susanoo = cv2.imread(susanoo_path, cv2.IMREAD_UNCHANGED)

        self.blindness_counter = 0

    def apply(self, frame, face_results, holistic_results, mp_holistic):
        if self.susanoo is None: return frame

        pose_results = holistic_results.pose_landmarks

        if not pose_results or not face_results:
            return frame
        
        h, w = frame.shape[:2]
        face_landmarks = face_results.landmark
        pose_landmarks = pose_results.landmark
        lm_pose = mp_holistic.PoseLandmark

        # Calculate width using shoulders
        l_sh = pose_landmarks[lm_pose.LEFT_SHOULDER]
        r_sh = pose_landmarks[lm_pose.RIGHT_SHOULDER]
        width_distance = math.hypot((l_sh.x - r_sh.x) * w, (l_sh.y - r_sh.y) * h)

        # Calculate height using forehead (landmark 10)
        head_lm = face_landmarks[10]
        x, y = int(head_lm.x * w), int(head_lm.y * h)
        height_distance = math.hypot(x - (w//2), y - h)

        x_size = int(width_distance * self.susanoo_scale_factor)
        y_size = int(height_distance * self.susanoo_scale_factor)

        if x_size > 0 and y_size > 0:
            resized = cv2.resize(self.susanoo, (x_size, y_size))
            if resized.shape[2] == 4:
                resized[:,:,3] = (resized[:,:,3] * 0.5).astype(np.uint8)
            frame = overlay_image(frame, resized, x, y + int(y_size * 0.1))
        return frame, self.blindness_counter
    
class KotoamatsukamiEffect(TechniqueInterface):
    def __init__(self):
        kotoamatsukami_path = os.path.join(MANGEKYOU_PATH, "feather.png")
        if not os.path.exists(kotoamatsukami_path):
            raise ValueError(f"Not such a file like {kotoamatsukami_path}")
        self.kotoamatsukami = cv2.imread(kotoamatsukami_path, cv2.IMREAD_UNCHANGED)

        self.blindness_counter = 0

    def apply(self, frame, x, y):
        x, y = int(x), int(y)
        h, w = frame.shape[:2]
        y1, y2, x1, x2 = 20, h - 20, 20, w - 20
        emerald_green_color = (0,77,36)

        blured = cv2.GaussianBlur(frame, (41, 41), 0)
        hazy_layer = np.full(frame.shape, 220, np.uint8)
        hazy_final = cv2.addWeighted(blured, 0.8, hazy_layer, 0.2, 0)
        hazy_final[y1:y2, x1:x2] = frame[y1:y2, x1:x2]

        emerald_green_image = np.full(frame.shape, emerald_green_color, np.uint8)
        emerald_hazy_image = cv2.addWeighted(hazy_final, 0.7, emerald_green_image, 0.3, 0)

        frame = overlay_image(emerald_hazy_image, self.kotoamatsukami, x, y)
        return frame, self.blindness_counter