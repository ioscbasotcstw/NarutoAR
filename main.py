# NarutoAR: An Augmented Reality Experience Inspired by Naruto and tysuprawee

"""
  ____              __    __           __                                  
/\  _`\           /\ \__/\ \__       /\ \                                 
\ \ \/\ \     __  \ \ ,_\ \ ,_\    __\ \ \____     __     __  __    ___   
 \ \ \ \ \  /'__`\ \ \ \/\ \ \/  /'__`\ \ '__`\  /'__`\  /\ \/\ \  / __`\ 
  \ \ \_\ \/\ \L\.\_\ \ \_\ \ \_/\  __/\ \ \L\ \/\ \L\.\_\ \ \_\ \/\ \L\ \
   \ \____/\ \__/.\_\\ \__\\ \__\ \____\\ \_,__/\ \__/.\_\\/`____ \ \____/
    \/___/  \/__/\/_/ \/__/ \/__/\/____/ \/___/  \/__/\/_/ `/___/> \/___/ 
                                                              /\___/      
                                                              \/__/                                                                                                                  
"""
import os
import time
import math
import cv2
import mediapipe as mp
from constants import (
    YOLO_MODEL_PATH,
    JUTSU_CATALOG,
    SHARINGAN_STAGES,
    MANGEKYOU_USERS,
    SIGNS_MAPPING,
    APP_NAME,
    MANGEKYOU_PATH,
    EYE_OPENED_COEFFICIENT,
    LIGHT_BLINDNESS,
    MEDIUM_BLINDNESS,
    HEAVY_BLINDNESS,
    MANGEKYOU_ABILITIES,
    MINIMUM_CHAKRA_LEVEL,

)
from utils import (
    chakra_level, 
    apply_blindness_effect, 
    save_player_data, 
    create_water_maps, 
    setup_player, 
    check_game_over, 
    process_techniques, 
    print_session_results
)
from src.chakra.factories.jutsu_factory import JutsuFactory
from src.chakra.factories.dojutsu_factory import DojutsuFactory
from ultralytics import YOLO
from typing import List

