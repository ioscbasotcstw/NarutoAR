import os
import cv2
from utils import get_distance, overlay_image

from .style_interface import StyleInterface

class HeadBandStyle(StyleInterface):
    def __init__(self, filename: str, holistic_results):
        super().__init__()
        img_path = os.path.join("src/assets/styles/", filename)
        if not os.path.exists(img_path):
            raise FileNotFoundError(f"Image file '{filename}' not found in 'src/assets/styles/' directory.")
        self.headband_image = cv2.imread(img_path, cv2.IMREAD_UNCHANGED)
        if self.headband_image.shape[2] == 4: # If it has transparency (Alpha channel)
            self.headband_image = cv2.cvtColor(self.headband_image, cv2.COLOR_BGRA2RGBA)
        else:
            self.headband_image = cv2.cvtColor(self.headband_image, cv2.COLOR_BGR2RGB)
        self.holistic_results = holistic_results

    def apply(self, frame):
        """Applies the headband style to the given frame if the conditions are met."""
        face_results = self.holistic_results.face_landmarks

        if not face_results: return frame 

        h, w = frame.shape[:2]

        landmarks = face_results.landmark

        forehead_top = landmarks[10]
        forehead_bottom = landmarks[168]
        forehead_left = landmarks[54]
        forehead_right = landmarks[284]

        measure_height = int(get_distance(forehead_top, forehead_bottom, w, h))
        measure_width = int(get_distance(forehead_left, forehead_right, w, h))

        if measure_width == 0 or measure_height == 0: return frame

        cx, cy = int(landmarks[10].x * w + 10), int(landmarks[10].y * h + 15)

        headband_resize = cv2.resize(self.headband_image, (int(measure_width * 1.08), int(measure_height * 1.15)))
        frame = overlay_image(frame, headband_resize, cx, cy)

        return frame

class KakashiMaskStyle(StyleInterface):
    def __init__(self, filename: str, holistic_results):
        super().__init__()
        img_path = os.path.join("src/assets/styles/", filename)
        if not os.path.exists(img_path):
            raise FileNotFoundError(f"Image file '{filename}' not found in 'src/assets/styles/' directory.")
        self.kakashi_mask = cv2.imread(img_path, cv2.IMREAD_UNCHANGED)
        if self.kakashi_mask.shape[2] == 4: # If it has transparency (Alpha channel)
            self.kakashi_mask = cv2.cvtColor(self.kakashi_mask, cv2.COLOR_BGRA2RGBA)
        else:
            self.kakashi_mask = cv2.cvtColor(self.kakashi_mask, cv2.COLOR_BGR2RGB)
        self.holistic_results = holistic_results
        
    def apply(self, frame):
        """Applies the Kakashi mask style to the given frame if the conditions are met."""
        face_results = self.holistic_results.face_landmarks

        if not face_results: return frame 

        h, w = frame.shape[:2]

        landmarks = face_results.landmark

        nose = landmarks[168]
        chin = landmarks[152]
        left_cheek = landmarks[215]
        right_cheek = landmarks[435]

        measure_height = int(get_distance(nose, chin, w, h))
        measure_width = int(get_distance(left_cheek, right_cheek, w, h))

        if measure_width == 0 or measure_height == 0: return frame

        cx, cy = int(landmarks[13].x * w + 10), int(landmarks[13].y * h)

        headband_resize = cv2.resize(self.kakashi_mask, (int(measure_width * 1.05), int(measure_height * 1.2)))
        frame = overlay_image(frame, headband_resize, cx, cy)

        return frame
    
class KakashiHairStyle(StyleInterface):
    def __init__(self, filename: str, holistic_results):
        super().__init__()
        img_path = os.path.join("src/assets/styles/", filename)
        if not os.path.exists(img_path):
            raise FileNotFoundError(f"Image file '{filename}' not found in 'src/assets/styles/' directory.")
        self.kakashi_hair = cv2.imread(img_path, cv2.IMREAD_UNCHANGED)
        if self.kakashi_hair.shape[2] == 4: # If it has transparency (Alpha channel)
            self.kakashi_hair = cv2.cvtColor(self.kakashi_hair, cv2.COLOR_BGRA2RGBA)
        else:
            self.kakashi_hair = cv2.cvtColor(self.kakashi_hair, cv2.COLOR_BGR2RGB)
        self.holistic_results = holistic_results
        
    def apply(self, frame):
        """Applies the Kakashi hair style to the given frame if the conditions are met."""
        face_results = self.holistic_results.face_landmarks

        if not face_results: return frame 

        h, w = frame.shape[:2]

        landmarks = face_results.landmark

        forehead_top = landmarks[10]
        forehead_bottom = landmarks[168]
        forehead_left = landmarks[54]
        forehead_right = landmarks[284]

        measure_height = int(get_distance(forehead_top, forehead_bottom, w, h))
        measure_width = int(get_distance(forehead_left, forehead_right, w, h))

        if measure_width == 0 or measure_height == 0: return frame

        cx, cy = int(landmarks[10].x * w + 35), int(landmarks[10].y * h - 30)

        headband_resize = cv2.resize(self.kakashi_hair, (int(measure_width * 2.1), int(measure_height * 2.5)))
        frame = overlay_image(frame, headband_resize, cx, cy)

        return frame
    
class TobiMaskStyle(StyleInterface):
    def __init__(self, filename: str, holistic_results):
        super().__init__()
        img_path = os.path.join("src/assets/styles/", filename)
        if not os.path.exists(img_path):
            raise FileNotFoundError(f"Image file '{filename}' not found in 'src/assets/styles/' directory.")
        self.obito_mask = cv2.imread(img_path, cv2.IMREAD_UNCHANGED)
        if self.obito_mask.shape[2] == 4: # If it has transparency (Alpha channel)
            self.obito_mask = cv2.cvtColor(self.obito_mask, cv2.COLOR_BGRA2RGBA)
        else:
            self.obito_mask = cv2.cvtColor(self.obito_mask, cv2.COLOR_BGR2RGB)
        self.holistic_results = holistic_results
        
    def apply(self, frame):
        """Applies the Tobi mask style to the given frame if the conditions are met."""
        face_results = self.holistic_results.face_landmarks

        if not face_results: return frame 

        h, w = frame.shape[:2]

        landmarks = face_results.landmark

        forehead_top = landmarks[10]
        chin = landmarks[152]
        left_cheek = landmarks[137]
        right_cheek = landmarks[366]

        measure_height = int(get_distance(forehead_top, chin, w, h))
        measure_width = int(get_distance(left_cheek, right_cheek, w, h))

        if measure_width == 0 or measure_height == 0: return frame

        cx, cy = int(landmarks[5].x * w + 10), int(landmarks[5].y * h - 35)

        headband_resize = cv2.resize(self.obito_mask, (int(measure_width * 1.9), int(measure_height * 1.8)))
        frame = overlay_image(frame, headband_resize, cx, cy)

        return frame