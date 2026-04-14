import math
import cv2
from ..jutsu import JutsuPerformedInsideHandEffect, JutsuPerformedAsBackgroundEffect, WaterPrisonJutsuEffect
from constants import DROP_CHAKRA_FACTOR, JUTSU_CATALOG
from typing import Any


class JutsuFactory:
    def __init__(self, 
                cached_jutsu_effect: Any, 
                precomputed_data: Any, 
                jutsu_path: str, 
                jutsu_name: str, 
                bg_image: cv2.Mat, 
                bg_resized: bool, 
                is_sequantial: bool, 
                has_image: bool, 
                is_hand_jutsu: bool, 
                radius: int, 
                current_chakra: float, 
                scale_factor_for_image_jutsu: float = 3.5
        ):
        self.cached_jutsu_effect = cached_jutsu_effect
        self.precomputed_data = precomputed_data 
        self.jutsu_path = jutsu_path
        self.jutsu_name = jutsu_name
        self.bg_image = bg_image 
        self.bg_resized = bg_resized 
        self.is_sequantial = is_sequantial
        self.has_image = has_image 
        self.is_hand_jutsu = is_hand_jutsu
        self.radius = radius 
        self.current_chakra = current_chakra
        self.scale_factor_for_image_jutsu = scale_factor_for_image_jutsu  

    def draw_hand_jutsu_effect(self, frame, dt, holistic_results) -> cv2.Mat:
        """""Draws hand-based jutsu effects on the frame based on detected hand landmarks."""
        h, w = frame.shape[:2]
        hands_to_process = []
        if holistic_results.left_hand_landmarks:
            hands_to_process.append(holistic_results.left_hand_landmarks)
        elif holistic_results.right_hand_landmarks:
            hands_to_process.append(holistic_results.right_hand_landmarks)

        for hand_lm in hands_to_process:
            lm_0, lm_9 = hand_lm.landmark[0], hand_lm.landmark[9]
            x, y = int(lm_9.x * w), int(lm_9.y * h)
            hand_size = math.hypot((lm_9.x - lm_0.x) * w, (lm_9.y - lm_0.y) * h)
            scale = int(hand_size * self.scale_factor_for_image_jutsu)

            if scale > 0:
                if self.cached_jutsu_effect is None or self.cached_jutsu_effect.jutsu_path != self.jutsu_path:
                    self.cached_jutsu_effect = JutsuPerformedInsideHandEffect(jutsu_path=self.jutsu_path)
                self.cached_jutsu_effect.update(scale=scale, x=x, y=y)
                frame, _ = self.cached_jutsu_effect.apply(frame)
                        
        drain_per_second = JUTSU_CATALOG.get(self.jutsu_name, {}).get("chakra_cost", 0) * DROP_CHAKRA_FACTOR
        self.current_chakra = max(0, self.current_chakra - (drain_per_second * dt))
        return frame
    
    def draw_no_hand_jutsu_effect(self, frame, dt, segmenter_results) -> cv2.Mat:
        """"Draws background-based jutsu effects on the frame based on segmenter results."""
        no_hand_jutsu = JutsuPerformedAsBackgroundEffect(bg_image=self.bg_image, bg_resized=self.bg_resized)
        frame, _ = no_hand_jutsu.apply(frame, segmenter_results)
                
        drain_per_second = JUTSU_CATALOG.get(self.jutsu_name, {}).get("chakra_cost", 0) * DROP_CHAKRA_FACTOR
        self.current_chakra = max(0, self.current_chakra - (drain_per_second * dt))
        return frame
    
    def draw_water_prison_jutsu_effect(self, frame, dt, holistic_results, mp_holistic) -> cv2.Mat: 
        """Draws the Water Prison Jutsu effect on the frame based on pose landmarks."""
        h, w = frame.shape[:2]
        center_x, center_y = w // 2, h // 2

        pose_results = holistic_results.pose_landmarks

        if not pose_results:
            return frame

        results = pose_results.landmark
        lm_pose = mp_holistic.PoseLandmark
        l_shoulder_x = results[lm_pose.LEFT_SHOULDER].x * w 
        r_shoulder_x = results[lm_pose.RIGHT_SHOULDER].x * w
        middle_between_shoulders = int((l_shoulder_x + r_shoulder_x) // 2)
        center_x += int((middle_between_shoulders - center_x) * 0.5) 
        cv2_jutsu = WaterPrisonJutsuEffect(center_x=center_x, center_y=center_y, radius=self.radius, precomputed_data=self.precomputed_data)
        frame, _ = cv2_jutsu.apply(frame)
                
        drain_per_second = JUTSU_CATALOG.get(self.jutsu_name, {}).get("chakra_cost", 0) * DROP_CHAKRA_FACTOR
        self.current_chakra = max(0, self.current_chakra - (drain_per_second * dt))
        return frame
    
    def draw_jutsu_effect(self, frame, dt, blindness_stage, jutsu_active, disable_bg, target_sequence, history, holistic_results, segmenter_results, mp_holistic) -> tuple:
        """Determines which jutsu effect to draw based on the current state and applies it to the frame."""
        if blindness_stage == "heavy":
            return frame, self.current_chakra
        
        if segmenter_results is None:
            return frame, self.current_chakra
            
        if not self.is_sequantial and self.jutsu_path is not None:
            return self.draw_hand_jutsu_effect(frame=frame, dt=dt, holistic_results=holistic_results), self.current_chakra

        if not jutsu_active:
            return frame, self.current_chakra
        
        if self.has_image:
            if self.is_hand_jutsu and self.jutsu_path is None: return frame, self.current_chakra
            if not self.is_hand_jutsu and self.bg_image is None: return frame, self.current_chakra

        jutsu_type = JUTSU_CATALOG.get(self.jutsu_name, {}).get("type")

        if self.has_image:
            if self.is_hand_jutsu and jutsu_type == "base_hand":
                return self.draw_hand_jutsu_effect(frame=frame, dt=dt, holistic_results=holistic_results), self.current_chakra
            elif not self.is_hand_jutsu and jutsu_type == "background_base" and disable_bg:
                return self.draw_no_hand_jutsu_effect(frame=frame, dt=dt, segmenter_results=segmenter_results), self.current_chakra
        elif not self.has_image and jutsu_type == "cv2_base":
            return self.draw_water_prison_jutsu_effect(frame=frame, dt=dt, holistic_results=holistic_results, mp_holistic=mp_holistic), self.current_chakra
        
        return frame, self.current_chakra