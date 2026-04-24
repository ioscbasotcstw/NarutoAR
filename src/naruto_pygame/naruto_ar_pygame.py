# NarutoAR: An Augmented Reality Experience Inspired by Naruto and tysuprawee

"""
   #                                                          
  # #   #    #   ##   ##### ###### #####    ##    ####  #    #
 #   #  ##  ##  #  #    #   #      #    #  #  #  #      #    #
#     # # ## # #    #   #   #####  #    # #    #  ####  #    #
####### #    # ######   #   #      #####  ######      # #    #
#     # #    # #    #   #   #      #   #  #    # #    # #    #
#     # #    # #    #   #   ###### #    # #    #  ####   #### 
"""

import math
import os
import time
import pygame
from pygame.locals import *
import cv2
import mediapipe as mp
import numpy as np

from constants import (
    SHARINGAN_PATH,
    YOLO_MODEL_PATH,
    JUTSU_CATALOG,
    SHARINGAN_STAGES,
    MANGEKYOU_USERS,
    SIGNS_MAPPING,
    CORRESPONDING_VISUAL_TO_SIGNS,
    STYLES,
    APP_NAME,
    MANGEKYOU_PATH,
    EYE_OPENED_COEFFICIENT,
    LIGHT_BLINDNESS,
    MEDIUM_BLINDNESS,
    HEAVY_BLINDNESS,
    MANGEKYOU_ABILITIES,
    RINNEGAN,
    BYAKUGAN,
)
from utils import (
    apply_blindness_effect,
    print_session_results, 
    save_player_data, 
    create_water_maps, 
    setup_player, 
    check_game_over, 
    process_techniques, 
    pygame_input_screen
)
from src.chakra.factories.jutsu_factory import JutsuFactory
from src.chakra.factories.dojutsu_factory import DojutsuFactory
from .styles.styles_factory import StyleFactory
from .ui.toggle import Toggle
from .backgound import Backgrounds
from ultralytics import YOLO
from typing import List

