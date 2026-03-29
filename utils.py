import os
import sys
import time
import math
import json
import cv2
import numpy as np
from typing import List
from PIL import Image
from evolution_of_sharingan import generate
from constants import (
    MANGEKYOU_ABILITIES, 
    MANGEKYOU_USERS, 
    MIN_CHAKRA_RESET, 
    MAX_CHAKRA_RESET, 
    SAVE_FILE, 
    MANGEKYOU_PATH,
    MINIMUM_CHAKRA_LEVEL, 
    MAXIMUM_CHAKRA_LEVEL, 
    JUTSU_CATALOG, 
    SHARINGAN_STAGES,
    USER_INFO_FILE
)

def overlay_image(frame: np.ndarray, ov: np.ndarray, x: int, y: int) -> np.ndarray:
    """Overlays image 'ov' onto 'frame' at center coordinates (x, y) with alpha blending."""
    frame_h, frame_w = frame.shape[:2]
    ov_h, ov_w, ov_ch = ov.shape

    if ov_ch < 4: 
        return frame  # No alpha channel

    # Center coordinates
    x -= ov_w // 2
    y -= ov_h // 2

    # Calculate clipping coordinates
    x1, y1 = max(x, 0), max(y, 0)
    x2, y2 = min(x + ov_w, frame_w), min(y + ov_h, frame_h)

    # Calculate overlay offsets
    ov_x1, ov_y1 = max(0, -x), max(0, -y)
    ov_x2, ov_y2 = ov_x1 + (x2 - x1), ov_y1 + (y2 - y1)

    # Crop
    ov_cropped = ov[ov_y1:ov_y2, ov_x1:ov_x2]
    frame_roi = frame[y1:y2, x1:x2]

    if ov_cropped.size == 0 or frame_roi.size == 0:
        return frame

    # Blend
    ov_bgr = ov_cropped[:, :, :3]
    ov_alpha = ov_cropped[:, :, 3] / 255.
    ov_alpha = ov_alpha[:, :, np.newaxis]
    frame[y1:y2, x1:x2] = (ov_alpha * ov_bgr + (1.0 - ov_alpha) * frame_roi).astype(np.uint8)
    return frame

def get_distance(p1, p2, w: int, h: int) -> float:
    """Euclidean distance between two landmarks."""
    x1, y1 = int(p1.x * w), int(p1.y * h)
    x2, y2 = int(p2.x * w), int(p2.y * h)
    return math.hypot(x2 - x1, y2 - y1)

def load_gif_frames(path): 
    """Loads a GIF from the hard drive ONCE and returns a list of frames."""
    gif = Image.open(path)
    frames = []
    try:
        while True:
            frame_rgba = gif.convert("RGBA")
            cv_frame = cv2.cvtColor(np.array(frame_rgba), cv2.COLOR_RGBA2BGRA)
            frames.append(cv_frame)
            gif.seek(gif.tell() + 1)
    except EOFError:
        pass
    return frames

def get_animated_frame(frames, current_index, last_time, fps=15):
    """Returns the current animation frame and updates timers."""
    if not frames:
        return None, current_index, last_time
    
    current_time = time.time()
    
    if current_time - last_time >= (1.0 / fps):
        current_index = (current_index + 1) % len(frames)
        last_time = current_time
        
    return frames[current_index], current_index, last_time

