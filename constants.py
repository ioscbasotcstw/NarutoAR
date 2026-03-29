# Dictionaries
SIGNS_MAPPING = {
    'hitsuji': 'ram', 'i': 'boar', 'inu': 'dog', 'mi': 'snake', 
    'ne': 'rat', 'saru': 'monkey', 'tatsu': 'dragon', 'tora': 'tiger', 
    'tori': 'bird', 'u': 'hare', 'uma': 'horse', 'ushi': 'ox'
}

JUTSU_CATALOG = {
    "chidori": {
        "type": "base_hand",
        "chakra_cost": 30,
        "sequence": ["ox", "hare", "monkey"],
        "image": "src/assets/jutsu/chidori.gif",
        "is_hand_jutsu": True,
    },
    "death reaper": {
        "type": "background_base",
        "chakra_cost": 50,
        "sequence": ["snake", "boar", "ram", "hare", "dog", "rat", "bird", "horse", "snake"],
        "image": "src/assets/jutsu/death_reaper.png",
        "is_hand_jutsu": False,
    },
    "water prison": {
        "type": "cv2_base",
        "chakra_cost": 40,
        "sequence": ["ram", "snake", "tiger", "hare", "snake", "dragon", "hare", "bird"],
        "image": None,
        "is_hand_jutsu": False,
    },
    "rasengan": {
        "type": "base_hand", 
        "chakra_cost": 50,
        "sequence": None,
        "image": "src/assets/jutsu/rasengan.gif",
        "is_hand_jutsu": True,
    },
}

SHARINGAN_STAGES = {
    "tomoe_1": {
        "chakra_cost": 5, 
        "image": "src/assets/three_great_dojutsu/sharingan/tomoe_1.png"
    },
    "tomoe_2": {
        "chakra_cost": 10, 
        "image": "src/assets/three_great_dojutsu/sharingan/tomoe_2.png"
    },
    "tomoe_3": {
        "chakra_cost": 15, 
        "image": "src/assets/three_great_dojutsu/sharingan/tomoe_3.png"
    },
    "mangekyou": {
        "chakra_cost": 25, 
        # "image": "src/assets/three_great_dojutsu/sharingan/mangekyou/itachi.png"
    },
}

MANGEKYOU_ABILITIES = {
    "amaterasu": {"chakra_cost": 70, "eye": "right_eye"},
    "tsukuyomi": {"chakra_cost": 75, "eye": "left_eye"},
    "kamui": {"chakra_cost": 55, "eye": "left_eye"},
    "kotoamatsukami": {"chakra_cost": 65, "eye": "left_eye"}, 
    "kagutsuchi": {"chakra_cost": 60, "eye": "right_eye"},    
    "susanoo": {"chakra_cost": 100, "eye": "both_eyes"},      
}

MANGEKYOU_USERS = {
    "itachi": ["amaterasu", "tsukuyomi", "susanoo"],
    "sasuke": ["kagutsuchi", "tsukuyomi", "susanoo"],
    "obito" : ["kamui", "susanoo"],
    "shisui": ["kotoamatsukami", "susanoo"],
    "madara": ["susanoo"],
    "indra" : ["amaterasu", "susanoo"],
}

# Strings
YOLO_MODEL_PATH = "src/models/naruto_signs_detection.onnx"
MANGEKYOU_PATH  = "src/assets/three_great_dojutsu/sharingan/mangekyou/"
APP_NAME        = "Naruto AR"
SAVE_FILE       = "app_cache.json"
USER_INFO_FILE  = "user_info.naruto"

# Integers
MINIMUM_CHAKRA_LEVEL = 30_000
MAXIMUM_CHAKRA_LEVEL = 1_000_000_000
MIN_CHAKRA_RESET     = 3
MAX_CHAKRA_RESET     = 10
DROP_CHAKRA_FACTOR   = 15
LIGHT_BLINDNESS      = 30_000    
MEDIUM_BLINDNESS     = 500_000  
HEAVY_BLINDNESS      = 10_000_000 

# Floats
EYE_SCALED_FACTOR      = 0.92
EYE_OPENED_COEFFICIENT = 0.20
SUSANO_SCALED_FACTOR   = 2.0