import math
import cv2 
from utils import get_distance, overlay_image, check_owner
from constants import (
    EYE_SCALED_FACTOR, 
    DROP_CHAKRA_FACTOR, 
    SHARINGAN_STAGES, 
    MANGEKYOU_ABILITIES, 
    SUSANO_SCALED_FACTOR,
)
from ..dojutsu import AmaterasuEffect, TsukuyomiEffect, KamuiEffect, SusanooEffect, KotoamatsukamiEffect
from typing import List

class DojutsuFactory:
    def __init__(self, dojutsu_img: cv2.Mat, sharingan_stage: str, mangekyou_owner: str, mangekyou_technique: List[str], eye_opened_coef: float, current_chakra: float):
        self.eye_opened_coef = eye_opened_coef
        self.dojutsu_img = dojutsu_img
        self.sharingan_stage = sharingan_stage
        self.mangekyou_technique = mangekyou_technique
        self.mangekyou_owner = mangekyou_owner
        self.current_chakra = current_chakra

        self.blindness_counter = 0
        self.face_results = None
        self.is_left_eye_open = False
        self.is_right_eye_open = False
        self.active_effects = {}
        
    def draw_eye_effect(self, frame, dt, holistic_results) -> cv2.Mat:
        """Draws the Sharingan overlay on the eyes."""        
        h, w = frame.shape[:2]
        self.face_results = holistic_results.face_landmarks

        if not self.face_results:
            return frame

        landmarks = self.face_results.landmark
        
        def check_eye_open(top_idx, bottom_idx, inner_idx, outer_idx):
            pt_top, pt_bottom = landmarks[top_idx], landmarks[bottom_idx]
            vertical_distance = get_distance(pt_top, pt_bottom, w, h)

            pt_inner, pt_outer = landmarks[inner_idx], landmarks[outer_idx]
            horizontal_distance = get_distance(pt_inner, pt_outer, w, h)

            if horizontal_distance == 0: return False
            return (vertical_distance / horizontal_distance) > self.eye_opened_coef

        self.is_left_eye_open = check_eye_open(159, 145, 33, 133)
        self.is_right_eye_open = check_eye_open(386, 374, 362, 263)
        
        def process_eye(center_idx, border_idx, opp_border_idx):
            cx, cy = int(landmarks[center_idx].x * w), int(landmarks[center_idx].y * h)
            p1 = (landmarks[border_idx].x * w, landmarks[border_idx].y * h)
            p2 = (landmarks[opp_border_idx].x * w, landmarks[opp_border_idx].y * h)
            diameter = math.hypot(p1[0] - p2[0], p1[1] - p2[1])
            size = int(diameter * EYE_SCALED_FACTOR)

            if size <= 0: return frame
            
            resized_eye = cv2.resize(self.dojutsu_img, (size, size))
            return overlay_image(frame, resized_eye, cx, cy)
        
        if self.is_left_eye_open: frame = process_eye(468, 474, 476)                
        if self.is_right_eye_open: frame = process_eye(473, 469, 471)
                
        drain_per_second = SHARINGAN_STAGES.get(self.sharingan_stage, {}).get("chakra_cost", 0) * DROP_CHAKRA_FACTOR
        self.current_chakra = max(0, self.current_chakra - (drain_per_second * dt))    
        return frame
    
    def draw_mangekyou_techniques_effect(self, frame, dt, center, x, y, kamui_active, holistic_results, mp_holistic) -> tuple:
        """Draws the Mangekyou Sharingan techniques based on the owner and technique."""  
          
        if "amaterasu" in self.mangekyou_technique and (not self.is_left_eye_open and self.is_right_eye_open) and check_owner(self.mangekyou_owner, "amaterasu"):
            if "amaterasu" not in self.active_effects:
                self.active_effects["amaterasu"] = AmaterasuEffect()
            frame, self.blindness_counter = self.active_effects["amaterasu"].apply(frame, results=self.face_results)
            drain_per_second = MANGEKYOU_ABILITIES.get("amaterasu", {}).get("chakra_cost", 0) * DROP_CHAKRA_FACTOR
            
        elif "tsukuyomi" in self.mangekyou_technique and (self.is_left_eye_open and not self.is_right_eye_open) and check_owner(self.mangekyou_owner, "tsukuyomi"):
            if "tsukuyomi" not in self.active_effects:
                self.active_effects["tsukuyomi"] = TsukuyomiEffect()
            frame, self.blindness_counter = self.active_effects["tsukuyomi"].apply(frame, results=self.face_results)
            drain_per_second = MANGEKYOU_ABILITIES.get("tsukuyomi", {}).get("chakra_cost", 0) * DROP_CHAKRA_FACTOR
            
        elif "kamui" in self.mangekyou_technique and (self.is_left_eye_open and not self.is_right_eye_open) and check_owner(self.mangekyou_owner, "kamui"):  
            if "kamui" not in self.active_effects:
                self.active_effects["kamui"] = KamuiEffect(center=center, radius=300, strength=5.0)
            if kamui_active:
                self.active_effects["kamui"].center = center
                frame, self.blindness_counter = self.active_effects["kamui"].apply(frame)
            drain_per_second = MANGEKYOU_ABILITIES.get("kamui", {}).get("chakra_cost", 0) * DROP_CHAKRA_FACTOR if kamui_active else 0.0

        elif "susanoo" in self.mangekyou_technique and (self.is_left_eye_open and self.is_right_eye_open) and check_owner(self.mangekyou_owner, "susanoo"):             
            if "susanoo" not in self.active_effects:
                self.active_effects["susanoo"] = SusanooEffect(susanoo_scale_factor=SUSANO_SCALED_FACTOR)
            frame, self.blindness_counter = self.active_effects["susanoo"].apply(frame=frame, face_results=self.face_results, holistic_results=holistic_results, mp_holistic=mp_holistic) 
            drain_per_second = MANGEKYOU_ABILITIES.get("susanoo", {}).get("chakra_cost", 0) * DROP_CHAKRA_FACTOR
        
        elif "kotoamatsukami" in self.mangekyou_technique and (not self.is_left_eye_open and self.is_right_eye_open) and check_owner(self.mangekyou_owner, "kotoamatsukami"):  
            if "kotoamatsukami" not in self.active_effects:
                self.active_effects["kotoamatsukami"] = KotoamatsukamiEffect()
            frame, self.blindness_counter = self.active_effects["kotoamatsukami"].apply(frame=frame, x=x, y=y)
            drain_per_second = MANGEKYOU_ABILITIES.get("kotoamatsukami", {}).get("chakra_cost", 0) * DROP_CHAKRA_FACTOR
        
        # I'll pass, you do it, Author: ioscbasotcstw
        elif "kagutsuchi" in self.mangekyou_technique and (not self.is_left_eye_open and self.is_right_eye_open) and check_owner(self.mangekyou_owner, "kagutsuchi"):             
            pass
        else:
            return frame, self.blindness_counter
            
        self.current_chakra = max(0, self.current_chakra - (drain_per_second * dt))
        return frame, self.blindness_counter
    
    def draw_dojutsu_effect(self, frame, dt, blindness_stage, center, x, y, kamui_active, holistic_results, mp_holistic) -> tuple:
        """Call stack to draw dojutsu effects in sequence."""
        if blindness_stage == "heavy":
            return frame, self.blindness_counter, self.current_chakra
        
        if self.dojutsu_img is not None:
            frame = self.draw_eye_effect(frame, dt, holistic_results)

        if getattr(self, "mangekyou_technique", None):
            frame, self.blindness_counter = self.draw_mangekyou_techniques_effect(frame, dt, center, x, y, kamui_active, holistic_results, mp_holistic)

        return frame, self.blindness_counter, self.current_chakra