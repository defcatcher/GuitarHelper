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

Guitar Assistant is designed to be **100% Cross-Platform**. Since the audio engine is powered by `sounddevice` (wrapping PortAudio) and the GUI by `PyQt6`, it runs identically on Windows, macOS, and Linux.

### Prerequisites
You need **Python 3.9+** installed on your system.

### 🐧 Linux
The audio stack uses **PortAudio** (via `sounddevice`) to talk to **ALSA**, **PulseAudio**, or **PipeWire** (and optionally JACK). Install your distro’s PortAudio package (runtime + headers) first, then run the app from a virtual environment as below.

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

#### Flatpak (Flathub)

*Not published yet.* When the app is listed on [Flathub](https://flathub.org/), you will be able to install it with:

```bash
flatpak install flathub io.github.defcatcher.GuitarHelper
```

or from your distribution’s software center. A Flatpak manifest is maintained in the [`flatpak/`](flatpak/) directory for local builds and future submission.

**Flatpak from GitHub (no Flathub):** each [GitHub Release](https://github.com/defcatcher/GuitarHelper/releases) includes `io.github.defcatcher.GuitarHelper-x86_64.flatpak`. Install with:

```bash
flatpak install --user ./io.github.defcatcher.GuitarHelper-x86_64.flatpak
```

(If your browser saved a `.zip`, unpack it — the installable file is the `.flatpak` inside.)

### 🍎 macOS
macOS comes natively equipped with CoreAudio, which PortAudio supports out of the box. *(Fully supports Apple Silicon M1/M2/M3)*.
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
Windows utilizes WASAPI, DirectSound, or ASIO internally through the framework. No extra `C++` audio headers required.
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

## 📦 GitHub Releases (pre-built binaries)

Maintainers ship **Windows `.exe`**, **macOS `.dmg`**, **Linux AppImage**, and **Linux Flatpak** on each published release.

### If you maintain this repository

1. **Commit and push** everything you want in the release (e.g. on `main`).
2. **Create a git tag** (example for version `v0.1.0`):
   ```bash
   git tag -a v0.1.0 -m "v0.1.0"
   git push origin v0.1.0
   ```
3. On GitHub open **Releases → Draft a new release** (or create release from the tag).
4. Choose the tag, set the title and release notes, then click **Publish release**.
5. Wait for the workflow **Release builds** (Actions tab). It builds all platforms and **uploads files to the same release** (may take **15–30+ minutes** because of the Flatpak job).
6. Refresh the release page and confirm the assets: `.exe`, `.dmg`, `.AppImage`, `.flatpak`.

If any job fails, open the failed run in **Actions**, read the log, fix the workflow or manifest, tag a new patch release if needed.

### If you only want to install

1. Open **[Releases](https://github.com/defcatcher/GuitarHelper/releases)**.
2. Download the file for your OS (Flatpak: `io.github.defcatcher.GuitarHelper-x86_64.flatpak`).
3. **Linux Flatpak:** `flatpak install --user /path/to/io.github.defcatcher.GuitarHelper-x86_64.flatpak`  
   First run may prompt to add the **flathub** remote for runtimes — accept if offered.
4. Run: `flatpak run io.github.defcatcher.GuitarHelper` or use your app menu (**Guitar Assistant**).

---

## 🛠️ Technology Stack
- **Language**: Python 3.9+
- **GUI Framework**: PyQt6 (Qt 6)
- **Audio I/O**: `sounddevice` (Python wrapper for PortAudio)
- **DSP/Math Engine**: `numpy` (FFT, Autocorrelation, Matrix math)

---

## 📜 License
This project is open-source and distributed under the **MIT License**. See the [LICENSE](LICENSE) file for more information. Contributions and forks are welcome!