class NarutoAR:
    def __init__(self):
        print("Loading models...")
        # Initialize Models
        self.yolo = YOLO(YOLO_MODEL_PATH, task="detect", verbose=False)
        self.mp_holistic = mp.solutions.holistic
        self.holistic_results = self.mp_holistic.Holistic(
            static_image_mode=False,
            model_complexity=1, # 0=fast, 1=balanced, 2=accurate
            refine_face_landmarks=True,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )
        self.segmenter = mp.solutions.selfie_segmentation.SelfieSegmentation(model_selection=1)
        print("Complete loading models...")
        # State Variables 
        self.history: List[str]  = []
        self.target_sequence     = []
        self.max_history         = 15
        self.is_broken_sequence  = False
        self.jutsu_active        = False
        self.is_jutsu_performed  = False
        # Debouncing
        self.current_sign_count  = 0
        self.last_raw_sign       = None
        self.stability_threshold = 1
        # Boolean
        self.is_hand_jutsu         = False
        self.has_image             = False
        self.is_sequantial         = True
        self.is_left_eye_open      = False
        self.is_right_eye_open     = False
        # Strings
        self.jutsu_name            = None
        self.cached_jutsu_effect   = None
        self.jutsu_path            = None
        self.dojutsu_img           = None
        self.mangekyou_owner       = None
        self.mangekyou_technique   = None
        self.rinnegan_left         = None
        self.rinnegan_right        = None
        self.byakugan              = None
        self.sharingan_stage       = None
        self.blindness_stage       = None 
        # Integers/floats
        self.current_chakra        = 0.0
        self.blindness_accumulator = 0.0
        self.chakra_reset          = 0
        self.base_chakra_level     = 0
        self.blindness_counter     = 0
        # Time
        self.last_time = time.time()
        # Camera
        self.cap = cv2.VideoCapture(1)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        self.width = self.cap.get(cv2.CAP_PROP_FRAME_WIDTH)
        self.height = self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT)

        if self.width == 0 and self.height == 0: raise ValueError("Camera not found or cannot be accessed.")
        
        # Other
        self.prison_radius = self.width // 3 if self.width > self.height else self.height // 3
        self.center_point  = [self.width // 2, self.height // 2]
        self.is_clicked    = False
        self.bg_resized    = False

        pygame.init()
        pygame.display.set_caption(APP_NAME)
        self.screen = pygame.display.set_mode([1280,720])

    def update(self, current_chakra, chakra_reset, base_chakra_level, blindness_accumulator) -> None:
        """Updates the player's chakra and blindness state from loaded data."""
        self.current_chakra = current_chakra
        self.chakra_reset = chakra_reset
        self.base_chakra_level = base_chakra_level
        self.blindness_accumulator = blindness_accumulator

    def load_technique(self, user_input: str) -> None:
        """Parses user input and loads corresponding images and sequences."""
        inputs = [x.strip() for x in user_input.split(',')]
        # ['sharingan mangekyou itachi amaterasu tsukuyomi susanoo kamui']
        # ['sharingan mangekyou itachi amaterasu tsukuyomi susanoo kamui', 'chidori']
        print(f"User input parsed as: {inputs}")
        # Reset
        self.target_sequence = []
        self.jutsu_path = None
        self.dojutsu_img = None
        self.rinnegan_left = None
        self.rinnegan_right = None
        self.byakugan = None
        found_something = False

        # sharingan mangekyou sarada amaterasu tsukuyomi susanoo kotoamatsukami kamui ohirume
        # chidori

        # rinnegan | byakugan
        # chidori
        for item in inputs:
            # Check Jutsu
            if item in JUTSU_CATALOG:
                data = JUTSU_CATALOG[item]
                self.jutsu_name = item
                self.target_sequence = data.get("sequence", None)
                self.jutsu_path = data.get("image", None)
                self.is_hand_jutsu = data.get("is_hand_jutsu", False)
                self.has_image = self.jutsu_path is not None
                self.is_sequantial = self.target_sequence is not None
                found_something = True
                self.is_jutsu_performed = True
            # Check Dojutsu
            # sharingan (tomoe_1 | tomoe_2 | tomoe_3 | mangekyou) (amaterasu | tsukuyomi |susanoo)
            elif item.startswith("sharingan"):
                # ['sharingan', 'mangekyou', 'itachi', 'amaterasu', 'tsukuyomi', 'susanoo', 'kamui']
                parts = item.split(' ')
                # tomoe_1 | tomoe_2 | tomoe_3 | mangekyou
                stage = parts[1] if len(parts) > 1 else None 
                
                if stage in SHARINGAN_STAGES:
                    stage_data = SHARINGAN_STAGES[stage]
                    # itachi | obito | sasuke | madara | shisui
                    owner = parts[2].strip()
                    if not owner in MANGEKYOU_USERS:
                        raise ValueError(f"Not such a mangekyou owner like {owner}")
                    
                    image_path = os.path.join(MANGEKYOU_PATH, f"{owner}.png")
                    if not os.path.exists(image_path):
                        raise ValueError(f"Not such a file like {image_path}")

                    # (tomoe_1 | tomoe_2 | tomoe_3).png | (itachi | obito | sasuke | madara | shisui | indra).png
                    img_path = stage_data["image"] if stage != "mangekyou" else image_path
                    self.sharingan_stage = stage

                    self.dojutsu_img  = self._load_image(img_path)
                    
                    if stage == "mangekyou":
                        self.mangekyou_owner = owner
                        # ['amaterasu', 'tsukuyomi', 'susanoo', 'kamui']
                        self.mangekyou_technique = parts[3:] 
                        
                found_something = True
            # rinnengan
            elif item == "rinnegan":
                rinnegan_left_eye_path  = RINNEGAN.get("rinnegan_left", None)
                rinnegan_right_eye_path = RINNEGAN.get("rinnegan_right", None)

                self.rinnegan_left  = self._load_image(rinnegan_left_eye_path)
                self.rinnegan_right = self._load_image(rinnegan_right_eye_path)

                found_something = True
            # byakugan
            elif item == "byakugan":
                byakugan_path = BYAKUGAN.get("byakugan", None)
                self.byakugan = self._load_image(byakugan_path)
                found_something = True

        # Fallback
        if not found_something:
            self.jutsu_name = "rasengan"
            data = JUTSU_CATALOG["rasengan"]
            self.jutsu_path = data.get("image")
            self.target_sequence = data.get("sequence")
            self.is_hand_jutsu = data.get("is_hand_jutsu", False)
            self.has_image = self.jutsu_path is not None
            self.is_sequantial = self.target_sequence is not None
            self.is_jutsu_performed = True

    def update_signs(self, frame) -> None:
        """Detects hand signs and updates the history buffer."""
        if self.jutsu_active:
            return
        if self.is_jutsu_performed == False:
            return
        
        results = self.yolo(frame, imgsz=640, stream=False, verbose=False)
        detected_name = None
        best_conf = 0
        result = results[0] if len(results) > 0 else None

        if result is not None:
            for box in result.boxes:
                conf = float(box.conf[0])
                if conf > best_conf:
                    best_conf = conf
                    cls_id = int(box.cls[0])
                    raw_label = result.names[cls_id]
                    detected_name = SIGNS_MAPPING.get(raw_label, raw_label)

        # Debouncing Logic 
        if detected_name:
            print(f"Detected sign: {detected_name}")

            if detected_name == self.last_raw_sign:
                self.current_sign_count += 1
            else:
                self.current_sign_count = 0
                self.last_raw_sign = detected_name

            if self.current_sign_count == self.stability_threshold:
                # Add to history if it's different from the immediate last one
                if not self.history or self.history[-1] != detected_name:
                    expected_index = len(self.history)
                    if self.target_sequence and expected_index < len(self.target_sequence) and detected_name == self.target_sequence[expected_index]:
                        self.history.append(detected_name)
                        self.is_broken_sequence = False
                        print(f"Correct sign! History: {self.history}")
                    else:
                        if len(self.history) > 0:
                            print(f"Wrong sign detected: {detected_name}. Restarting sequence.")
                            self.is_broken_sequence = True

                        self.history = []

                        if self.target_sequence and detected_name == self.target_sequence[0]:
                            self.history.append(detected_name)
                            self.is_broken_sequence = False
                            print(f"First sign is correct after error! History: {self.history}")
                    self._check_activation()

    def _check_activation(self) -> None:
        """Checks if the recent history matches the target sequence."""
        if not self.target_sequence:
            return

        seq_len = len(self.target_sequence)
        if len(self.history) >= seq_len:
            if self.history[-seq_len:] == self.target_sequence:
                self.jutsu_active = True
                self.history = [] # Clear history

    def run(self) -> None:
        """Main entrypoint for the AR session."""
        try:
            self._print_controls()
            self._init_assets_and_factories()
            self._init_ui_elements()
            
            while True: 
                if not self._main_loop_step(): break
                    
        except Exception as e: print(f"Error in main: {e}")
        finally: self._cleanup()

    def _print_controls(self):
        print("Controls:")
        print(" - Click on the video: Activate/Move Kamui center")
        print(" - Click again: Deactivate")
        print("Starting AR... Press 'q' to quit, 'r' to reset.")
        print("Press TAB to choose style and press TAB again to choose Six Paths Technique.")

    def _load_image(self, path: str):
        """Helper to safely load and convert images with transparency support."""
        if not os.path.exists(path):
            raise FileNotFoundError(f"Image file '{path}' not found.")
        
        img = cv2.imread(path, cv2.IMREAD_UNCHANGED)
        if len(img.shape) == 3 and img.shape[2] == 4:
            return cv2.cvtColor(img, cv2.COLOR_BGRA2RGBA)
        return cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

    def _init_assets_and_factories(self):
        precomputed_data = create_water_maps(self.prison_radius)
        bg_image = cv2.imread(self.jutsu_path)
        
        tomoe_3 = eye_bleeding = susanoo = kotoamatsukami = None

        if self.sharingan_stage is not None:
            tomoe_3 = self._load_image(os.path.join(SHARINGAN_PATH, "tomoe_3.png"))
            eye_bleeding = self._load_image(os.path.join(MANGEKYOU_PATH, "blood_bleed_from_eye.png"))
            susanoo = self._load_image(os.path.join(MANGEKYOU_PATH, "techniques/susanoo.png"))
            kotoamatsukami = self._load_image(os.path.join(MANGEKYOU_PATH, "feather.png"))

        self.jutsu_factory = JutsuFactory(
            cached_jutsu_effect=self.cached_jutsu_effect,
            jutsu_path=self.jutsu_path,
            jutsu_name=self.jutsu_name,
            bg_image=bg_image,
            bg_resized=self.bg_resized,
            radius=self.prison_radius,
            precomputed_data=precomputed_data,
            is_sequantial=self.is_sequantial,
            has_image=self.has_image,
            is_hand_jutsu=self.is_hand_jutsu,
            current_chakra=self.current_chakra,
            scale_factor_for_image_jutsu=3.5,
        )

        self.dojutsu_factory = DojutsuFactory(
            eye_opened_coef=EYE_OPENED_COEFFICIENT,
            dojutsu_img=self.dojutsu_img,
            eye_bleeding=eye_bleeding,
            susanoo=susanoo,
            kotoamatsukami=kotoamatsukami,
            tomoe_3=tomoe_3,
            rinnegan_left=self.rinnegan_left,
            rinnegan_right=self.rinnegan_right,
            byakugan=self.byakugan,
            sharingan_stage=self.sharingan_stage,
            mangekyou_technique=self.mangekyou_technique,
            mangekyou_owner=self.mangekyou_owner,
            current_chakra=self.current_chakra,
        )

        self.bg = Backgrounds(bg_resized=self.bg_resized)
        self.style_factory = StyleFactory()

    def _init_ui_elements(self):
        """Bundles dictionaries tracking UI configuration, animation states, and text boxes."""
        base_x = int(self.width)
        self.toggles = {
            'bg': Toggle(base_x + 250, 300, 60, 30, starting_state=True),
            'ohirume': Toggle(base_x + 250, 350, 60, 30, starting_state=True),
            'byakugan': Toggle(base_x + 250, 350, 60, 30, starting_state=True),
            'susanoo': Toggle(base_x + 20, 300, 60, 30, starting_state=True),
            'mangekyou': Toggle(base_x + 20, 350, 60, 30, starting_state=True),
            'sharingan': Toggle(base_x + 20, 400, 60, 30, starting_state=True),
        }
        
        if self.sharingan_stage is not None:
            self.toggles['jutsu'] = Toggle(base_x + 20, 450, 60, 30, starting_state=True)
        else:
            self.toggles['jutsu'] = Toggle(base_x + 20, 300, 60, 30, starting_state=True)

        self.ui_state = {
            'input_text': "",
            'picked_styles':[],
            'picked_style': None,
            'active_box': None,
            'spt_input_text': "",
            'six_paths_technique': None,
        }

        self.anim_vars = {
            'i': 0,
            'amplitude': 50,
            'frequency': 0.05,
            'speed': 2,
            'center_x': self.width // 2,
            'x': 0.0,
            'y': self.height // 4
        }

        self.cached_target_seq = {}
        self.new_image_size = (100, 100)

        self.fonts = {
            'title': pygame.font.SysFont("Arial", 14, bold=True),
            'sub': pygame.font.SysFont("Arial", 14),
            'input': pygame.font.SysFont("Arial", 14),
            'toggle': pygame.font.SysFont("Arial", 16, bold=True),
            'chakra': pygame.font.SysFont("Arial", 28, bold=True)
        }

    def _main_loop_step(self) -> bool:
        success, frame = self.cap.read()
        if not success: 
            return False

        self.screen.fill([0, 0, 0])

        current_time = time.time()
        dt = current_time - getattr(self, 'last_time', current_time)
        self.last_time = current_time

        frame = cv2.flip(frame, 1)
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        holistic_results = self.holistic_results.process(frame)
        
        # Only process segmenter if Jutsu is active or background is ON
        segmenter_results = None
        if self.is_jutsu_performed or self.toggles['bg'].state:
            segmenter_results = self.segmenter.process(frame)

        self.update_signs(frame)
        self._update_blindness(dt)

        if self.current_chakra >= 10:
            frame = apply_blindness_effect(frame=frame, stage=self.blindness_stage)
                   
            if self.ui_state['picked_style']:
                frame = self.style_factory.create_style(
                    frame=frame, 
                    style_name=self.ui_state['picked_styles'], 
                    holistic_results=holistic_results
                )

            if self.toggles['bg'].state:
                frame = self.bg.apply(frame=frame, segmenter_results=segmenter_results)

            if self.toggles['jutsu'].state:
                self.jutsu_factory.current_chakra = self.current_chakra
                self.jutsu_factory.update(
                    frame=frame, 
                    dt=dt, 
                    blindness_stage=self.blindness_stage, 
                    jutsu_active=self.jutsu_active, 
                    disable_bg=not self.toggles['bg'].state,
                    holistic_results=holistic_results, 
                    segmenter_results=segmenter_results, 
                    mp_holistic=self.mp_holistic,
                )
                frame, self.current_chakra = self.jutsu_factory.draw_jutsu_effect()
            
            if self.toggles['sharingan'].state:
                self.dojutsu_factory.current_chakra = self.current_chakra
                self.dojutsu_factory.update(
                    frame=frame, 
                    dt=dt, 
                    x=self.anim_vars['x'], 
                    y=self.anim_vars['y'], 
                    blindness_stage=self.blindness_stage, 
                    center=self.center_point, 
                    is_clicked=self.is_clicked, 
                    disable_ohirume=not self.toggles['ohirume'].state,
                    disable_susanoo=not self.toggles['susanoo'].state,
                    disable_mangekyou=not self.toggles['mangekyou'].state,
                    disable_byakugan=not self.toggles['byakugan'].state,
                    spt=self.ui_state['six_paths_technique'],
                    holistic_results=holistic_results, 
                    mp_holistic=self.mp_holistic,
                )

                frame, self.blindness_counter, self.current_chakra = self.dojutsu_factory.draw_dojutsu_effect()

        # Convert array dimensions for Pygame
        frame = np.swapaxes(frame, 0, 1)
        frame = pygame.surfarray.make_surface(frame) 

        # Animation Math Updates(For Kotoamatsukami)
        self.anim_vars['x'] = self.anim_vars['center_x'] + (self.anim_vars['amplitude'] * math.sin(self.anim_vars['frequency'] * self.anim_vars['i']))
        self.anim_vars['y'] += self.anim_vars['speed']
        if self.anim_vars['y'] >= self.height - 200:
            self.anim_vars['y'] = 20
        self.anim_vars['i'] += 1
        
        if not self._check_chakra_depletion():
            return False

        self.screen.blit(frame, (0, 0))
        self._render_ui()
        pygame.display.update()

        return self._handle_events()

    def _update_blindness(self, dt):
        self.blindness_accumulator += self.blindness_counter * dt
        if LIGHT_BLINDNESS <= self.blindness_accumulator < MEDIUM_BLINDNESS:
            self.blindness_stage = "light"
        elif MEDIUM_BLINDNESS <= self.blindness_accumulator < HEAVY_BLINDNESS:
            self.blindness_stage = "medium"
        elif self.blindness_accumulator >= HEAVY_BLINDNESS:
            self.blindness_stage = "heavy"
        else:                    
            self.blindness_stage = None

    def _check_chakra_depletion(self) -> bool:
        if self.current_chakra <= 0:
            self.jutsu_active = False
            self.is_jutsu_performed = False
            self.cached_jutsu_effect = None
            self.history =[]
            
            if getattr(self, 'chakra_reset', 0) <= 0:
                print("Game Over! No resets left.")
                self.current_chakra = 0
                self.chakra_reset = 0
                return False
                
            self.chakra_reset -= 1
            self.current_chakra = self.base_chakra_level
            print(f"Chakra depleted! Resetting... Remaining resets: {self.chakra_reset}")
        return True

    def _render_ui(self):
        ui_x = int(self.width) + 20 
        ui_y = 50
        bar_width, bar_height = 300, 25

        # Render Chakra Bar
        chakra_percent = (self.current_chakra / self.base_chakra_level) if getattr(self, 'base_chakra_level', 0) > 0 else 0
        fill_width = max(0, min(int(chakra_percent * bar_width), bar_width))

        text_str = f"Chakra: {(chakra_percent * 100):.2f}% | Reset: {self.chakra_reset}"
        self.screen.blit(self.fonts['chakra'].render(text_str, True, (255, 255, 255)), (ui_x, ui_y - 35))

        pygame.draw.rect(self.screen, (255, 255, 255), (ui_x, ui_y, bar_width, bar_height))
        if fill_width > 0:
            pygame.draw.rect(self.screen, (255, 0, 0), (ui_x, ui_y, fill_width, bar_height))

        self._render_target_sequence()
        self._render_styles_ui(ui_x)
        self._render_toggles(ui_x)

    def _render_target_sequence(self):
        if self.cached_target_seq.get("sequence_name") != self.target_sequence:
            self.cached_target_seq["sequence_name"] = list(self.target_sequence)
            self.cached_target_seq["target"] =[]

            for target in self.target_sequence:
                img_path = CORRESPONDING_VISUAL_TO_SIGNS.get(target, None)
                if img_path and os.path.exists(img_path):
                    image = pygame.image.load(img_path)
                    image = pygame.transform.scale(image, self.new_image_size)
                    self.cached_target_seq["target"].append(image)
                else:
                    surf = pygame.Surface(self.new_image_size)
                    surf.fill((100, 100, 100))
                    self.cached_target_seq["target"].append(surf)

        matched_count = len(self.history)
        current_x_padding = 5
        image_y = self.height + 100
        
        for i, target_img in enumerate(self.cached_target_seq.get("target",[])):
            image_to_tint = target_img.copy()

            if i < matched_count:
                image_to_tint.fill((0, 80, 0), special_flags=pygame.BLEND_RGB_ADD)
            elif i == matched_count and len(self.history) > 0:
                image_to_tint.fill((120, 0, 0), special_flags=pygame.BLEND_RGB_ADD)

            if self.is_broken_sequence:
                self.screen.blit(target_img, (current_x_padding, image_y))
            else:
                self.screen.blit(image_to_tint, (current_x_padding, image_y))

            current_x_padding += self.new_image_size[0] + 10

    def _render_styles_ui(self, ui_x):
        self.screen.blit(self.fonts['title'].render("Enter your desire style.", True, (255, 255, 255)), (ui_x, 150))
        self.screen.blit(self.fonts['sub'].render(f"Available styles: {', '.join(STYLES)}", True, (180, 180, 180)), (ui_x, 180))

        input_box_rect = pygame.Rect(ui_x, 210, 300, 40)
        pygame.draw.rect(self.screen, (255, 255, 255), input_box_rect, 2)
        
        cursor = "|" if time.time() % 1 > 0.5 else ""
        txt_surf = self.fonts['input'].render(self.ui_state['input_text'] + cursor, True, (100, 255, 100))
        self.screen.blit(txt_surf, (input_box_rect.x + 10, input_box_rect.y + 5))
        
        if self.ui_state['picked_style']:
            ps = self.ui_state['picked_styles']
            active_str = f"Active: {ps[0] if len(ps) == 1 else ', '.join(ps)}"
            self.screen.blit(self.fonts['sub'].render(active_str, True, (255, 200, 0)), (ui_x, 260))

        if self.rinnegan_left is not None:
            self.screen.blit(self.fonts['title'].render("Enter desire technique: ", True, (255, 255, 255)), (ui_x, 355))
            self.screen.blit(self.fonts['sub'].render("Available six paths technique: chibaku tensei", True, (180, 180, 180)), (ui_x, 385))

            spt_input_box_rect = pygame.Rect(ui_x, 405, 300, 40)
            pygame.draw.rect(self.screen, (255, 255, 255), spt_input_box_rect, 2)
            
            spt_txt_surf = self.fonts['input'].render(self.ui_state['spt_input_text'] + cursor, True, (100, 255, 100))
            self.screen.blit(spt_txt_surf, (spt_input_box_rect.x + 10, spt_input_box_rect.y + 5))

    def _render_toggles(self, ui_x):
        self.toggles['bg'].draw(self.screen)
        self.screen.blit(self.fonts['toggle'].render(f"Background: {'ON' if self.toggles['bg'].state else 'OFF'}", True, (255, 255, 255)), (ui_x + 300, 305))

        if self.sharingan_stage is not None:
            self.toggles['susanoo'].draw(self.screen)
            self.toggles['mangekyou'].draw(self.screen)
            self.toggles['sharingan'].draw(self.screen)
            self.toggles['ohirume'].draw(self.screen)
            
            self.screen.blit(self.fonts['toggle'].render(f"Susanoo: {'ON' if self.toggles['susanoo'].state else 'OFF'}", True, (255, 255, 255)), (ui_x + 75, 305))
            self.screen.blit(self.fonts['toggle'].render(f"Mangekyou: {'ON' if self.toggles['mangekyou'].state else 'OFF'}", True, (255, 255, 255)), (ui_x + 75, 355))
            self.screen.blit(self.fonts['toggle'].render(f"Sharingan: {'ON' if self.toggles['sharingan'].state else 'OFF'}", True, (255, 255, 255)), (ui_x + 75, 405))
            self.screen.blit(self.fonts['toggle'].render(f"Ohirume: {'ON' if self.toggles['ohirume'].state else 'OFF'}", True, (255, 255, 255)), (ui_x + 300, 355))

        if getattr(self, 'jutsu_active', False):
            self.toggles['jutsu'].draw(self.screen)
            jut_label = self.fonts['toggle'].render(f"Jutsu: {'ON' if self.toggles['jutsu'].state else 'OFF'}", True, (255, 255, 255))
            y_offset = 455 if self.sharingan_stage is not None else 305
            self.screen.blit(jut_label, (ui_x + 75, y_offset))

        if self.byakugan is not None:
            self.toggles['byakugan'].draw(self.screen)
            self.screen.blit(self.fonts['toggle'].render(f"Byakugan: {'ON' if self.toggles['byakugan'].state else 'OFF'}", True, (255, 255, 255)), (ui_x + 300, 355))

    def _handle_events(self) -> bool:
        """Returns False if it is time to shut down/quit the main loop."""
        for event in pygame.event.get():
            if event.type == QUIT:
                return False
            
            elif event.type == KEYDOWN:
                if event.key == K_TAB:
                    self.ui_state['active_box'] = "spt" if self.ui_state['active_box'] == "style" else "style"
                    continue 

                if self.ui_state['active_box'] == "style":
                    self._handle_style_input(event)
                elif self.ui_state['active_box'] == "spt":
                    self._handle_spt_input(event)
                else:
                    if event.key == K_q:
                        return False
                    elif event.key == K_r:
                        self.jutsu_active = False
                        self.cached_jutsu_effect = None
                        self.history =[]
                        self.cached_target_seq.clear()
                        print("Reset sequence.")
                        
            elif event.type == MOUSEBUTTONDOWN and event.button == 1:
                for name, toggle in self.toggles.items():
                    if name == 'jutsu' and not getattr(self, 'jutsu_active', False): continue         
                    if name in ['susanoo', 'mangekyou', 'sharingan', 'ohirume'] and self.sharingan_stage is None: continue 
                    if name == 'byakugan' and self.byakugan is None: continue
                    toggle.handle_event(event)

                x_mouse, y_mouse = event.pos  
                if x_mouse <= self.width and y_mouse <= self.height:
                    self.is_clicked = not self.is_clicked
                    self.center_point = [x_mouse, y_mouse]
        return True

    def _handle_style_input(self, event):
        if event.key == K_RETURN:
            raw_input = self.ui_state['input_text'].strip().lower()
            parts =[p.strip().replace(" ", "_") for p in raw_input.split(',')]
            
            if len(parts) > 1:
                style_1, style_2 = parts[0], parts[1]
                if style_1 in STYLES and style_2 in STYLES:
                    self.ui_state['picked_styles'] = [style_1, style_2]
                    self.ui_state['picked_style'] = f"{style_1}, {style_2}"
                else:
                    self.ui_state['picked_styles'] = [STYLES[0]]
                    self.ui_state['picked_style'] = STYLES[0]
            elif parts and parts[0]:
                single_style = parts[0]
                if single_style in STYLES:
                    self.ui_state['picked_styles'] = [single_style]
                    self.ui_state['picked_style'] = single_style
                else:
                    self.ui_state['picked_styles'] = [STYLES[0]]
                    self.ui_state['picked_style'] = STYLES[0]
                    
            self.ui_state['input_text'] = "" 
            self.ui_state['active_box'] = None
            print(f"Style changed to: {self.ui_state['picked_style']}")
            
        elif event.key == K_BACKSPACE:
            self.ui_state['input_text'] = self.ui_state['input_text'][:-1]
            
        elif event.unicode.isprintable():
            self.ui_state['input_text'] += event.unicode

    def _handle_spt_input(self, event):
        if event.key == K_RETURN:
            raw_spt_input = self.ui_state['spt_input_text'].strip().lower()
            self.ui_state['six_paths_technique'] = raw_spt_input.replace(" ", "_")
            self.ui_state['spt_input_text'] = ""
            self.ui_state['active_box'] = None
            
        elif event.key == K_BACKSPACE:
            self.ui_state['spt_input_text'] = self.ui_state['spt_input_text'][:-1]
            
        elif event.unicode.isprintable():
            self.ui_state['spt_input_text'] += event.unicode

    def _cleanup(self):
        """Teardown windows and cap instances elegantly"""
        pygame.quit()
        if hasattr(self, 'cap') and self.cap is not None:
            self.cap.release()
        cv2.destroyAllWindows()

def main():
    app = NarutoAR()
    current_user = pygame_input_screen(app.screen, "Enter your username:").strip()

    player_data = setup_player(current_user, app=app)
    check_game_over(player_data)
    
    app.update(
        current_chakra=player_data.get("chakra", 0.0),
        chakra_reset=player_data.get("resets", 0),
        base_chakra_level=player_data.get("base_chakra_level", 100.0), 
        blindness_accumulator=player_data.get("blindness_counter", 0.0)
    )
    
    available = list(JUTSU_CATALOG.keys()) + list(MANGEKYOU_ABILITIES.keys())
    sub_text = f"Available: {', '.join(available)}"
    choice = pygame_input_screen(app.screen, "Choose technique (e.g., chidori, sharingan | rinnegan | byakugan):", sub_text).lower()
    
    choices_list =[c.strip() for c in choice.split(",")]
    final_load_string = process_techniques(current_user, player_data, choices_list, app=app)
    print(f"Loading techniques: {final_load_string}")
    app.load_technique(final_load_string)
    
    try:
        app.run()
    finally:
        save_player_data(
            current_user, 
            chakra=app.current_chakra, 
            resets=app.chakra_reset, 
            base_chakra_level=app.base_chakra_level, 
            blindness=app.blindness_stage, 
            blindness_counter=app.blindness_accumulator
        )

        print_session_results(app)

if __name__ == "__main__":
    main()