def chakra_level(frame, current_chakra, base_chakra_level, chakra_reset):
    """Draws the chakra level UI onto the frame."""
    _, w = frame.shape[:2] 
    
    bar_width, bar_height = 200, 20
    margin_right, margin_top = 20, 40 
    
    x1 = w - margin_right - bar_width
    y1 = margin_top                    
    x2 = w - margin_right              
    y2 = margin_top + bar_height       
    
    fill_width = int((current_chakra / base_chakra_level) * bar_width) if base_chakra_level > 0 else 0
    
    cv2.rectangle(frame, (x1, y1), (x2, y2), (255, 255, 255), -1)
    if fill_width > 0:
        cv2.rectangle(frame, (x1, y1), (x1 + fill_width, y2), (0, 0, 255), -1)
        
    text = f'Chakra: {((current_chakra / base_chakra_level) * 100):.2f}% | Reset: {chakra_reset}'
    cv2.putText(frame, text, (x1 - 100, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
    return frame

def save_data_to_txt(username: str = None, sharingan_stage: str | None = None, mangekyou_techniques: List[str] | None = None, mangekyou_owner: str | None = None) -> None:
    """Saves Dojutsu stage info to a custom text file."""
    parts = [username or ""]
    parts.append(sharingan_stage or " ")
    parts.append(mangekyou_owner or " ")
    
    if mangekyou_techniques:
        parts.append(", ".join(mangekyou_techniques))
    else:
        parts.append(" ")

    with open(USER_INFO_FILE, 'a', encoding='utf-8') as f:
        f.write(". ".join(parts) + ".\n")

def get_user_data(username: str):
    """Retrieves basic user info from the custom text file."""
    if not os.path.exists(USER_INFO_FILE):
        return None 

    with open(USER_INFO_FILE, 'r', encoding='utf-8') as f:
        for line in f:
            parts = line.split('. ')
            if parts[0] == username:
                stage = parts[1].strip() if len(parts) > 1 else None
                owner = parts[2].strip() if len(parts) > 1 else None
                techs_str = parts[3].strip() if len(parts) > 2 else ""
                if techs_str.endswith('.'):
                    techs_str = techs_str.replace('.', '')
                techniques = techs_str.split(", ") if techs_str else []
                return {"stage": stage, "owner": owner, "techniques": techniques}    
    return None 

def draw_eye_bleeding(frame, face_results, technique):
    """Draws blood dripping from the specific eye required by the technique."""
    image_path = os.path.join(MANGEKYOU_PATH, "blood_bleed_from_eye.png")
    if not os.path.exists(image_path):
        return frame
    
    ov = cv2.imread(image_path, cv2.IMREAD_UNCHANGED)
    if ov is None or not face_results: 
        return frame
    
    tech_data = MANGEKYOU_ABILITIES.get(technique, {})
    required_eye = tech_data.get("eye")

    if required_eye == "left_eye":
        iris_landmark, eyelid_landmark = 468, 145
    elif required_eye == "right_eye":
        iris_landmark, eyelid_landmark = 473, 374
    else:
        return frame # Skip if it requires both eyes (e.g., Susanoo)

    h, w = frame.shape[:2]
    landmarks = face_results.landmark

    eye_iris = landmarks[iris_landmark]
    eyelid_bottom = landmarks[eyelid_landmark]
    chin = landmarks[152]

    iris_x = int(eye_iris.x * w)
    eyelid_y = int(eyelid_bottom.y * h)
    chin_y = int(chin.y * h)

    desire_height = int((chin_y - eyelid_y) * 0.8)
    desired_width = int(desire_height * (ov.shape[1] / ov.shape[0]))

    ov_resized = cv2.resize(ov, (desired_width, desire_height))
    center_y = eyelid_y + (desire_height // 2)

    return overlay_image(frame, ov_resized, iris_x, center_y)

def apply_blindness_effect(frame, stage):
    """Applies a blindness effect to the frame based on the severity level."""
    kernels = {"light": (10, 10), "medium": (50, 50), "heavy": (100, 100)}
    if stage in kernels:
        return cv2.blur(frame, kernels[stage])
    return frame  

def check_owner(mangekyou_owner, technique):
    """Checks if the current user is the owner of the Mangekyou technique."""
    return technique in MANGEKYOU_USERS.get(mangekyou_owner, [])

def load_player_data(username, chakra_reset=MIN_CHAKRA_RESET, chakra_level=MINIMUM_CHAKRA_LEVEL, blindness_counter=0):
    """Loads specific user data or returns defaults if new user."""
    default_data = {
        "chakra": chakra_level,
        "base_chakra_level": chakra_level, 
        "resets": chakra_reset,
        "blindness": None,
        "blindness_counter": blindness_counter, 
    }

    if not os.path.exists(SAVE_FILE):
        return default_data

    try:
        with open(SAVE_FILE, "r") as f:
            all_data = json.load(f)
            return all_data.get(username, default_data)
    except (json.JSONDecodeError, ValueError):
        return default_data

def save_player_data(username, chakra, resets, base_chakra_level=MINIMUM_CHAKRA_LEVEL, blindness_counter=0, blindness=None):
    """Saves the current stats to the JSON file."""
    all_data = {}
    if os.path.exists(SAVE_FILE):
        try:
            with open(SAVE_FILE, "r") as f:
                all_data = json.load(f)
        except (json.JSONDecodeError, ValueError):
            pass

    all_data[username] = {
        "chakra": chakra,
        "base_chakra_level": base_chakra_level, 
        "resets": resets,
        "blindness": blindness,
        "blindness_counter": blindness_counter,
    }

    with open(SAVE_FILE, "w") as f:
        json.dump(all_data, f, indent=4)

##########################################      C     ##########################################################
##########################################      H     ##########################################################
##########################################      A     ##########################################################
##########################################      N     ##########################################################
##########################################      G     ##########################################################
##########################################      E     ##########################################################
def create_water_maps(radius):
    """Precomputes the distortion, shadows, and reflections."""
    size = int(radius * 2)
    center = radius

    x, y = np.meshgrid(np.arange(size), np.arange(size))
    dx, dy = x - center, y - center
    r = np.sqrt(dx**2 + dy**2)

    inside = r < radius

    map_x, map_y = x.astype(np.float32), y.astype(np.float32)
    bulge_strength = 0.6 
    
    r_norm = r[inside] / radius
    r_new = radius * (r_norm ** (1.0 + bulge_strength))
    r_safe = np.where(r[inside] == 0, 1, r[inside])
    
    map_x[inside] = center + dx[inside] * (r_new / r_safe)
    map_y[inside] = center + dy[inside] * (r_new / r_safe)

    shading = np.zeros((size, size, 1), dtype=np.float32)
    shading[inside, 0] = r_norm ** 2.5 

    highlight = np.zeros((size, size, 3), dtype=np.uint8)
    cv2.ellipse(highlight, (int(radius*0.65), int(radius*0.35)), 
                (int(radius*0.4), int(radius*0.15)), 
                angle=-45, startAngle=0, endAngle=360, 
                color=(255, 255, 255), thickness=-1)
    highlight = cv2.GaussianBlur(highlight, (0, 0), sigmaX=radius*0.08)

    circle_mask = np.zeros((size, size, 1), dtype=np.float32)
    circle_mask[inside] = 1.0

    return map_x, map_y, shading, highlight, circle_mask

def get_optional_int(prompt: str, min_val: int, max_val: int, default_val: int):
    """Safely prompts for an integer, handling empty inputs and invalid characters."""
    user_input = input(prompt).strip()
    if not user_input:
        return None
    try:
        val = int(user_input)
        if min_val <= val <= max_val:
            return val
        print(f"Invalid input. Should be between {min_val} and {max_val}. Using default value {default_val}.")
        return default_val
    except ValueError:
        print(f"Invalid numeric input. Using default value {default_val}.")
        return default_val

def setup_player(current_user: str) -> dict:
    """Handles optional stat inputs and returns the loaded player data."""
    chakra_prompt = f"(Optional) Enter your chakra level ({MINIMUM_CHAKRA_LEVEL}-{MAXIMUM_CHAKRA_LEVEL}): "
    chakra_input = get_optional_int(chakra_prompt, MINIMUM_CHAKRA_LEVEL, MAXIMUM_CHAKRA_LEVEL, MINIMUM_CHAKRA_LEVEL)
    
    reset_prompt = f"(Optional) Enter your chakra resets ({MIN_CHAKRA_RESET}-{MAX_CHAKRA_RESET}): "
    reset_input = get_optional_int(reset_prompt, MIN_CHAKRA_RESET, MAX_CHAKRA_RESET, MIN_CHAKRA_RESET)

    if chakra_input is not None and reset_input is not None:
        save_player_data(current_user, chakra=chakra_input, resets=reset_input, base_chakra_level=chakra_input)
        return load_player_data(current_user, reset_input, chakra_input)
    
    return load_player_data(current_user)

def check_game_over(player_data: dict):
    """Checks for game-over conditions and exits if necessary."""
    if player_data.get("blindness") == "heavy":
        print("You can no longer see anything... Game Over! Maybe consider get new sharingan eye somewhere else 👉👈")
        sys.exit()

    if player_data.get("resets", 0) <= 0 and player_data.get("chakra", 0.0) <= 0:
        print("You have no more resets or chakra left. Game Over!")
        sys.exit()

def process_techniques(current_user: str, player_data: dict, choices_list: list) -> str:
    """Processes user jutsu/dojutsu selections and returns the final load string."""
    techniques_to_load = []
    user_data = get_user_data(current_user)
    
    # Dojutsu Logic (Check for word 'sharingan' or specific stage names)
    if any(c == "sharingan" or c in SHARINGAN_STAGES for c in choices_list):
        if user_data and user_data['stage']:
            stage = user_data['stage']
            mangekyou_owner = user_data.get("owner", 'None')
            techniques = user_data.get('techniques', [])           
            print(f"\nWelcome back, {current_user}!\nActivating your previously awakened: {stage.upper()}")
            if techniques:
                print(f"Available Mangekyou techniques: {', '.join(techniques).title()}")   
            print(f"Mangekyou owner is {mangekyou_owner.capitalize()}")  
            print(f"Your current blindness stage: {player_data.get('blindness', 'None')}")   
        else:
            scenario = input("\nDescribe your emotional scenario to determine your Sharingan stage: ")
            stage = generate(scenario).replace(' ', '_')
            techniques = []
            mangekyou_owner = None
            
            if stage == "mangekyou":
                mangekyou_owner_input = input("Choose only one sharingan owner(`list of owners | itachi obito sasuke madara shisui indra |`): ").lower()
                if len(mangekyou_owner_input.split(",")) <= 1:
                    mangekyou_owner = mangekyou_owner_input
                    
                tech_input = input("Which Mangekyou technique do you want to manifest? (e.g., amaterasu, tsukuyomi): ").lower()
                techniques = [t.strip() for t in tech_input.split(',') if t.strip()]
                
            print(f"\nBased on your scenario, you have awakened: {stage.upper()}") 
            save_data_to_txt(current_user, stage, techniques, mangekyou_owner)
            print("(Your Sharingan data has been saved for next time!)")
            
        sharingan_str = f"sharingan {stage.lower()} {mangekyou_owner.lower()} {' '.join(techniques).lower()}".strip()
        techniques_to_load.append(sharingan_str)

    # Jutsu Logic
    jutsu_choices = [c for c in choices_list if c in JUTSU_CATALOG]
    if jutsu_choices:
        techniques_to_load.append(jutsu_choices[0])
    
    if techniques_to_load:
        return ", ".join(techniques_to_load)
    return ", ".join(choices_list)

def print_session_results(app):
    """Prints the final statistics of the session."""
    chakra_percent = (app.current_chakra / app.base_chakra_level * 100) if app.base_chakra_level > 0 else 0.0
    
    print("-" * 40)
    print("SESSION RESULTS:")
    print(f"Blindness accumulator: {app.blindness_accumulator}")
    print(f"Final Blindness Stage: {app.blindness_stage}")
    print(f"Base Chakra: {app.base_chakra_level}")
    print(f"Final Chakra: {app.current_chakra}")
    print(f"Remaining Chakra(%): {chakra_percent:.2f}%")
    print(f"Resets Remaining: {app.chakra_reset}")
    print("-" * 40)