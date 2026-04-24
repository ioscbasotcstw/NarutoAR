import math
import random
import cv2 
from utils import get_distance, overlay_image, check_owner
from constants import (
    EYE_SCALED_FACTOR, 
    DROP_CHAKRA_FACTOR, 
    SHARINGAN_STAGES, 
    RINNEGAN,
    BYAKUGAN,
    SIX_PATHS_TECHNIQUE,
    MANGEKYOU_ABILITIES, 
    SUSANO_SCALED_FACTOR,
    RIGHT_EYE_LANDMARKS,
    LEFT_EYE_LANDMARKS,
)
from ..dojutsu import (
    AmaterasuEffect, 
    TsukuyomiEffect, 
    KamuiEffect, 
    SusanooEffect, 
    KotoamatsukamiEffect, 
    OhirumeEffect,
    ChibakuTenseiEffect,
    ByakuganEffect,
)
from typing import List

class DojutsuFactory:
    def __init__(self, 
                dojutsu_img: cv2.Mat, 
                eye_bleeding: cv2.Mat,
                susanoo: cv2.Mat,
                kotoamatsukami: cv2.Mat,
                tomoe_3: cv2.Mat,
                rinnegan_left: cv2.Mat,
                rinnegan_right: cv2.Mat,
                byakugan: cv2.Mat,
                sharingan_stage: str, 
                mangekyou_owner: str, 
                mangekyou_technique: List[str], 
                eye_opened_coef: float, 
                current_chakra: float, 
        ):
        self.eye_opened_coef = eye_opened_coef
        self.dojutsu_img = dojutsu_img
        self.eye_bleeding = eye_bleeding
        self.susanoo = susanoo
        self.kotoamatsukami = kotoamatsukami
        self.tomoe_3 = tomoe_3
        self.rinnegan_left = rinnegan_left
        self.rinnegan_right = rinnegan_right
        self.byakugan = byakugan
        self.sharingan_stage = sharingan_stage
        self.mangekyou_technique = mangekyou_technique
        self.mangekyou_owner = mangekyou_owner
        self.current_chakra = current_chakra

        self.blindness_counter = 0
        self.radius = random.randint(5, 10)
        self.face_results = None
        self.is_left_eye_open = False
        self.is_right_eye_open = False
        self.active_effects = {}
        self.points = []

    def update(self, **args):
        self.args = args

    def _check_eye_open(self, landmarks, top_idx, bottom_idx, inner_idx, outer_idx, w, h):
        """Determines if an eye is open based on the ratio of vertical to horizontal distances."""
        pt_top, pt_bottom = landmarks[top_idx], landmarks[bottom_idx]
        vertical_distance = get_distance(pt_top, pt_bottom, w, h)

        pt_inner, pt_outer = landmarks[inner_idx], landmarks[outer_idx]
        horizontal_distance = get_distance(pt_inner, pt_outer, w, h)

        if horizontal_distance == 0: return False
        return (vertical_distance / horizontal_distance) > self.eye_opened_coef
        
    def _process_eye(self, frame, image, landmarks, center_idx, border_idx, opp_border_idx, w, h):
        """Processes a single eye for overlay."""
        cx, cy = int(landmarks[center_idx].x * w), int(landmarks[center_idx].y * h)
        p1 = (landmarks[border_idx].x * w, landmarks[border_idx].y * h)
        p2 = (landmarks[opp_border_idx].x * w, landmarks[opp_border_idx].y * h)
        diameter = math.hypot(p1[0] - p2[0], p1[1] - p2[1])
        size = int(diameter * EYE_SCALED_FACTOR)

        if size <= 0: return frame
        resized_eye = cv2.resize(image, (size, size))

        return overlay_image(frame, resized_eye, cx, cy)
        
    def _draw_sharingan(self) -> cv2.Mat:
        """Draws the Sharingan overlay on the eyes."""  
        if self.tomoe_3 is None or self.dojutsu_img is None: return self.args["frame"]  
            
        h, w = self.args["frame"].shape[:2]
        self.face_results = self.args["holistic_results"].face_landmarks

        if not self.face_results: return self.args["frame"]

        landmarks = self.face_results.landmark

        self.is_left_eye_open = self._check_eye_open(landmarks, 159, 145, 33, 133, w, h)
        self.is_right_eye_open = self._check_eye_open(landmarks, 386, 374, 362, 263, w, h)
        
        if self.sharingan_stage == "mangekyou" and self.args["disable_mangekyou"]:
            # src/assets/three_great_dojutsu/sharingan/tomoe_3.png            
            image = self.tomoe_3
        else:
            image = self.dojutsu_img
        
        if self.is_left_eye_open:  self.args["frame"] = self._process_eye(self.args["frame"], image, landmarks, 468, 474, 476, w, h)                
        if self.is_right_eye_open: self.args["frame"] = self._process_eye(self.args["frame"], image, landmarks, 473, 469, 471, w, h)
                
        drain_per_second = SHARINGAN_STAGES.get(self.sharingan_stage, {}).get("chakra_cost", 0) * DROP_CHAKRA_FACTOR
        self.current_chakra = max(0, self.current_chakra - (drain_per_second * self.args["dt"]))    
        return self.args["frame"]
    
    def _draw_mangekyou_techniques_effect(self) -> tuple:
        """Draws the Mangekyou Sharingan techniques based on the owner and technique."""  
        if self.eye_bleeding is None or self.susanoo is None or self.kotoamatsukami is None:
            return self.args["frame"], self.blindness_counter
          
        if "amaterasu" in self.mangekyou_technique and (not self.is_left_eye_open and self.is_right_eye_open) and check_owner(self.mangekyou_owner, "amaterasu"):
            if "amaterasu" not in self.active_effects:
                self.active_effects["amaterasu"] = AmaterasuEffect(eye_bleeding=self.eye_bleeding)
            self.args["frame"], self.blindness_counter = self.active_effects["amaterasu"].apply(self.args["frame"], results=self.face_results)
            drain_per_second = MANGEKYOU_ABILITIES.get("amaterasu", {}).get("chakra_cost", 0) * DROP_CHAKRA_FACTOR
            
        elif "tsukuyomi" in self.mangekyou_technique and (self.is_left_eye_open and not self.is_right_eye_open) and check_owner(self.mangekyou_owner, "tsukuyomi"):
            if "tsukuyomi" not in self.active_effects:
                self.active_effects["tsukuyomi"] = TsukuyomiEffect(eye_bleeding=self.eye_bleeding)
            self.args["frame"], self.blindness_counter = self.active_effects["tsukuyomi"].apply(self.args["frame"], results=self.face_results)
            drain_per_second = MANGEKYOU_ABILITIES.get("tsukuyomi", {}).get("chakra_cost", 0) * DROP_CHAKRA_FACTOR
            
        elif "kamui" in self.mangekyou_technique and (self.is_left_eye_open and not self.is_right_eye_open) and check_owner(self.mangekyou_owner, "kamui"):  
            if "kamui" not in self.active_effects:
                self.active_effects["kamui"] = KamuiEffect(center=self.args["center"], radius=300, strength=5.0)
            if self.args["is_clicked"]:
                self.active_effects["kamui"].center = self.args["center"]
                self.args["frame"] , self.blindness_counter = self.active_effects["kamui"].apply(self.args["frame"])
            drain_per_second = MANGEKYOU_ABILITIES.get("kamui", {}).get("chakra_cost", 0) * DROP_CHAKRA_FACTOR if self.args["is_clicked"] else 0.0

        elif not self.args["disable_susanoo"] and "susanoo" in self.mangekyou_technique and (self.is_left_eye_open and self.is_right_eye_open) and check_owner(self.mangekyou_owner, "susanoo"):             
            if "susanoo" not in self.active_effects:
                self.active_effects["susanoo"] = SusanooEffect(susanoo=self.susanoo, susanoo_scale_factor=SUSANO_SCALED_FACTOR)
            self.args["frame"], self.blindness_counter = self.active_effects["susanoo"].apply(frame=self.args["frame"], face_results=self.face_results, holistic_results=self.args["holistic_results"], mp_holistic=self.args["mp_holistic"]) 
            drain_per_second = MANGEKYOU_ABILITIES.get("susanoo", {}).get("chakra_cost", 0) * DROP_CHAKRA_FACTOR
        
        elif "kotoamatsukami" in self.mangekyou_technique and (not self.is_left_eye_open and self.is_right_eye_open) and check_owner(self.mangekyou_owner, "kotoamatsukami"):  
            if "kotoamatsukami" not in self.active_effects:
                self.active_effects["kotoamatsukami"] = KotoamatsukamiEffect(kotoamatsukami=self.kotoamatsukami)
            self.args["frame"], self.blindness_counter = self.active_effects["kotoamatsukami"].apply(frame=self.args["frame"], x=self.args["x"], y=self.args["y"])
            drain_per_second = MANGEKYOU_ABILITIES.get("kotoamatsukami", {}).get("chakra_cost", 0) * DROP_CHAKRA_FACTOR
        
        elif "ohirume" in self.mangekyou_technique and (self.is_left_eye_open and self.is_right_eye_open) and check_owner(self.mangekyou_owner, "ohirume"):             
            if "ohirume" not in self.active_effects:
                self.active_effects["ohirume"] = OhirumeEffect()
            if self.args["disable_ohirume"]:
                self.active_effects["ohirume"].reset()
            self.active_effects["ohirume"].update(center=self.args["center"], is_active=self.args["is_clicked"])
            self.args["frame"], self.blindness_counter = self.active_effects["ohirume"].apply(frame=self.args["frame"]) 
            drain_per_second = MANGEKYOU_ABILITIES.get("ohirume", {}).get("chakra_cost", 0) * DROP_CHAKRA_FACTOR if self.args["is_clicked"] else 0.0
         
        # I'll pass, you do it, Author: ioscbasotcstw
        elif "kagutsuchi" in self.mangekyou_technique and (not self.is_left_eye_open and self.is_right_eye_open) and check_owner(self.mangekyou_owner, "kagutsuchi"):             
            pass
        else:
            return self.args["frame"], self.blindness_counter
            
        self.current_chakra = max(0, self.current_chakra - (drain_per_second * self.args["dt"]))
        return self.args["frame"], self.blindness_counter
    
    def _draw_rinnegan(self) -> cv2.Mat:
        """Draws the Rinnegan overlay on the eyes."""  
        if self.rinnegan_left is None and self.rinnegan_right is None: return self.args["frame"]  
            
        h, w = self.args["frame"].shape[:2]
        self.face_results = self.args["holistic_results"].face_landmarks

        if not self.face_results: return self.args["frame"]

        landmarks = self.face_results.landmark

        self.is_left_eye_open = self._check_eye_open(landmarks, 159, 145, 33, 133, w, h)
        self.is_right_eye_open = self._check_eye_open(landmarks, 386, 374, 362, 263, w, h)
        
        def _process_eye(img, center_idx, left, right, up, bottom):
            """Processes a single eye for overlay."""
            cx, cy = int(landmarks[center_idx].x * w), int(landmarks[center_idx].y * h)
            eyeL = landmarks[left]
            eyeR = landmarks[right]
            eyeU = landmarks[up]
            eyeB = landmarks[bottom]
            
            measure_width  = int(get_distance(eyeL, eyeR, w, h))
            measure_height = int(get_distance(eyeU, eyeB, w, h))

            if measure_width <= 0 and measure_height <= 0: return frame

            resized_eye = cv2.resize(img, (int(measure_width * 1.1), int(measure_height * 1.1)))

            return overlay_image(self.args["frame"], resized_eye, cx, cy)
        
        if self.is_left_eye_open: frame  = _process_eye(self.rinnegan_left, 468, 33, 133, 159, 145)                
        if self.is_right_eye_open: frame = _process_eye(self.rinnegan_right, 473, 362, 263, 386, 477)
                
        drain_per_second = RINNEGAN.get("chakra_cost", 0) * DROP_CHAKRA_FACTOR
        self.current_chakra = max(0, self.current_chakra - (drain_per_second * self.args["dt"]))    
        return self.args["frame"]
    
    def _draw_six_paths_technique(self) -> tuple:
        """Draws the Six paths technique"""  
        if self.args["spt"] == "chibaku_tensei":
            if "chibaku_tensei" not in self.active_effects:
                self.active_effects["chibaku_tensei"] = ChibakuTenseiEffect(self.args["center"])
            
            if self.radius >= 100: self.radius = random.randint(5, 10)

            if self.args["is_clicked"]:
                self.radius += 1
                self.active_effects["chibaku_tensei"].center = self.args["center"]
                self.active_effects["chibaku_tensei"].update(self.radius)
                self.args["frame"], self.blindness_counter = self.active_effects["chibaku_tensei"].apply(self.args["frame"])
            drain_per_second = SIX_PATHS_TECHNIQUE.get("deva_path", {}).get("chibaku_tensei", {}).get("chakra_cost", 0) * DROP_CHAKRA_FACTOR if self.args["is_clicked"] else 0.0
        else:
            return self.args["frame"], self.blindness_counter
            
        self.current_chakra = max(0, self.current_chakra - (drain_per_second * self.args["dt"]))
        return self.args["frame"], self.blindness_counter
    
    def _draw_byakugan(self) -> cv2.Mat:
        """Draws the Byakugan overlay on the eyes."""  
        if self.byakugan is None: return self.args["frame"]  
            
        h, w = self.args["frame"].shape[:2]
        self.face_results = self.args["holistic_results"].face_landmarks

        if not self.face_results: return self.args["frame"]

        landmarks = self.face_results.landmark # 478

        self.is_left_eye_open  = self._check_eye_open(landmarks, 159, 145, 33, 133, w, h)
        self.is_right_eye_open = self._check_eye_open(landmarks, 386, 374, 362, 263, w, h)
        
        if self.is_left_eye_open:  self.args["frame"] = self._process_eye(self.args["frame"], self.byakugan, landmarks, 468, 474, 476, w, h)                
        if self.is_right_eye_open: self.args["frame"] = self._process_eye(self.args["frame"], self.byakugan, landmarks, 473, 469, 471, w, h)

        for i in range(len(landmarks)):
            if i % 7 == 0 and i not in RIGHT_EYE_LANDMARKS and i not in LEFT_EYE_LANDMARKS:
                self.points.append((int(landmarks[i].x * w), int(landmarks[i].y * h)))
                cv2.circle(self.args["frame"], (int(landmarks[i].x * w), int(landmarks[i].y * h)), 5, (43, 86, 214), -1) 
                cv2.line(self.args["frame"], self.points[-1], self.points[-2], (55, 103, 245), 1)           

        drain_per_second = BYAKUGAN.get("chakra_cost", 0) * DROP_CHAKRA_FACTOR
        self.current_chakra = max(0, self.current_chakra - (drain_per_second * self.args["dt"]))    
        return self.args["frame"]
    
    def _draw_byakugan_technique(self) -> tuple:
        """Draws the Byakugan technique""" 
        if not self.args["disable_byakugan"]: 
            if "byakugan" not in self.active_effects:
                self.active_effects["byakugan"] = ByakuganEffect()
            self.args["frame"], self.blindness_counter = self.active_effects["byakugan"].apply(self.args["frame"])
            drain_per_second = BYAKUGAN.get("chakra_cost", 0) * DROP_CHAKRA_FACTOR
            self.current_chakra = max(0, self.current_chakra - (drain_per_second * self.args["dt"]))
        else:
            return self.args["frame"], self.blindness_counter
        return self.args["frame"], self.blindness_counter
    
    def draw_dojutsu_effect(self) -> tuple:
        """Call stack to draw dojutsu effects in sequence."""
        try:
            if self.args["blindness_stage"] == "heavy":
                return self.args["frame"], self.blindness_counter, self.current_chakra
            
            if self.dojutsu_img is not None:
                self.args["frame"] = self._draw_sharingan()

            if self.rinnegan_left is not None and self.rinnegan_right is not None:
                self.args["frame"] = self._draw_rinnegan()

            if getattr(self, "mangekyou_technique", None) and not self.args["disable_mangekyou"]:
                self.args["frame"], self.blindness_counter = self._draw_mangekyou_techniques_effect()
            
            if self.args["spt"] is not None:
                self.args["frame"], self.blindness_counter = self._draw_six_paths_technique()

            if self.byakugan is not None:
                self.args["frame"] = self._draw_byakugan()
                self.args["frame"], self.blindness_counter = self._draw_byakugan_technique()

            return self.args["frame"], self.blindness_counter, self.current_chakra
        except Exception as e:
            print(f"Error in dojutsu factory: {e}") 
        finally:
            return self.args["frame"], self.blindness_counter, self.current_chakra