class NarutoAR:
    def __init__(self):
        # Initialize Models
        print("Loading models...")
        self.yolo = YOLO(YOLO_MODEL_PATH, task="detect", verbose=False)
        
        # Mediapipe Need use Holistic
        self.mp_holistic = mp.solutions.holistic
        self.holistic_results = self.mp_holistic.Holistic(
            static_image_mode=False,
            model_complexity=1, # 0=fast, 1=balanced, 2=accurate
            refine_face_landmarks=True,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )
        self.segmenter = mp.solutions.selfie_segmentation.SelfieSegmentation(model_selection=1)

        # State Variables
        self.history: List[str] = []
        self.target_sequence    = []
        self.max_history        = 15
        self.jutsu_active       = False
        self.is_jutsu_performed = False
        
        # Debouncing
        self.current_sign_count  = 0
        self.last_raw_sign       = None
        self.stability_threshold = 5

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
        self.sharingan_stage       = None
        self.blindness_stage       = None 
        # Integers/floats
        self.current_chakra        = 0.0
        self.chakra_reset          = 0
        self.base_chakra_level     = 0
        self.blindness_counter     = 0
        self.blindness_accumulator = 0.0
        # Time
        self.last_time = time.time()
        
        # Camera
        self.cap = cv2.VideoCapture(0)
        # Other
        self.bg_resized   = False
        self.center_point = [320, 240]
        self.kamui_active = False

        self.width = self.cap.get(cv2.CAP_PROP_FRAME_WIDTH)
        self.height = self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
        self.prison_radius = self.width // 3 if self.width > self.height else self.height // 3

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
        print(f"User input parsed as: {inputs}")
        # Reset
        self.target_sequence = []
        self.jutsu_path = None
        self.dojutsu_img = None
        found_something = False

        for item in inputs:
            # Check Jutsu
            if item in JUTSU_CATALOG:
                data = JUTSU_CATALOG[item]
                self.jutsu_name = item
                self.target_sequence = data.get("sequence")
                self.jutsu_path = data.get("image")
                self.is_hand_jutsu = data.get("is_hand_jutsu", False)
                self.has_image = self.jutsu_path is not None
                self.is_sequantial = self.target_sequence is not None
                found_something = True
                self.is_jutsu_performed = True
            # Check Dojutsu
            # (sharingan | byakugan | rinnengan) (tomoe_1 | tomoe_2 | tomoe_3 | mangekyou) (amaterasu | tsukuyomi |susanoo)
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
                    self.dojutsu_img = cv2.imread(img_path, cv2.IMREAD_UNCHANGED)
                    
                    if stage == "mangekyou":
                        self.mangekyou_owner = owner
                        # ['amaterasu', 'tsukuyomi', 'susanoo', 'kamui']
                        self.mangekyou_technique = parts[3:] 
                        
                found_something = True
        # Fallback
        if not found_something:
            self.jutsu_name = "rasengan"
            print(f"Technique not found, defaulting to '{self.jutsu_name}'")
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
        
        results = self.yolo(frame, imgsz=640, stream=True, verbose=False)
        detected_name = None
        best_conf = 0

        for result in results:
            for box in result.boxes:
                conf = float(box.conf[0])
                if conf > best_conf:
                    best_conf = conf
                    cls_id = int(box.cls[0])
                    raw_label = result.names[cls_id]
                    detected_name = SIGNS_MAPPING.get(raw_label, raw_label)

        # Debouncing Logic 
        if detected_name:
            cv2.putText(frame, f"Detecting: {detected_name}", (10, 80), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (184, 15, 32), 2)

            if detected_name == self.last_raw_sign:
                self.current_sign_count += 1
            else:
                self.current_sign_count = 0
                self.last_raw_sign = detected_name

            if self.current_sign_count == self.stability_threshold:
                # Add to history if it's different from the immediate last one
                if not self.history or self.history[-1] != detected_name:
                    self.history.append(detected_name)
                    if len(self.history) > self.max_history:
                        self.history.pop(0)
                    print(f"History: {self.history}")
                    self.check_activation()

    def check_activation(self) -> None:
        """Checks if the recent history matches the target sequence."""
        if not self.target_sequence:
            return

        seq_len = len(self.target_sequence)
        if len(self.history) >= seq_len:
            if self.history[-seq_len:] == self.target_sequence:
                self.jutsu_active = True
                self.history = [] # Clear history
                
    def run(self) -> None:
        try:
            # Mouse callback to set the Kamui center
            def set_center(event, x, y, flags, param):
                if event == cv2.EVENT_LBUTTONDOWN:
                    self.kamui_active = not self.kamui_active # Toggle on/off
                    self.center_point = [x, y]
                    print(f"Kamui Center set to: {x}, {y}, Active: {self.kamui_active}")

            cv2.namedWindow(APP_NAME)
            cv2.setMouseCallback(APP_NAME, set_center)

            print("Controls:")
            print(" - Click on the video: Activate/Move Kamui center")
            print(" - Click again: Deactivate")
            print("Starting AR... Press 'q' to quit, 'r' to reset.")

            precomputed_data = create_water_maps(self.prison_radius)
            bg_image = cv2.imread(self.jutsu_path)

            jutsu_factory = JutsuFactory(
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

            dojutsu_factory = DojutsuFactory(
                eye_opened_coef=EYE_OPENED_COEFFICIENT,
                dojutsu_img=self.dojutsu_img,
                sharingan_stage=self.sharingan_stage,
                mangekyou_technique=self.mangekyou_technique,
                mangekyou_owner=self.mangekyou_owner,
                current_chakra=self.current_chakra,
            )

            i = 0
            amplitude=50
            frequency=0.05
            speed = 2

            center_x, y = self.width // 2, self.height // 4
            x = 0.0

            while True:
                current_time = time.time()
                dt = current_time - self.last_time 
                self.last_time = current_time

                success, frame = self.cap.read()
                if not success: break

                frame = cv2.flip(frame, 1)

                rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

                holistic_results  = self.holistic_results.process(rgb)
                segmenter_results = self.segmenter.process(rgb) if self.is_jutsu_performed else None

                # Update Logic
                self.update_signs(frame)

                self.blindness_accumulator += self.blindness_counter * dt

                if self.blindness_accumulator >= LIGHT_BLINDNESS and self.blindness_accumulator < MEDIUM_BLINDNESS:
                    self.blindness_stage = "light"
                elif self.blindness_accumulator >= MEDIUM_BLINDNESS and self.blindness_accumulator < HEAVY_BLINDNESS:
                    self.blindness_stage = "medium"
                elif self.blindness_accumulator >= HEAVY_BLINDNESS:
                    self.blindness_stage = "heavy"
                else:                    
                    self.blindness_stage = None

                # Draw Effects
                if self.current_chakra >= 10:
                    frame = apply_blindness_effect(frame=frame, stage=self.blindness_stage)

                    jutsu_factory.current_chakra = self.current_chakra
                    frame, self.current_chakra = jutsu_factory.draw_jutsu_effect(frame=frame, dt=dt, blindness_stage=self.blindness_stage, jutsu_active=self.jutsu_active, target_sequence=self.target_sequence, history=self.history, holistic_results=holistic_results, segmenter_results=segmenter_results, mp_holistic=self.mp_holistic)
                    
                    dojutsu_factory.current_chakra = self.current_chakra
                    frame, self.blindness_counter, self.current_chakra = dojutsu_factory.draw_dojutsu_effect(frame=frame, dt=dt, x=x, y=y, blindness_stage=self.blindness_stage, center=self.center_point, kamui_active=self.kamui_active, holistic_results=holistic_results, mp_holistic=self.mp_holistic)
                    
                    # print(f"Blindness Counter from draw: {self.blindness_counter}, Blindness Accumulator: {self.blindness_accumulator}")
                frame = chakra_level(frame=frame, current_chakra=self.current_chakra, base_chakra_level=self.base_chakra_level, chakra_reset=self.chakra_reset) 

                x = center_x + (amplitude * math.sin(frequency * i))
                y += speed

                if y >= self.height - 200:
                    y = 20
                
                if self.current_chakra <= 0:
                    self.jutsu_active = False
                    self.is_jutsu_performed = False
                    self.cached_jutsu_effect = None
                    self.history = []
                    if self.chakra_reset <= 0:
                        print("Game Over! No resets left.")
                        self.current_chakra = 0
                        self.chakra_reset = 0
                        break
                    self.chakra_reset -= 1
                    self.current_chakra = self.base_chakra_level
                    print(f"Chakra depleted! Resetting... Remaining resets: {self.chakra_reset}")

                i += 1
                cv2.imshow(APP_NAME, frame)

                key = cv2.waitKey(1) & 0xFF
                if key == ord('q'):
                    break
                elif key == ord('r'):
                    self.jutsu_active = False
                    self.is_jutsu_performed = False
                    self.cached_jutsu_effect = None
                    self.history = []
                    print("Reset sequence.")
        finally:
            self.cap.release()
            cv2.destroyAllWindows()

def main():
    app = NarutoAR()
    # Display available techniques
    available = list(JUTSU_CATALOG.keys()) + list(MANGEKYOU_ABILITIES.keys())
    print(f"Available: {', '.join(available)}")
    current_user = input("Enter your username: ").strip()
    # Setup Player & Check Status
    player_data = setup_player(current_user)
    check_game_over(player_data)
    # Initialize App with player data
    app.update(
        current_chakra=player_data.get("chakra", 0.0),
        chakra_reset=player_data.get("resets", 0),
        base_chakra_level=player_data.get("base_chakra_level", MINIMUM_CHAKRA_LEVEL),
        blindness_accumulator=player_data.get("blindness_counter", 0.0)
    )
    choice = input("Choose technique (e.g., chidori, sharingan): ").lower()
    choices_list = [c.strip() for c in choice.split(",")]
    final_load_string = process_techniques(current_user, player_data, choices_list)
    print(f"Loading techniques: {final_load_string}")
    app.load_technique(final_load_string)
    app.run()

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