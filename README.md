<div align="center">
  <h1>🎸 Guitar Assistant</h1>
  <p><b>An ultra-minimalist, high-performance desktop assistant for guitarists.</b></p>
  
  [![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
  [![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/)
  [![PyQt6](https://img.shields.io/badge/PyQt6-GUI-orange.svg)](https://riverbankcomputing.com/software/pyqt/)
  
  <p align="center">
    <br>
    <i>Smart Notepad • Real-Time Tuner • Fretboard Visualizer • Precision Metronome</i>
    <br>
  </p>
</div>

---

Guitar Assistant is a highly responsive, elegantly designed desktop application built for musicians to practice, compose, and tune their guitars. Designed with a custom "Deep Green" theme and native `Manrope` typography, it brings all essential practice tools into a single seamless, distraction-free interface.

---

## ✨ Features

- **🧠 Smart Notepad**: An intelligent composition area that dynamically calculates diatonic chords based on your selected Key/Mode.
- **🔄 Auto-Transposing Capo**: Write your chords using brackets (e.g., `[Am]`). Whenever you change the Capo slider, the app mathematically transposes the text right in your editor so you can play in a new position instantly.
- **🎛️ Ultra-Low Latency Tuner**: A built-in microphone tuner running an optimized $O(N \log N)$ FFT-based YIN pitch algorithm. Features a global-minimum fallback threshold to accurately track acoustic guitar fundamentals without subharmonic jumping. Smoothed with a Median + Exponential Moving Average for a needle that feels analog.
- **⏱️ Precision Audio Metronome**: A multi-thread architecture metronome running independently of the UI event loop for sample-accurate playback. Visual flashes are dispatched securely across threads to prevent GUI stutters.
- **🎨 Deep Green Aesthetics**: A meticulously crafted dark UI bypassing all standard OS geometries in favor of custom flat elements. You will never see a native scrolling bar, dropdown arrow, or up/down tick in this application!

---

## 🚀 Installation & Running

Guitar Assistant runs on **Windows**, **macOS**, and **Linux**.

**Easiest option:** use the **[GitHub Releases](https://github.com/defcatcher/GuitarHelper/releases)** page — instructions are in **Downloading releases** below.

### 📦 Downloading releases

Each [release](https://github.com/defcatcher/GuitarHelper/releases) includes **Windows** (`.exe`), **macOS** (`.dmg`), **Linux** (`.AppImage` and `.flatpak` for x86_64).

1. Open the **Assets** list on a release and download the file for your platform.
2. **Windows:** run the `.exe`.
3. **macOS:** open the `.dmg` and drag the app into Applications (or run from the mounted image).
4. **Linux AppImage:** `chmod +x GuitarAssistant-x86_64.AppImage` then run it (or use your file manager).
5. **Linux Flatpak:** if the browser gave you a `.zip`, unpack it first. Then:
   ```bash
   flatpak install --user /path/to/io.github.defcatcher.GuitarHelper-x86_64.flatpak
   ```
   The first install may ask to add the **flathub** remote for runtimes — choose **yes** if prompted. Start the app with:
   ```bash
   flatpak run io.github.defcatcher.GuitarHelper
   ```
   or from the app menu under **Guitar Assistant**.

**Flathub (app store):** *not published yet.* When it is, you will be able to run `flatpak install flathub io.github.defcatcher.GuitarHelper` or install from your software center.

### Run from source (developers)

You need **Python 3.9+** and **Git**. On Linux you also need **PortAudio** development packages so the microphone/tuner can use your audio stack (ALSA, PulseAudio, PipeWire, or JACK).

### 🐧 Linux
Install your distro’s PortAudio packages (runtime + headers), then:

#### Ubuntu / Debian / Mint / Pop!_OS (APT)

```bash
sudo apt-get update
sudo apt-get install -y libportaudio2 libportaudiocpp0 portaudio19-dev python3-venv
```

#### Fedora / RHEL / CentOS Stream (DNF)

```bash
sudo dnf install -y portaudio-devel python3
```

#### Arch Linux / Manjaro / EndeavourOS (pacman)

```bash
sudo pacman -S --needed portaudio python
```

On Arch, the `portaudio` package includes what you need to build and run against the system library.

#### Clone, venv, and run (any distro)

```bash
git clone https://github.com/defcatcher/GuitarHelper.git
cd GuitarHelper

python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

python main.py
```

### 🍎 macOS
Prefer a **`.dmg`** from [Releases](https://github.com/defcatcher/GuitarHelper/releases). To run from a clone:
```bash
# 1. Clone the repository
git clone https://github.com/defcatcher/GuitarHelper.git
cd GuitarHelper

# 2. Create a virtual environment & install dependencies
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 3. Run the app!
python main.py
```
*Note: The first time you use the Tuner, macOS will prompt you to allow the Terminal/Python to access the Microphone.*

### 🪟 Windows
Prefer the **`.exe`** from [Releases](https://github.com/defcatcher/GuitarHelper/releases). To run from a clone:
```powershell
# 1. Clone the repository
git clone https://github.com/defcatcher/GuitarHelper.git
cd GuitarHelper

# 2. Create a virtual environment & install dependencies
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt

# 3. Run the app!
python main.py
```

---

## 📜 License
This project is open-source and distributed under the **MIT License**. See the [LICENSE](LICENSE) file for more information. Contributions and forks are welcome!
