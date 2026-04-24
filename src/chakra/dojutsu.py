import os
import time 
import math
import random
import cv2
import numpy as np
from constants import MANGEKYOU_PATH
from utils import overlay_image, load_gif_frames, get_animated_frame, draw_eye_bleeding
from .technique_interface import TechniqueInterface


# Sharingan
class AmaterasuEffect(TechniqueInterface):
    def __init__(self, eye_bleeding: cv2.Mat):
        self.amaterasu_idx = 0
        self.amaterasu_time = time.time()
        self.blindness_counter = 0
        amaterasu_path = os.path.join(MANGEKYOU_PATH, "techniques/amaterasu.gif")
        if not os.path.exists(amaterasu_path):
            raise ValueError(f"Not such a file like {amaterasu_path}")
        self.gif_frames = load_gif_frames(amaterasu_path)
        self.eye_bleeding = eye_bleeding

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
        frame = draw_eye_bleeding(frame, self.eye_bleeding, results, "amaterasu")
        return frame, self.blindness_counter
    
class TsukuyomiEffect(TechniqueInterface):
    def __init__(self, eye_bleeding: cv2.Mat):
        self.blindness_counter = 0
        self.eye_bleeding = eye_bleeding
        # self.mask = np.linspace(1, 0, height, dtype=np.float32)[:, np.newaxis, np.newaxis]

    def apply(self, frame: cv2.Mat, results):
        """Applies the Tsukuyomi effect to the given frame if the conditions are met."""
        self.blindness_counter += 1
        random_factor = np.random.uniform(0.01, 0.05)  # Random factor to vary the intensity of the effect
        random_factor = round(random_factor, 2)  # Round to 2 decimal places for consistency
        height, _ = frame.shape[:2]
        inversed = cv2.bitwise_not(frame).astype(np.float32) # Invert colors

        red_tint = frame.astype(np.float32)
        np.clip(red_tint[:, :, 2] * 20.0, 0, 255, out=red_tint[:, :, 0])   # Boost Red
        red_tint[:, :, 1] *= 0.3 # Reduce Green
        red_tint[:, :, 2] *= 0.3 # Reduce Blue

        # (height, 1, 1)
        mask = np.linspace(1, 0, height, dtype=np.float32)[:, np.newaxis, np.newaxis]

        # Inversed + Mask * (Red_Tint - Inversed)
        red_tint -= inversed
        red_tint *= mask
        inversed += red_tint

        frame = inversed.astype(np.uint8)

        frame = draw_eye_bleeding(frame, self.eye_bleeding, results, "tsukuyomi")
        if random_factor > 0:
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
        """""Applies the Kamui effect to the given frame if the conditions are met."""
        rows, cols = frame.shape[:2]
        
        if (self.map_x is None or 
            self.center != self.prev_center or 
            (rows, cols) != self.prev_shape):
            
            self._generate_map(rows, cols)
            self.prev_center = self.center
            self.prev_shape = (rows, cols)

            if len(self.blur_mask.shape) == 2:
                # (H, W, 1)
                self.blur_mask = self.blur_mask[:, :, np.newaxis]

        # (H, W, 3)
        remaped = cv2.remap(frame, self.map_x, self.map_y, interpolation=cv2.INTER_LINEAR).astype(np.float32)
        blurred = cv2.GaussianBlur(remaped, (15, 15), 0)
        # Result = b * m + (1.0 - m) * f
        # frame = blurred * mask + frame * (1.0 - mask)
        
        # Result = bm + r - mr
        # Result = r + bm - mr
        # Result = r + m * (b - r)
        blurred -= remaped
        blurred *= self.blur_mask 
        remaped += blurred
        return remaped.astype(np.uint8), self.blindness_counter

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
        self.blur_mask = blur_mask.astype(np.float32)

