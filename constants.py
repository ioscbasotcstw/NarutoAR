# Dictionaries
SIGNS_MAPPING = {
    'hitsuji': 'ram', 'i': 'boar', 'inu': 'dog', 'mi': 'snake', 
    'ne': 'rat', 'saru': 'monkey', 'tatsu': 'dragon', 'tora': 'tiger', 
    'tori': 'bird', 'u': 'hare', 'uma': 'horse', 'ushi': 'ox'
}

CORRESPONDING_VISUAL_TO_SIGNS = {
    'ram': 'src/assets/jutsu/signs/ram.jpg',
    'boar': 'src/assets/jutsu/signs/boar.jpg',
    'dog': 'src/assets/jutsu/signs/dog.jpg',
    'snake': 'src/assets/jutsu/signs/snake.jpg',
    'rat': 'src/assets/jutsu/signs/rat.jpg',
    'monkey': 'src/assets/jutsu/signs/monkey.jpg',
    'dragon': 'src/assets/jutsu/signs/dragon.jpg',
    'tiger': 'src/assets/jutsu/signs/tiger.jpg',
    'bird': 'src/assets/jutsu/signs/bird.jpg',
    'hare': 'src/assets/jutsu/signs/hare.jpg',
    'horse': 'src/assets/jutsu/signs/horse.jpg',
    'ox': 'src/assets/jutsu/signs/ox.jpg',
}

CORRESPONDING_NARUTO_STYLE = {
    "obito_mask": "src/assets/styles/obito_mask.png",
    "kakashi_mask": "src/assets/styles/kakashi_mask.png",
    "kakashi_hair": "src/assets/styles/kakashi_hair.png",
    "hidden_leaf_headband": "src/assets/styles/hidden_leaf_headband.png",
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
    },
}

MANGEKYOU_ABILITIES = {
    "amaterasu": {"chakra_cost": 70, "eye": "right_eye"},
    "tsukuyomi": {"chakra_cost": 75, "eye": "left_eye"},
    "kamui": {"chakra_cost": 55, "eye": "left_eye"},
    "kotoamatsukami": {"chakra_cost": 65, "eye": "left_eye"}, 
    "kagutsuchi": {"chakra_cost": 60, "eye": "right_eye"},    
    "susanoo": {"chakra_cost": 100, "eye": "both_eyes"},    
    "ohirume": {"chakra_cost": 110, "eye": "both_eyes"},  
}

MANGEKYOU_USERS = {
    "itachi": ["amaterasu", "tsukuyomi", "susanoo"],
    "sasuke": ["kagutsuchi", "tsukuyomi", "susanoo"],
    "obito" : ["kamui", "susanoo"],
    "shisui": ["kotoamatsukami", "susanoo"],
    "madara": ["susanoo"],
    "indra" : ["amaterasu", "susanoo"],
    "sarada": ["ohirume"],
}

RINNEGAN = {
    "rinnegan_left": "src/assets/three_great_dojutsu/rinnegan/rinnegan_left.png",
    "rinnegan_right": "src/assets/three_great_dojutsu/rinnegan/rinnegan_right.png",
    "chakra_cost": 100,
}

SIX_PATHS_TECHNIQUE = {
    "deva_path": {
        "chibaku_tensei": {"chakra_cost": 200},
    },
}

BYAKUGAN = {
    "byakugan": "src/assets/three_great_dojutsu/byakugan/byakugan.png",
    "chakra_cost": 50,
}

# Lists
STYLES = ["obito_fullfacemask", "kakashi_mask", "kakashi_hair", "hidden_leaf_headband"]
BACKGROUNDS = ["src/assets/backgrounds/akatsuki.jpeg", "src/assets/backgrounds/infinite_tsukuyomi.png", "src/assets/backgrounds/konoha.jpg", "src/assets/backgrounds/naruto_forest.jpg"]
RIGHT_EYE_LANDMARKS = [33, 7, 163, 144, 145, 153, 154, 155, 133, 246, 161, 160, 159, 158, 157, 173, 468, 469, 470, 471, 472, 46, 53, 52, 65, 55, 70, 63, 105, 66, 107]
LEFT_EYE_LANDMARKS = [263, 249, 390, 373, 374, 380, 381, 382, 362, 466, 388, 387, 386, 385, 384, 398, 473, 474, 475, 476, 477, 276, 283, 282, 295, 285, 300, 293, 334, 296, 336]

# Strings
YOLO_MODEL_PATH = "src/models/naruto_signs_detection.onnx"
MANGEKYOU_PATH  = "src/assets/three_great_dojutsu/sharingan/mangekyou/"
SHARINGAN_PATH  = "src/assets/three_great_dojutsu/sharingan/"
RINNEGAN_PATH   = "src/assets/three_great_dojutsu/rinnegan/"
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