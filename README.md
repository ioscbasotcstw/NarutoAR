# 🍥 NarutoAR: Real-Time Computer Vision Jutsu Simulator

**NarutoAR** is an interactive Augmented Reality (AR) application that brings the world of Naruto into real life using your webcam. By leveraging advanced computer vision models (YOLO, MediaPipe, OpenCV), this project detects real-time hand signs to trigger ninjutsu and overlays complex Dojutsu (eye techniques) onto your face. 

Experience the thrill of weaving signs for a casting *Chidori*,  *Death Reaper*, or awakening the *Mangekyou Sharingan*—but watch your Chakra reserves and beware of the Mangekyou's blindness penalty!

---

## ✨ Features

### 👐 Hand Sign Detection & Ninjutsu
* **YOLO-Powered Sign Tracking**: Weave hand signs (e.g., Tiger, Snake, Dragon) in front of your camera. The app tracks your sequence in real time.
* **Hand-Based Jutsus**: Trigger abilities like *Chidori* or *Rasengan* that dynamically scale and track to the position of your hands.
* **Background Alteration Jutsus**: Unleash techniques like *Death Reaper* that seamlessly replace your background using MediaPipe Selfie Segmentation.
* **Environmental Manipulations**: Perform *Water Prison Jutsu* with real-time OpenCV screen distortion and localized color mapping around your body.

### 👁️ Dojutsu (Eye Techniques)
* **Sharingan Tracking**: MediaPipe Holistic dynamically maps Sharingan overlays onto your pupils, automatically scaling and hiding them when you blink or close your eyes.
* **Mangekyou Abilities**:
  * 🔥 **Amaterasu**: Summons black flames with eye-bleeding effects.
  * 🌑 **Tsukuyomi**: Inverts colors, tints the world red, and distorts time.
  * 🌀 **Kamui**: Click anywhere on the screen to create a spatial distortion/suction vortex.
  * 🦴 **Susanoo**: Overlays a scaled Susanoo ribcage/avatar based on your shoulder and head proportions.
  * 🧠 **Kotoamatsukami**: An emerald-green color appears on the screen, featuring images of falling raven feathers with blurred, indistinct edges.

### 📊 RPG Mechanics
* **Chakra System**: Every active Jutsu and Dojutsu drains your Chakra. If you run out, your techniques deactivate until you reset.
* **Blindness Accumulator**: Overusing Mangekyou techniques incrementally builds blindness (Light ➔ Medium ➔ Heavy). Heavy blindness will severely obscure your camera feed!
* **Player Profiles**: Saves your current Chakra level, available resets, and blindness state across sessions.

---

## 🛠️ Prerequisites & Dependencies

To run this project, you will need **Python 3.10.16+** and a webcam.

**Required Assets (Not included in code):**
Since this project relies on custom assets, ensure you maintain the following directory structure:
* `src/assets/three_great_dojutsu/sharingan/mangekyou/techniques/amaterasu.gif`
* `src/assets/three_great_dojutsu/sharingan/mangekyou/techniques/susanoo.png`
* A custom trained YOLO model for hand signs (`YOLO_MODEL_PATH`).
* GIF/PNG files for Jutsus defined in your `JUTSU_CATALOG` and `SHARINGAN_STAGES`.

---

## 🚀 Installation & Usage

1. **Clone the repository**:
   ```bash
   git clone https://github.com/ioscbasotcstw/NarutoAR.git
   cd NarutoAR
   ```
2. **Install the required Python packages**:
   ```bash
   pip install -r requirements.txt
   ```
3. **Add API Key**: Create a `.env` file containing your Google GenAI API key, example `GEMINI_API_KEY="your-api-key"`

4. **Run the Application**:
   ```bash
   python main.py
   ```

5. **In-Game Flow**:
   * The terminal will prompt you to enter a **username** to load your save data.
   * You will be prompted to enter your chakra level and reset your chakra—this is optional, then choose whether it is just a jutsu (*Chidori*, *Death Reaper*, or *Water Prison*) or the *Sharingan*. If you choose both jutsu and Sharingan, enter the jutsu first, then the Sharingan.
   * Once the camera feed opens, perform the required hand signs to activate Jutsus, or open your eyes to activate Dojutsu.

---

## 🎮 Controls

* **user_info.naruto**: This is the file for configuring the Sharingan; it looks like this: `Kakashi. mangekyou. indra. amaterasu, tsukuyomi, susanoo, kamui, kotoamatsukami.`. First comes the user name, then the Sharingan stage (either Tomoe 1–3 or Mangekyo), followed by the Mangekyo owner, and finally the Mangekyo techniques. You can edit all these settings directly in the file. If you want, for example, to change the level from Tomoe 1 to Mangekyo, go ahead; or change the Mangekyo owner, or add a new Mangekyo technique—go ahead.
* **Left Mouse Click**: Sets the center point for the **Kamui** vortex and toggles it ON/OFF.
* **`r` Key**: Resets your hand sign history and deactivates the current Jutsu.
* **`q` Key**: Quits the application and saves your current Chakra/Blindness progress.

---

## 🏗️ Architecture

* **`NarutoAR` (Main Class)**: Handles the webcam loop, YOLO hand sign detections, sequence debouncing, and coordinates updating the graphics.
* **`JutsuFactory`**: Orchestrates standard Jutsu rendering. Switches between OpenCV base effects, background replacements, and hand-bound GIFs.
* **`DojutsuFactory`**: Processes MediaPipe Face/Pose landmarks to precisely map Sharingan eyes and render complex Mangekyou abilities based on eye-open states.
* **`TechniqueInterface`**: The base class guaranteeing an `apply()` method for modular integration of new techniques like `KamuiEffect` or `SusanooEffect`.

---

## 🙏 Special thanks

* To `tysuprawee` for his wonderful [Naruto-Hand-Signs](https://github.com/tysuprawee/Naruto-Hand-Signs) project, which inspired me to create my own project.
* To `@otani-sbz1y` for his [dataset](https://universe.roboflow.com/otani-sbz1y/naruto-in)

---

## ⚠️ Disclaimer
This is a fan-made, non-commercial open-source project. *Naruto*, *Sharingan*, and all related properties are trademarks of Masashi Kishimoto, Shueisha, and VIZ Media. This project is for educational purposes in computer vision and Python programming.