class SusanooEffect(TechniqueInterface):
    def __init__(self,susanoo: cv2.Mat, susanoo_scale_factor: float):
        self.susanoo = susanoo
        self.susanoo_scale_factor = susanoo_scale_factor
        self.blindness_counter = 0

    def apply(self, frame, face_results, holistic_results, mp_holistic):
        """Applies the Susanoo effect to the given frame if the conditions are met."""
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
    def __init__(self, kotoamatsukami: cv2.Mat):
        self.blindness_counter = 0
        self.kotoamatsukami = kotoamatsukami

    def apply(self, frame, x, y):
        """""Applies the Kotoamatsukami effect to the given frame if the conditions are met."""
        x, y = int(x), int(y)
        h, w = frame.shape[:2]
        y1, y2, x1, x2 = 20, h - 20, 20, w - 20
        emerald_green_color_rgb = (0,77,36)

        blured = cv2.GaussianBlur(frame, (41, 41), 0)
        hazy_layer = np.full(frame.shape, 220, np.uint8)
        hazy_final = cv2.addWeighted(blured, 0.8, hazy_layer, 0.2, 0)
        hazy_final[y1:y2, x1:x2] = frame[y1:y2, x1:x2]

        emerald_green_image = np.full(frame.shape, emerald_green_color_rgb, np.uint8)
        emerald_hazy_image = cv2.addWeighted(hazy_final, 0.7, emerald_green_image, 0.3, 0)

        frame = overlay_image(emerald_hazy_image, self.kotoamatsukami, x, y)
        return frame, self.blindness_counter  

class OhirumeEffect(TechniqueInterface):
    def __init__(self):
        self.centers = []
        self.prev_active = False
        self.blindness_counter = 0

    def update(self, center, is_active):
        if is_active and not self.prev_active:
            radius = random.randint(5, 100)
            self.centers.append((center, radius))
        self.prev_active = is_active

    def reset(self):
        self.centers.clear()
    
    def apply(self, frame):
        if not self.centers or len(self.centers) > 4: 
            self.reset()
            return frame, self.blindness_counter

        for (x, y), r in self.centers:
            cv2.circle(frame, (x, y), r, (0, 0, 0), -1)
        return frame, self.blindness_counter

# Rinnegan
class ChibakuTenseiEffect(TechniqueInterface):
    def __init__(self, center):
        self.center = center
        self.radius = 0
        self.blindness_counter = 0
        self.halo_color = (150, 220, 255)

    def update(self, radius):
        self.radius = radius

    def reset(self):
        self.radius = 0
    
    def apply(self, frame):
        """Applies the Chibaku Tensei effect to the given frame if the conditions are met."""
        if not self.center or self.radius <= 0: return frame, self.blindness_counter

        x, y, r = int(self.center[0]), int(self.center[1]), int(self.radius)

        glow_mask = np.zeros_like(frame)
        halo_radius = int(r * 1.5)
        cv2.circle(glow_mask, (x, y), halo_radius, self.halo_color, -1)

        k_size = int(r * 2.0)
        if k_size % 2 == 0: k_size += 1
        k_size = max(3, k_size)

        glow_mask = cv2.GaussianBlur(glow_mask, (k_size, k_size), 0)
        frame = cv2.add(frame, glow_mask)

        cv2.circle(frame, (x, y), r, (0, 0, 0), -1)
        return frame, self.blindness_counter

# Byakugan  
class ByakuganEffect(TechniqueInterface):
    def __init__(self):
        self.blindness_counter = 0

    def apply(self, frame: cv2.Mat):
        """Applies the Byakugan effect to the given frame if the conditions are met."""
        inversed = cv2.bitwise_not(frame).astype(np.float32)
        reduce = inversed.astype(np.float32)
        reduce[:, :, 2] *= 0.9 # Reduce Red
        reduce[:, :, 1] *= 0.9 # Reduce Green
        reduce[:, :, 0] *= 0.9 # Reduce Blue
        frame = reduce.astype(np.uint8)
        return frame, self.blindness_counter