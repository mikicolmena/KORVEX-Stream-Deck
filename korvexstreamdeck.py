#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys, os, json, re, time, threading, subprocess, shutil, struct, math
from typing import Dict, List, Optional
from dataclasses import dataclass, field

import pulsectl
from pulsectl import PulseError

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QSlider, QPushButton, QScrollArea, QFrame, QComboBox, QStackedWidget,
    QMessageBox, QLineEdit, QDialog, QDialogButtonBox, QInputDialog,
    QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView,
    QSizePolicy, QListWidget, QListWidgetItem, QCheckBox
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QObject, QThread, pyqtSlot, QSize
from PyQt6.QtGui import QColor, QPainter, QLinearGradient, QBrush, QIcon

def log(tag: str, msg: str):
    print(f"[Korvex/{tag}] {msg}", flush=True)

# ======================================================================
# ESTILO
# ======================================================================
APP_BG = "#0B0B0E"; PANEL_BG = "#15151C"; PANEL_LIGHT = "#1F1F2A"
BORDER = "#2A2A35"; BORDER_HOVER = "#3E3E4E"
ACCENT = "#5E6AD2"; ACCENT_HOVER = "#707EED"; ACCENT_DIM = "rgba(94, 106, 210, 0.15)"
TEXT_MAIN = "#F1F1F4"; TEXT_MUTED = "#8B8B9E"
DANGER = "#E54D4D"; DANGER_DIM = "rgba(229, 77, 77, 0.15)"; SUCCESS = "#43B581"
STRIP_MIN_W = 110
STRIP_MAX_W = 220
STRIP_MIN_H = 280
STRIP_HEADER_H = 26
ROW_HEIGHT = 48

STYLESHEET = f"""
QWidget {{ background-color: {APP_BG}; color: {TEXT_MAIN}; font-family: "Segoe UI", "Inter", sans-serif; font-size: 10pt; }}
QScrollArea, QScrollArea > QWidget > QWidget, QWidget#FaderContainer, QLabel {{ background-color: transparent; }}
QScrollBar:vertical {{ background: transparent; width: 10px; margin: 0; }}
QScrollBar::handle:vertical {{ background: {BORDER_HOVER}; border-radius: 5px; min-height: 40px; }}
QScrollBar::handle:vertical:hover {{ background: {TEXT_MUTED}; }}
QScrollBar::add-line, QScrollBar::sub-line {{ height: 0; }}
QScrollBar:horizontal {{ background: transparent; height: 10px; margin: 0; }}
QScrollBar::handle:horizontal {{ background: {BORDER_HOVER}; border-radius: 5px; min-width: 40px; }}
QListWidget#SideBar {{ background-color: {APP_BG}; border: none; border-right: 1px solid {BORDER}; outline: none; }}
QListWidget#SideBar::item {{ padding: 12px 20px; margin: 4px 12px; border-radius: 8px; color: {TEXT_MUTED}; font-weight: 600; font-size: 11pt; background-color: transparent; }}
QListWidget#SideBar::item:hover {{ background-color: {PANEL_BG}; color: {TEXT_MAIN}; }}
QListWidget#SideBar::item:selected {{ background-color: {ACCENT_DIM}; color: {ACCENT}; }}
QFrame#ChannelStrip {{ background-color: {PANEL_BG}; border: 1px solid {BORDER}; border-radius: 12px; }}
QFrame#ChannelStrip:hover {{ border-color: {BORDER_HOVER}; background-color: {PANEL_LIGHT}; }}

QSlider#Fader {{ background-color: transparent; }}
QSlider#Fader::groove:vertical {{ margin: 0 8px; background-color: rgba(0, 0, 0, 0.55); border-radius: 4px; border: 1px solid rgba(255,255,255,0.06); }}
QSlider#Fader::sub-page:vertical {{ margin: 0 8px; background-color: rgba(0, 0, 0, 0.55); border-radius: 4px; }}
QSlider#Fader::add-page:vertical {{ margin: 0 8px; background-color: {ACCENT}; border-radius: 4px; }}
QSlider#Fader::handle:vertical {{ height: 14px; width: 24px; margin: 0 -9px; border-radius: 7px; background-color: #FFFFFF; border: 2px solid {ACCENT}; }}
QSlider#Fader::handle:vertical:hover {{ background-color: {TEXT_MAIN}; }}
QSlider#Fader::handle:vertical:pressed {{ background-color: {ACCENT_HOVER}; }}

QPushButton {{ background-color: {PANEL_LIGHT}; border: 1px solid {BORDER}; border-radius: 8px; padding: 8px 16px; color: {TEXT_MAIN}; font-weight: 600; }}
QPushButton:hover {{ background-color: {BORDER_HOVER}; }}
QPushButton:pressed {{ background-color: {ACCENT}; border-color: {ACCENT}; color: #FFF; }}
QPushButton:disabled {{ background-color: {PANEL_BG}; color: {TEXT_MUTED}; border-color: {BORDER}; }}
QPushButton#PrimaryBtn {{ background-color: {ACCENT}; border: none; color: #FFF; }}
QPushButton#PrimaryBtn:hover {{ background-color: {ACCENT_HOVER}; }}
QPushButton#PrimaryBtn:disabled {{ background-color: {BORDER}; color: {TEXT_MUTED}; }}
QPushButton#DangerBtn {{ background-color: {DANGER}; border: none; color: #FFF; }}
QPushButton#DangerBtn:hover {{ background-color: #F06060; }}
QPushButton#DangerBtn:disabled {{ background-color: {BORDER}; color: {TEXT_MUTED}; }}
QPushButton#IconBtn, QPushButton#IconBtnDanger {{ background-color: transparent; border: none; color: {TEXT_MUTED}; padding: 4px; border-radius: 6px; }}
QPushButton#IconBtn:hover {{ background-color: {PANEL_LIGHT}; color: {TEXT_MAIN}; }}
QPushButton#IconBtnDanger:hover {{ background-color: {DANGER_DIM}; color: {DANGER}; }}
QPushButton#MuteBtn {{ background-color: {PANEL_BG}; border: 1px solid {BORDER}; font-size: 11pt; padding: 6px; border-radius: 8px; color: {TEXT_MAIN}; }}
QPushButton#MuteBtn:hover {{ background-color: {PANEL_LIGHT}; border-color: {BORDER_HOVER}; }}
QPushButton#MuteBtn:checked {{ background-color: {DANGER_DIM}; border-color: {DANGER}; color: {DANGER}; }}
QPushButton#AddStripBtn {{ background-color: transparent; border: 2px dashed {BORDER}; border-radius: 12px; color: {BORDER_HOVER}; font-size: 28pt; font-weight: 300; }}
QPushButton#AddStripBtn:hover {{ border-color: {ACCENT}; color: {ACCENT}; background-color: {ACCENT_DIM}; }}

QTableWidget {{ background-color: {PANEL_BG}; border: 1px solid {BORDER}; border-radius: 12px; gridline-color: {BORDER}; outline: none; }}
QTableWidget::viewport {{ background-color: transparent; border-radius: 12px; }}
QTableWidget::item {{ padding: 4px 12px; border-bottom: 1px solid {BORDER}; }}
QHeaderView {{ background-color: transparent; }}
QHeaderView::section {{ background-color: {PANEL_BG}; color: {TEXT_MUTED}; padding: 0 12px; border: none; border-bottom: 2px solid {BORDER}; font-weight: 700; font-size: 9pt; text-transform: uppercase; border-top-left-radius: 12px; border-top-right-radius: 12px; }}

QComboBox {{ background-color: {PANEL_LIGHT}; border: 1px solid {BORDER}; border-radius: 6px; padding: 0 10px; color: {TEXT_MAIN}; min-height: 32px; font-size: 10pt; }}
QComboBox:hover {{ border-color: {ACCENT}; }}
QComboBox::drop-down {{ border: none; width: 22px; background: transparent; }}
QComboBox::down-arrow {{ image: none; width: 0; height: 0; border-style: solid; border-width: 5px 5px 0 5px; border-color: {TEXT_MUTED} transparent transparent transparent; margin-right: 6px; }}
QComboBox QAbstractItemView {{ background-color: {PANEL_LIGHT}; border: 1px solid {BORDER}; border-radius: 6px; selection-background-color: {ACCENT}; color: {TEXT_MAIN}; outline: none; padding: 4px; }}

QCheckBox {{ color: {TEXT_MAIN}; font-size: 10pt; spacing: 10px; padding: 4px; }}
QCheckBox::indicator {{ width: 18px; height: 18px; border-radius: 5px; border: 1px solid {BORDER_HOVER}; background: {PANEL_BG}; }}
QCheckBox::indicator:hover {{ border-color: {ACCENT}; }}
QCheckBox::indicator:checked {{ background: {ACCENT}; border-color: {ACCENT}; }}

QDialog {{ background-color: {APP_BG}; border: 1px solid {BORDER}; border-radius: 12px; }}
QLineEdit {{ background-color: {PANEL_BG}; border: 1px solid {BORDER}; border-radius: 8px; padding: 10px 14px; color: {TEXT_MAIN}; }}
QLineEdit:focus {{ border-color: {ACCENT}; }}
QLabel#PageTitle {{ font-size: 18pt; font-weight: 800; color: {TEXT_MAIN}; letter-spacing: -0.5px; }}
QLabel#SubTitle {{ color: {TEXT_MUTED}; font-size: 10pt; }}
QLabel#DangerWarn {{ color: {DANGER}; font-size: 10pt; font-weight: 600; }}
QLabel#SettingLabel {{ color: {TEXT_MAIN}; font-size: 11pt; font-weight: 600; }}
QLabel#SettingHint {{ color: {TEXT_MUTED}; font-size: 9.5pt; }}
"""

_HAS_PW_METADATA = shutil.which("pw-metadata") is not None
_HAS_PACTL = shutil.which("pactl") is not None
_HAS_PW_DUMP = shutil.which("pw-dump") is not None
_HAS_PAREC = shutil.which("parec") is not None

# ======================================================================
# LOGO
# ======================================================================
def _find_logo_path() -> Optional[str]:
    candidates = [
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "KorvexLogo.png"),
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "KorvexLogo.ico"),
        "/usr/share/icons/hicolor/256x256/apps/korvex-streamdeck.png",
        "/usr/share/icons/hicolor/128x128/apps/korvex-streamdeck.png",
        "/usr/share/pixmaps/korvex-streamdeck.png",
        os.path.expanduser("~/.local/share/icons/korvex-streamdeck.png"),
    ]
    for p in candidates:
        if os.path.exists(p):
            return p
    return None

def _get_app_icon() -> QIcon:
    path = _find_logo_path()
    if path:
        return QIcon(path)
    return QIcon()

# ======================================================================
# AUTOSTART
# ======================================================================
def _autostart_path() -> str:
    return os.path.expanduser("~/.config/autostart/korvex-streamdeck.desktop")

def is_autostart_enabled() -> bool:
    return os.path.exists(_autostart_path())

def enable_autostart() -> bool:
    try:
        path = _autostart_path()
        os.makedirs(os.path.dirname(path), exist_ok=True)
        script = os.path.abspath(sys.argv[0])
        py = sys.executable or "/usr/bin/env python3"
        with open(path, "w") as f:
            f.write(f"""[Desktop Entry]
Type=Application
Name=KORVEX Stream Deck
Comment=Audio mixer for streaming
Exec={py} {script}
Icon=korvex-streamdeck
Terminal=false
Categories=Audio;AudioVideo;
X-GNOME-Autostart-enabled=true
StartupNotify=false
""")
        return True
    except Exception as e:
        log("ERROR", f"enable_autostart: {e}")
        return False

def disable_autostart() -> bool:
    try:
        path = _autostart_path()
        if os.path.exists(path): os.remove(path)
        return True
    except Exception as e:
        log("ERROR", f"disable_autostart: {e}")
        return False

# ======================================================================
# DATACLASSES
# ======================================================================
@dataclass
class ChannelInfo:
    sink_name: str; name: str; sink_index: int
    volume: int = 100; mute: bool = False; peak: float = 0.0; is_system: bool = False

@dataclass
class ProcessInfo:
    index: int; name: str; binary: str; icon_name: str
    current_channel_sink_name: str; volume: int = 100; mute: bool = False

@dataclass
class AppState:
    channels: Dict[str, ChannelInfo] = field(default_factory=dict)
    processes: List[ProcessInfo] = field(default_factory=list)
    physical_sinks: List[Dict[str, str]] = field(default_factory=list)
    current_output_sink: str = ""
    system_channel_sink_name: str = ""
    assignments: Dict[str, str] = field(default_factory=dict)

# ======================================================================
# UTILIDADES
# ======================================================================
def slugify(text: str) -> str:
    text = text.strip().lower()
    text = re.sub(r'[^\w\s-]', '', text, flags=re.UNICODE)
    return re.sub(r'[-\s]+', '_', text)[:40]

def generate_sink_name(base_name: str) -> str:
    return f"korvex_ch_{slugify(base_name)}"

def parse_module_args(args_str: str) -> Dict[str, str]:
    res = {}
    for m in re.finditer(r'(\w+)\s*=\s*("([^"]*)"|(\S+))', args_str or ""):
        k = m.group(1)
        v = m.group(3) if m.group(3) is not None else m.group(4)
        res[k] = v.strip('"')
    return res

def _is_index_error(exc: Exception) -> bool:
    s = str(exc)
    return s.isdigit() or "No such" in s or "does not exist" in s

def pretty_app_name(binary: str, fallback: str = "") -> str:
    src = (binary or fallback or "").strip()
    if not src: return "Desconocido"
    for prefix in ("com.", "org.", "io.", "net."):
        if src.startswith(prefix):
            parts = src.split(".")
            if len(parts) >= 2:
                src = parts[-1]
                break
    src = src.replace("-", " ").replace("_", " ").strip()
    return src.title()

# ======================================================================
# PEAK READER — variante 1 (peak lineal + release rápido)
# ======================================================================
class PeakReader(threading.Thread):
    SAMPLE_RATE = 48000
    CHANNELS = 2
    CHUNK_MS = 20
    RELEASE_TAU = 0.10
    GAIN = 1.8

    def __init__(self, sink_name: str, cache: dict, lock: threading.Lock):
        super().__init__(daemon=True, name=f"PeakReader-{sink_name}")
        self.sink_name = sink_name
        self.monitor_name = f"{sink_name}.monitor"
        self.cache = cache
        self.lock = lock
        self._stop_flag = threading.Event()
        self._proc: Optional[subprocess.Popen] = None

    def stop(self):
        self._stop_flag.set()
        if self._proc:
            try: self._proc.terminate()
            except Exception: pass

    def run(self):
        if not _HAS_PAREC: return
        try:
            self._proc = subprocess.Popen(
                ["parec",
                 f"--device={self.monitor_name}",
                 "--format=s16le",
                 f"--rate={self.SAMPLE_RATE}",
                 f"--channels={self.CHANNELS}",
                 "--latency-msec=20",
                 "--raw"],
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                bufsize=-1
            )
        except Exception as e:
            log("PEAK", f"{self.sink_name}: parec: {e}")
            return

        frames = int(self.SAMPLE_RATE * self.CHUNK_MS / 1000)
        total = frames * self.CHANNELS
        nbytes = total * 2
        fmt = f"<{total}h"
        dt = self.CHUNK_MS / 1000.0
        a_rel = 1.0 - math.exp(-dt / self.RELEASE_TAU)
        level = 0.0

        try:
            while not self._stop_flag.is_set():
                buf = bytearray()
                while len(buf) < nbytes and not self._stop_flag.is_set():
                    piece = self._proc.stdout.read(nbytes - len(buf))
                    if not piece: raise EOFError("parec stdout cerrado")
                    buf.extend(piece)
                if len(buf) < nbytes: break

                samples = struct.unpack(fmt, bytes(buf))
                peak = 0
                for s in samples:
                    a = -s if s < 0 else s
                    if a > peak: peak = a

                p = min(1.0, peak / 32768.0 * self.GAIN)
                if p > level: level = p
                else: level += (p - level) * a_rel

                with self.lock:
                    self.cache[self.sink_name] = level
        except EOFError:
            pass
        except Exception as e:
            if not self._stop_flag.is_set():
                log("PEAK", f"{self.sink_name}: {e}")
        finally:
            try:
                if self._proc:
                    self._proc.terminate()
                    try: self._proc.wait(timeout=0.5)
                    except Exception: pass
            except Exception: pass

# ======================================================================
# PEAK METER
# ======================================================================
class PeakMeter(QWidget):
    def __init__(self, parent=None, width=6):
        super().__init__(parent)
        self.setFixedWidth(width)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Expanding)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self._level = 0.0

    def set_level(self, level: float):
        new = max(0.0, min(1.0, level))
        if abs(new - self._level) > 0.002:
            self._level = new
            self.update()

    def paintEvent(self, event):
        p = QPainter(self); p.setRenderHint(QPainter.RenderHint.Antialiasing)
        r = self.rect(); p.fillRect(r, QColor(0, 0, 0, 120))
        h = int(r.height() * self._level)
        if h > 0:
            g = QLinearGradient(0, r.bottom(), 0, r.top())
            g.setColorAt(0.0, QColor(SUCCESS)); g.setColorAt(0.7, QColor("#F5C451"))
            g.setColorAt(1.0, QColor(DANGER))
            p.setBrush(QBrush(g)); p.setPen(Qt.PenStyle.NoPen)
            p.drawRoundedRect(0, r.bottom() - h, r.width(), h, 3, 3)

# ======================================================================
# AUDIO WORKER
# ======================================================================
class AudioWorker(QObject):
    state_updated = pyqtSignal(object)
    peaks_updated = pyqtSignal(dict)
    error_occurred = pyqtSignal(str)
    operation_finished = pyqtSignal(bool, str)
    finished = pyqtSignal()

    MASTER_SINK_NAME = "korvex_master"
    CHANNEL_PREFIX = "korvex_ch_"
    SYSTEM_CHANNEL_VISIBLE_NAME = "System"

    def __init__(self, config_path: str):
        super().__init__()
        self.config_path = config_path
        self.config = self._load_config()
        self.pulse: Optional[pulsectl.Pulse] = None
        self._running = False; self._stopping = False; self._reconnecting = False
        self._reconnect_attempts = 0
        self._reconnect_timer: Optional[QTimer] = None
        self._save_timer: Optional[QTimer] = None
        self._config_dirty = False
        self._ops_lock = threading.Lock()
        self._module_ids: Dict[str, int] = {}
        self._sink_name_to_index: Dict[str, int] = {}
        self._channel_volumes: Dict[str, int] = {}
        self._channel_mutes: Dict[str, bool] = {}
        self._auto_moved_sis: Dict[int, str] = {}
        self._last_applied_vol: Dict[int, int] = {}
        self._peak_cache: Dict[str, float] = {}
        self._peak_lock = threading.Lock()
        self._peak_readers: Dict[str, PeakReader] = {}
        self._original_default_sink_name: Optional[str] = None
        self._poll_timer: Optional[QTimer] = None
        self._peak_timer: Optional[QTimer] = None
        log("INIT", f"pw-metadata={_HAS_PW_METADATA} pactl={_HAS_PACTL} "
                    f"pw-dump={_HAS_PW_DUMP} parec={_HAS_PAREC}")

    def _start_peak_reader(self, sink_name: str):
        if not _HAS_PAREC: return
        if sink_name in self._peak_readers: return
        reader = PeakReader(sink_name, self._peak_cache, self._peak_lock)
        reader.start()
        self._peak_readers[sink_name] = reader

    def _stop_peak_reader(self, sink_name: str):
        reader = self._peak_readers.pop(sink_name, None)
        if reader: reader.stop()
        with self._peak_lock: self._peak_cache.pop(sink_name, None)

    def _stop_all_peak_readers(self):
        for sn in list(self._peak_readers.keys()):
            self._stop_peak_reader(sn)

    @pyqtSlot()
    def start(self):
        if self._running: return
        try:
            self.pulse = pulsectl.Pulse('korvex-worker')
            self._original_default_sink_name = self.pulse.server_info().default_sink_name
            log("START", f"Default sink: {self._original_default_sink_name}")
            self._cleanup_ghost_modules()
            self._ensure_audio_graph()
            self._running = True; self._stopping = False
            self._reconnecting = False; self._reconnect_attempts = 0
            if self._poll_timer is None:
                self._poll_timer = QTimer(self)
                self._poll_timer.setInterval(250)
                self._poll_timer.timeout.connect(self._poll_loop)
            self._poll_timer.start()
            if self._peak_timer is None:
                self._peak_timer = QTimer(self)
                self._peak_timer.setInterval(20)
                self._peak_timer.timeout.connect(self._emit_peaks)
            self._peak_timer.start()
            self._poll_loop()
        except Exception as e:
            log("ERROR", f"Fatal init: {e}")
            self.error_occurred.emit(f"Fatal Audio Init Error: {e}")
            self.finished.emit()

    @pyqtSlot()
    def stop(self):
        log("STOP", "Deteniendo worker...")
        self._stopping = True; self._running = False
        if self._poll_timer: self._poll_timer.stop()
        if self._peak_timer: self._peak_timer.stop()
        if self._reconnect_timer:
            self._reconnect_timer.stop(); self._reconnect_timer = None
        if self._save_timer: self._save_timer.stop()
        self._stop_all_peak_readers()
        acquired = self._ops_lock.acquire(timeout=2.0)
        if self.pulse:
            try:
                if self._original_default_sink_name:
                    try:
                        so = self._get_sink_by_name(self._original_default_sink_name)
                        if so: self.pulse.default_set(so)
                    except Exception: pass
                real_idx = self._get_sink_index(self._original_default_sink_name or "")
                if real_idx is None:
                    phys = [s for s in self.pulse.sink_list()
                            if not s.name.startswith(self.CHANNEL_PREFIX)
                            and s.name != self.MASTER_SINK_NAME]
                    if phys: real_idx = phys[0].index
                if real_idx is not None:
                    our = {self.MASTER_SINK_NAME} | {k.split(':', 1)[1]
                        for k in self._module_ids if k.startswith('sink:')}
                    for si in self.pulse.sink_input_list():
                        if self._is_our_loopback(si): continue
                        try:
                            so = self.pulse.sink_info(si.sink)
                            if so.name in our:
                                self.pulse.sink_input_move(si.index, real_idx)
                        except Exception: pass
            except Exception: pass
            finally:
                self._unload_all_tracked_modules()
                try: self.pulse.close()
                except Exception: pass
                self.pulse = None
        self._flush_config()
        if acquired: self._ops_lock.release()
        self.finished.emit()

    @pyqtSlot()
    def _emit_peaks(self):
        if not self._running or self._stopping or self._reconnecting: return
        with self._peak_lock:
            snapshot = dict(self._peak_cache)
        for sn in list(snapshot.keys()):
            if self._channel_mutes.get(sn, False) or self._channel_volumes.get(sn, 100) == 0:
                snapshot[sn] = 0.0
        try: self.peaks_updated.emit(snapshot)
        except Exception: pass

    def _load_module(self, name, args, key):
        if not self.pulse: return None
        try:
            mid = self.pulse.module_load(name, args)
            self._module_ids[key] = mid
            return mid
        except Exception as e:
            log("ERROR", f"Module {key}: {e}")
            return None

    def _unload_module(self, key):
        mid = self._module_ids.pop(key, None)
        if mid and self.pulse:
            try: self.pulse.module_unload(mid)
            except Exception: pass

    def _unload_all_tracked_modules(self):
        for k in list(self._module_ids.keys()): self._unload_module(k)

    def _cleanup_ghost_modules(self):
        if not self.pulse: return
        try:
            for mod in self.pulse.module_list():
                args = parse_module_args(mod.argument or "")
                name = mod.name or ""
                is_sink = (name == "module-null-sink" and
                           (args.get("sink_name") == self.MASTER_SINK_NAME or
                            args.get("sink_name", "").startswith(self.CHANNEL_PREFIX)))
                is_lb = (name == "module-loopback" and (
                    args.get("source") == f"{self.MASTER_SINK_NAME}.monitor" or
                    (args.get("source", "").startswith(self.CHANNEL_PREFIX)
                     and args.get("source", "").endswith(".monitor")) or
                    args.get("sink") == self.MASTER_SINK_NAME or
                    args.get("sink", "").startswith(self.CHANNEL_PREFIX)))
                if is_sink or is_lb:
                    try: self.pulse.module_unload(mod.index)
                    except Exception: pass
        except Exception: pass

    def _get_sink_by_name(self, name):
        if not self.pulse: return None
        try:
            for s in self.pulse.sink_list():
                if s.name == name: return s
        except Exception: pass
        return None

    def _create_null_sink(self, sink_name: str, description: str):
        args = f"sink_name={sink_name} sink_properties=device.description='{description}'"
        return self._load_module("module-null-sink", args, f"sink:{sink_name}")

    def _ensure_audio_graph(self):
        if not self._sink_exists(self.MASTER_SINK_NAME):
            self._create_null_sink(self.MASTER_SINK_NAME, "KORVEX Master Mix")
        else:
            for mod in self.pulse.module_list():
                if mod.name == "module-null-sink" and \
                   parse_module_args(mod.argument).get("sink_name") == self.MASTER_SINK_NAME:
                    self._module_ids[f"sink:{self.MASTER_SINK_NAME}"] = mod.index
                    break
        sys_sink = f"{self.CHANNEL_PREFIX}system"
        if not self._sink_exists(sys_sink):
            self._create_null_sink(sys_sink, self.SYSTEM_CHANNEL_VISIBLE_NAME)
        else:
            for mod in self.pulse.module_list():
                if mod.name == "module-null-sink" and \
                   parse_module_args(mod.argument).get("sink_name") == sys_sink:
                    self._module_ids[f"sink:{sys_sink}"] = mod.index
                    break
        for ch_cfg in self.config.get("channels", []):
            name = ch_cfg["name"]
            if name == self.SYSTEM_CHANNEL_VISIBLE_NAME: continue
            sink_name = ch_cfg.get("sink_name", generate_sink_name(name))
            if not sink_name.startswith(self.CHANNEL_PREFIX):
                sink_name = generate_sink_name(name)
            if not self._sink_exists(sink_name):
                mid = self._create_null_sink(sink_name, name)
                if mid: ch_cfg["sink_name"] = sink_name
            else:
                for mod in self.pulse.module_list():
                    if mod.name == "module-null-sink" and \
                       parse_module_args(mod.argument).get("sink_name") == sink_name:
                        self._module_ids[f"sink:{sink_name}"] = mod.index
                        break
        self._recreate_channel_loopbacks()
        self._update_output_routing()
        try:
            so = self._get_sink_by_name(sys_sink)
            if so: self.pulse.default_set(so)
        except Exception: pass
        for sn in self._get_current_channels_raw().keys():
            self._start_peak_reader(sn)
        self._save_config()

    def _recreate_channel_loopbacks(self):
        if not self.pulse: return
        for k in [k for k in self._module_ids
                  if k.startswith("lb:") and k.endswith("->master")]:
            self._unload_module(k)
        for sink_name in self._get_current_channels_raw().keys():
            key = f"lb:{sink_name}->master"
            if key not in self._module_ids:
                self._load_module("module-loopback",
                    f"source={sink_name}.monitor sink={self.MASTER_SINK_NAME} "
                    f"source_dont_move=true sink_dont_move=true", key)

    def _update_output_routing(self):
        if not self.pulse: return
        self._unload_module("lb:master->output")
        target = self.config.get("output_sink", "")
        if not target:
            phys = self._get_physical_sinks_raw()
            if phys: target = phys[0]["name"]
        if target and self._sink_exists(target):
            self._load_module("module-loopback",
                f"source={self.MASTER_SINK_NAME}.monitor sink={target} "
                f"source_dont_move=true sink_dont_move=true", "lb:master->output")
            if self.config.get("output_sink") != target:
                self.config["output_sink"] = target
                self._save_config()

    def _sink_exists(self, name):
        if not self.pulse: return False
        try: return any(s.name == name for s in self.pulse.sink_list())
        except Exception: return False

    def _get_sink_index(self, name):
        idx = self._sink_name_to_index.get(name)
        if idx is not None: return idx
        if not self.pulse: return None
        try:
            for s in self.pulse.sink_list():
                if s.name == name:
                    self._sink_name_to_index[name] = s.index
                    return s.index
        except Exception: pass
        return None

    def _sink_input_exists(self, si_index) -> bool:
        if not self.pulse: return False
        try:
            for si in self.pulse.sink_input_list():
                if si.index == si_index: return True
        except Exception: pass
        return False

    def _is_our_loopback(self, si) -> bool:
        try:
            nn = (si.proplist.get("node.name", "") or "").lower()
            mn = (si.proplist.get("media.name", "") or "").lower()
            sn_ = (si.name or "").lower()
            an = (si.proplist.get("application.name", "") or "").lower()
            if nn.startswith("loopback-"): return True
            if "loopback" in nn and "output" in nn: return True
            if sn_.startswith("loopback from"): return True
            if mn.startswith("loopback from"): return True
            if "loopback" in an and "korvex" in (nn + an): return True
        except Exception: pass
        return False

    # ✅ NUEVO: filtrar streams internos del sistema que no son apps de usuario
    def _should_ignore_sink_input(self, si) -> bool:
        """Ignora streams del sistema que no queremos mostrar."""
        try:
            binary = (si.proplist.get("application.process.binary", "") or "").lower()
            app_name = (si.proplist.get("application.name", "") or "").lower()
            node_name = (si.proplist.get("node.name", "") or "").lower()

            # speech-dispatcher y sus drivers (dummy, espeak, festival, etc.)
            if binary.startswith("sd_") or app_name.startswith("speech-dispatcher"):
                return True
            if "speech-dispatcher" in node_name:
                return True

            # Otros streams internos comunes que no aportan nada al usuario
            ignored_binaries = {
                "pipewire", "wireplumber", "pulseaudio",
                "gnome-shell", "plasmashell",
            }
            if binary in ignored_binaries:
                return True
        except Exception:
            pass
        return False

    def _move_stream(self, si_index: int, target_sink_name: str) -> bool:
        si_info = None
        try:
            for si in self.pulse.sink_input_list():
                if si.index == si_index: si_info = si; break
        except Exception: return False
        if si_info is None: return False
        moved = False
        if _HAS_PACTL:
            try:
                r = subprocess.run(
                    ["pactl", "move-sink-input", str(si_index), target_sink_name],
                    capture_output=True, text=True, timeout=3)
                if r.returncode == 0: moved = True
            except Exception: pass
        if not moved:
            idx = self._get_sink_index(target_sink_name)
            if idx is not None:
                try:
                    self.pulse.sink_input_move(si_index, idx)
                    moved = True
                except Exception: pass
        return moved

    def _get_current_channels_raw(self):
        res = {}
        if not self.pulse: return res
        for s in self.pulse.sink_list():
            if s.name != self.MASTER_SINK_NAME and s.name.startswith(self.CHANNEL_PREFIX):
                res[s.name] = {"sink_name": s.name, "sink_index": s.index,
                               "description": s.description}
        return res

    def _get_physical_sinks_raw(self):
        if not self.pulse: return []
        return [{"name": s.name, "description": s.description}
                for s in self.pulse.sink_list()
                if not s.name.startswith(self.CHANNEL_PREFIX)
                and s.name != self.MASTER_SINK_NAME]

    def _apply_volume_to_channel_apps(self, channel_sink_name: str, volume: int, mute: bool):
        if not self.pulse: return 0
        target_idx = self._get_sink_index(channel_sink_name)
        if target_idx is None: return 0
        count = 0
        try:
            for si in self.pulse.sink_input_list():
                if self._is_our_loopback(si): continue
                if self._should_ignore_sink_input(si): continue
                if si.sink != target_idx: continue
                n = 2
                if si.volume and si.volume.values: n = len(si.volume.values)
                try:
                    self.pulse.sink_input_volume_set(si.index,
                        pulsectl.PulseVolumeInfo([volume/100.0]*n))
                    self.pulse.sink_input_mute(si.index, mute)
                    self._last_applied_vol[si.index] = volume
                    count += 1
                except Exception: pass
        except Exception: pass
        return count

    def _poll_loop(self):
        if not self._running or self._stopping or self._reconnecting: return
        if not self._ops_lock.acquire(timeout=0.1): return
        released = False
        try:
            if not self.pulse: raise PulseError("No connection")
            self.state_updated.emit(self._collect_state())
        except (PulseError, ConnectionResetError, OSError, BrokenPipeError) as e:
            self._ops_lock.release(); released = True
            self._handle_pulse_disconnect(); return
        except Exception as e:
            log("ERROR", f"poll: {e}")
        finally:
            if not released:
                try: self._ops_lock.release()
                except Exception: pass

    def _handle_pulse_disconnect(self):
        if self._reconnecting or self._stopping: return
        self._reconnecting = True
        if self._poll_timer: self._poll_timer.stop()
        if self._peak_timer: self._peak_timer.stop()
        self._stop_all_peak_readers()
        if self.pulse:
            try: self.pulse.close()
            except Exception: pass
        self.pulse = None; self._module_ids.clear()
        wait_time = min(0.5 * (2 ** self._reconnect_attempts), 5.0)
        self._reconnect_attempts += 1
        self._reconnect_timer = QTimer(self)
        self._reconnect_timer.setSingleShot(True)
        self._reconnect_timer.timeout.connect(self._attempt_reconnect)
        self._reconnect_timer.start(int(wait_time * 1000))

    def _attempt_reconnect(self):
        if self._stopping: return
        try:
            self.pulse = pulsectl.Pulse('korvex-reconnect')
            self._cleanup_ghost_modules()
            self._ensure_audio_graph()
            self._reconnecting = False; self._reconnect_attempts = 0
            self._running = True
            if self._poll_timer: self._poll_timer.start()
            if self._peak_timer: self._peak_timer.start()
        except Exception as e:
            log("ERROR", f"reconnect: {e}")
            self._reconnect_timer = QTimer(self)
            self._reconnect_timer.setSingleShot(True)
            self._reconnect_timer.timeout.connect(self._attempt_reconnect)
            self._reconnect_timer.start(1000)

    def _collect_state(self):
        state = AppState()
        raw = self._get_current_channels_raw()
        assignments = self.config.get("assignments", {})
        all_sinks_list = self.pulse.sink_list()
        all_sinks_by_idx = {s.index: s for s in all_sinks_list}
        all_sinks_by_name = {s.name: s for s in all_sinks_list}
        self._sink_name_to_index = {s.name: s.index for s in all_sinks_list}

        current_si_idx = {si.index for si in self.pulse.sink_input_list()}
        for k in list(self._auto_moved_sis.keys()):
            if k not in current_si_idx: del self._auto_moved_sis[k]
        for k in list(self._last_applied_vol.keys()):
            if k not in current_si_idx: del self._last_applied_vol[k]

        for sn in raw.keys():
            if sn not in self._peak_readers:
                self._start_peak_reader(sn)

        for sink_name, info in raw.items():
            vol = self._channel_volumes.get(sink_name, 100)
            mute = self._channel_mutes.get(sink_name, False)
            if sink_name not in self._channel_volumes:
                so = all_sinks_by_name.get(sink_name)
                if so:
                    try:
                        vol = int(self.pulse.sink_volume(so.index).value_flat * 100)
                        mute = self.pulse.sink_mute(so.index)
                        self._channel_volumes[sink_name] = vol
                        self._channel_mutes[sink_name] = mute
                    except Exception: pass
            with self._peak_lock:
                peak = self._peak_cache.get(sink_name, 0.0)
            if mute or vol == 0: peak = 0.0
            is_sys = info["description"] == self.SYSTEM_CHANNEL_VISIBLE_NAME
            state.channels[sink_name] = ChannelInfo(
                sink_name=sink_name, name=info["description"],
                sink_index=info["sink_index"],
                volume=vol, mute=mute, peak=min(1.0, peak), is_system=is_sys)
            if is_sys: state.system_channel_sink_name = sink_name

        for si in self.pulse.sink_input_list():
            if self._is_our_loopback(si): continue
            if self._should_ignore_sink_input(si): continue   # ✅ filtro nuevo
            so = all_sinks_by_idx.get(si.sink)
            ch_sink = so.name if (so and so.name in raw) else "unknown"
            binary = si.proplist.get("application.process.binary", "") or \
                     si.proplist.get("application.name", si.name)
            icon_name = si.proplist.get("application.icon_name", "") or ""
            try:
                app_vol = int(self.pulse.sink_input_volume(si.index).value_flat * 100)
                app_mute = self.pulse.sink_input_mute(si.index)
            except Exception:
                app_vol, app_mute = 100, False
            state.processes.append(ProcessInfo(
                index=si.index, name=si.name, binary=binary, icon_name=icon_name,
                current_channel_sink_name=ch_sink,
                volume=app_vol, mute=app_mute))

            if ch_sink != "unknown":
                target_vol = self._channel_volumes.get(ch_sink, 100)
                target_mute = self._channel_mutes.get(ch_sink, False)
                if self._last_applied_vol.get(si.index) != target_vol or app_mute != target_mute:
                    try:
                        n = 2
                        if si.volume and si.volume.values: n = len(si.volume.values)
                        self.pulse.sink_input_volume_set(si.index,
                            pulsectl.PulseVolumeInfo([target_vol/100.0]*n))
                        self.pulse.sink_input_mute(si.index, target_mute)
                        self._last_applied_vol[si.index] = target_vol
                    except Exception: pass

            if binary in assignments:
                tv = assignments[binary]
                ts = next((sn for sn, ci in raw.items()
                           if ci["description"] == tv), None)
                if ts:
                    target_sink_name = raw[ts]["sink_name"]
                    already = self._auto_moved_sis.get(si.index)
                    if already != target_sink_name:
                        if ch_sink != target_sink_name:
                            if self._move_stream(si.index, target_sink_name):
                                self._auto_moved_sis[si.index] = target_sink_name
                                self._apply_volume_to_channel_apps(
                                    target_sink_name,
                                    self._channel_volumes.get(target_sink_name, 100),
                                    self._channel_mutes.get(target_sink_name, False))
                        else:
                            self._auto_moved_sis[si.index] = target_sink_name

        state.physical_sinks = self._get_physical_sinks_raw()
        state.current_output_sink = self.config.get("output_sink", "")
        state.assignments = assignments.copy()
        return state

    def _load_config(self):
        os.makedirs(self.config_path, exist_ok=True)
        fpath = os.path.join(self.config_path, "config.json")
        default = {"channels": [], "assignments": {}, "output_sink": "",
                   "channel_volumes": {}, "channel_mutes": {}}
        if os.path.exists(fpath):
            try:
                with open(fpath, "r") as f: default.update(json.load(f))
            except Exception: pass
        if not any(c.get("name") == self.SYSTEM_CHANNEL_VISIBLE_NAME
                   for c in default.get("channels", [])):
            default.setdefault("channels", []).insert(0,
                {"name": self.SYSTEM_CHANNEL_VISIBLE_NAME,
                 "sink_name": f"{self.CHANNEL_PREFIX}system"})
        self._channel_volumes = default.get("channel_volumes", {})
        self._channel_mutes = default.get("channel_mutes", {})
        return default

    def _save_config(self):
        self.config["channel_volumes"] = self._channel_volumes
        self.config["channel_mutes"] = self._channel_mutes
        self._config_dirty = True
        if self._save_timer is None:
            self._save_timer = QTimer(self)
            self._save_timer.setSingleShot(True)
            self._save_timer.timeout.connect(self._flush_config)
        if not self._save_timer.isActive():
            self._save_timer.start(500)

    @pyqtSlot()
    def _flush_config(self):
        if not self._config_dirty: return
        try:
            with open(os.path.join(self.config_path, "config.json"), "w") as f:
                json.dump(self.config, f, indent=4)
            self._config_dirty = False
        except Exception as e:
            log("ERROR", f"config save: {e}")

    def _try_lock(self, timeout=2.0):
        if not self._running or self._reconnecting or self._stopping: return False
        return self._ops_lock.acquire(timeout=timeout)

    def _check_lock(self):
        if not self._running or self._reconnecting or self._stopping:
            self.operation_finished.emit(False, "Sistema no listo"); return False
        if not self._ops_lock.acquire(timeout=2.0):
            self.operation_finished.emit(False, "Sistema ocupado"); return False
        if not self.pulse:
            self._ops_lock.release()
            self.operation_finished.emit(False, "Sin conexión"); return False
        return True

    def _unlock(self):
        try: self._ops_lock.release()
        except Exception: pass

    @pyqtSlot(str, int)
    def set_volume(self, sink_name, volume):
        if not self._try_lock(timeout=2.0): return
        try:
            self._channel_volumes[sink_name] = volume
            self._save_config()
            self._apply_volume_to_channel_apps(sink_name, volume,
                self._channel_mutes.get(sink_name, False))
            idx = self._get_sink_index(sink_name)
            if idx is not None:
                info = self.pulse.sink_info(idx)
                n = len(info.volume.values) if info.volume and info.volume.values else 2
                try:
                    self.pulse.sink_volume_set(idx,
                        pulsectl.PulseVolumeInfo([volume/100.0]*n))
                except Exception: pass
        except Exception as e:
            log("ERROR", f"set_volume: {e}")
        finally: self._unlock()

    @pyqtSlot(str)
    def toggle_mute(self, sink_name):
        if not self._try_lock(timeout=2.0): return
        try:
            new_mute = not self._channel_mutes.get(sink_name, False)
            self._channel_mutes[sink_name] = new_mute
            self._save_config()
            self._apply_volume_to_channel_apps(
                sink_name, self._channel_volumes.get(sink_name, 100), new_mute)
            idx = self._get_sink_index(sink_name)
            if idx is not None:
                try: self.pulse.sink_mute(idx, new_mute)
                except Exception: pass
        except Exception as e:
            log("ERROR", f"toggle_mute: {e}")
        finally: self._unlock()

    @pyqtSlot(int, str)
    def move_sink_input(self, si_index, target_sink_name):
        if not self._try_lock(timeout=1.0): return
        try:
            if not self._sink_input_exists(si_index): return
            binary = None
            try:
                for si in self.pulse.sink_input_list():
                    if si.index == si_index:
                        binary = si.proplist.get("application.process.binary", "") or \
                                 si.proplist.get("application.name", "")
                        break
            except Exception: pass
            if self._move_stream(si_index, target_sink_name):
                self._auto_moved_sis[si_index] = target_sink_name
                raw = self._get_current_channels_raw()
                target_info = raw.get(target_sink_name)
                if binary and target_info:
                    self.config.setdefault("assignments", {})[binary] = target_info["description"]
                    self._save_config()
                self._apply_volume_to_channel_apps(
                    target_sink_name,
                    self._channel_volumes.get(target_sink_name, 100),
                    self._channel_mutes.get(target_sink_name, False))
        except Exception as e:
            if not _is_index_error(e): log("ERROR", f"move: {e}")
        finally: self._unlock()

    @pyqtSlot(str)
    def add_channel(self, visible_name):
        visible_name = (visible_name or "").strip()
        if not visible_name:
            self.operation_finished.emit(False, "Nombre vacío"); return
        if not self._check_lock(): return
        try:
            raw = self._get_current_channels_raw()
            if any(i["description"] == visible_name for i in raw.values()):
                raise ValueError("Ya existe un canal con ese nombre")
            sn = generate_sink_name(visible_name)
            if self._sink_exists(sn):
                b, i = sn, 2
                while self._sink_exists(f"{b}_{i}"): i += 1
                sn = f"{b}_{i}"
            mid = self._create_null_sink(sn, visible_name)
            if mid is None: raise RuntimeError("No se pudo crear sink")
            key = f"lb:{sn}->master"
            lb = self._load_module("module-loopback",
                f"source={sn}.monitor sink={self.MASTER_SINK_NAME} "
                f"source_dont_move=true sink_dont_move=true", key)
            if lb is None:
                self._unload_module(f"sink:{sn}")
                raise RuntimeError("No se pudo crear loopback")
            self.config.setdefault("channels", []).append(
                {"name": visible_name, "sink_name": sn})
            self._channel_volumes[sn] = 100
            self._channel_mutes[sn] = False
            self._save_config()
            self._start_peak_reader(sn)
            self.operation_finished.emit(True, "Canal creado")
        except Exception as e:
            log("ERROR", f"add_channel: {e}")
            self.operation_finished.emit(False, str(e))
        finally: self._unlock()

    @pyqtSlot(str)
    def remove_channel(self, sink_name):
        if not self._check_lock(): return
        try:
            raw = self._get_current_channels_raw()
            info = raw.get(sink_name)
            if not info: raise ValueError("Canal no encontrado")
            if info["description"] == self.SYSTEM_CHANNEL_VISIBLE_NAME:
                raise ValueError("No se puede borrar System")
            sys_sink_name = f"{self.CHANNEL_PREFIX}system"
            sys_idx = self._get_sink_index(sys_sink_name)
            if sys_idx is not None:
                for si in self.pulse.sink_input_list():
                    if self._is_our_loopback(si): continue
                    if self._should_ignore_sink_input(si): continue
                    if si.sink == info["sink_index"]:
                        if self._sink_input_exists(si.index):
                            try: self.pulse.sink_input_move(si.index, sys_idx)
                            except Exception: pass
            dead_name = info["description"]
            for b, c in list(self.config.get("assignments", {}).items()):
                if c == dead_name:
                    self.config["assignments"][b] = self.SYSTEM_CHANNEL_VISIBLE_NAME
            for k in list(self._auto_moved_sis.keys()):
                if self._auto_moved_sis[k] == sink_name:
                    del self._auto_moved_sis[k]
            self._stop_peak_reader(sink_name)
            self._unload_module(f"lb:{sink_name}->master")
            self._unload_module(f"sink:{sink_name}")
            self.config["channels"] = [c for c in self.config.get("channels", [])
                                       if c.get("sink_name") != sink_name]
            self._channel_volumes.pop(sink_name, None)
            self._channel_mutes.pop(sink_name, None)
            sys_vol = self._channel_volumes.get(sys_sink_name, 100)
            sys_mute = self._channel_mutes.get(sys_sink_name, False)
            self._apply_volume_to_channel_apps(sys_sink_name, sys_vol, sys_mute)
            self._save_config()
            self.operation_finished.emit(True, "Canal borrado")
        except Exception as e:
            log("ERROR", f"remove_channel: {e}")
            self.operation_finished.emit(False, str(e))
        finally: self._unlock()

    @pyqtSlot(str, str)
    def rename_channel(self, old_sink_name, new_visible_name):
        new_visible_name = (new_visible_name or "").strip()
        if not new_visible_name:
            self.operation_finished.emit(False, "Nombre vacío"); return
        if not self._check_lock(): return
        try:
            raw = self._get_current_channels_raw()
            info = raw.get(old_sink_name)
            if not info: raise ValueError("Canal no encontrado")
            if info["description"] == self.SYSTEM_CHANNEL_VISIBLE_NAME:
                raise ValueError("No se puede renombrar System")
            if info["description"] == new_visible_name:
                self.operation_finished.emit(True, "Sin cambios"); return
            if any(i["description"] == new_visible_name for i in raw.values()):
                raise ValueError("Ya existe un canal con ese nombre")
            self.pulse.sink_proplist_update(info["sink_index"],
                {"device.description": new_visible_name})
            for c in self.config.get("channels", []):
                if c.get("sink_name") == old_sink_name: c["name"] = new_visible_name
            for b, c in self.config.get("assignments", {}).items():
                if c == info["description"]:
                    self.config["assignments"][b] = new_visible_name
            self._save_config()
            self.operation_finished.emit(True, "Renombrado")
        except Exception as e:
            log("ERROR", f"rename_channel: {e}")
            self.operation_finished.emit(False, str(e))
        finally: self._unlock()

    @pyqtSlot(str)
    def set_output_sink(self, sink_name):
        if not self._check_lock(): return
        try:
            if sink_name.startswith(self.CHANNEL_PREFIX) or sink_name == self.MASTER_SINK_NAME:
                raise ValueError("No se puede enrutar a canal virtual")
            if not self._sink_exists(sink_name):
                raise ValueError("Sink no existe")
            if self.config.get("output_sink") != sink_name:
                self.config["output_sink"] = sink_name
                self._save_config()
                self._update_output_routing()
            self.operation_finished.emit(True, "Salida actualizada")
        except Exception as e:
            log("ERROR", f"set_output_sink: {e}")
            self.operation_finished.emit(False, str(e))
        finally: self._unlock()

# ======================================================================
# CHANNEL STRIP
# ======================================================================
class ChannelStrip(QFrame):
    volume_changed = pyqtSignal(str, int)
    mute_toggled = pyqtSignal(str)
    rename_requested = pyqtSignal(str, str)
    delete_requested = pyqtSignal(str)

    def __init__(self, info: ChannelInfo):
        super().__init__()
        self.setObjectName("ChannelStrip")
        self.sink_name = info.sink_name
        self.is_system = info.is_system
        self._current_name = info.name
        self._last_volume = info.volume
        self._dragging = False
        self._last_user_change = 0.0
        self._pending_volume: Optional[int] = None
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Expanding)
        self.setMinimumHeight(STRIP_MIN_H)
        self._build_ui(info)
        self._apply_dynamic_width(info.name)

    def _compute_width(self, name: str) -> int:
        fm = self.lbl_name.fontMetrics()
        text_w = fm.horizontalAdvance(name)
        buttons_w = 0 if self.is_system else 50
        return max(STRIP_MIN_W, min(STRIP_MAX_W, text_w + 24 + buttons_w + 12))

    def _apply_dynamic_width(self, name: str):
        w = self._compute_width(name)
        self.setFixedWidth(w)
        fm = self.lbl_name.fontMetrics()
        buttons_w = 0 if self.is_system else 50
        avail = w - 24 - buttons_w - 4
        self.lbl_name.setText(fm.elidedText(name, Qt.TextElideMode.ElideRight, avail))

    def _build_ui(self, info):
        root = QVBoxLayout(self); root.setContentsMargins(12, 14, 12, 14); root.setSpacing(8)
        header_wrap = QWidget()
        header_wrap.setFixedHeight(STRIP_HEADER_H)
        header_wrap.setStyleSheet("background: transparent;")
        header = QHBoxLayout(header_wrap)
        header.setContentsMargins(0, 0, 0, 0); header.setSpacing(4)

        self.lbl_name = QLabel(info.name)
        self.lbl_name.setProperty("system", info.is_system)
        self.lbl_name.setToolTip(info.name)
        self.lbl_name.setAlignment(Qt.AlignmentFlag.AlignCenter)

        if not self.is_system:
            header.addStretch(1)
            header.addWidget(self.lbl_name)
            header.addStretch(1)
            b1 = QPushButton("✎"); b1.setObjectName("IconBtn"); b1.setFixedSize(22, 22)
            b1.clicked.connect(self._ask_rename); header.addWidget(b1)
            b2 = QPushButton("×"); b2.setObjectName("IconBtnDanger"); b2.setFixedSize(22, 22)
            b2.clicked.connect(self._ask_delete); header.addWidget(b2)
        else:
            header.addWidget(self.lbl_name, 1)
        root.addWidget(header_wrap)

        line = QFrame(); line.setFrameShape(QFrame.Shape.HLine)
        line.setStyleSheet(f"background-color: {BORDER};"); line.setFixedHeight(1)
        root.addWidget(line)

        fader_area = QWidget(); fader_area.setObjectName("FaderContainer")
        fader_area.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)
        fl = QHBoxLayout(fader_area); fl.setContentsMargins(0, 5, 0, 5); fl.setSpacing(10)
        fl.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.fader = QSlider(Qt.Orientation.Vertical)
        self.fader.setObjectName("Fader")
        self.fader.setRange(0, 100)
        self.fader.setValue(info.volume)
        self.fader.setInvertedAppearance(False)
        self.fader.setFixedWidth(24)
        self.fader.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Expanding)
        self.fader.sliderPressed.connect(lambda: setattr(self, '_dragging', True))
        self.fader.sliderReleased.connect(self._on_slider_released)
        self.fader.valueChanged.connect(self._on_slider_moved)

        self.peak_meter = PeakMeter()
        fl.addWidget(self.fader); fl.addWidget(self.peak_meter)
        root.addWidget(fader_area, 1)

        self.lbl_vol = QLabel(f"{info.volume}%")
        self.lbl_vol.setObjectName("VolumeValue")
        self.lbl_vol.setAlignment(Qt.AlignmentFlag.AlignCenter)
        root.addWidget(self.lbl_vol)

        self.btn_mute = QPushButton("MUTE"); self.btn_mute.setObjectName("MuteBtn")
        self.btn_mute.setCheckable(True); self.btn_mute.setChecked(info.mute)
        self.btn_mute.setFixedHeight(32)
        self.btn_mute.clicked.connect(lambda: self.mute_toggled.emit(self.sink_name))
        root.addWidget(self.btn_mute)

        self.update_state(info)

    def set_peak(self, level: float):
        self.peak_meter.set_level(level)

    def _on_slider_released(self):
        self._dragging = False; self._last_user_change = time.time()

    def _on_slider_moved(self, value):
        if value != self._last_volume:
            self._last_volume = value
            self._last_user_change = time.time()
            self._pending_volume = value
            self.lbl_vol.setText(f"{value}%")
            self.volume_changed.emit(self.sink_name, value)

    def _ask_rename(self):
        name, ok = QInputDialog.getText(self, "Renombrar", "Nuevo nombre:",
                                        text=self.lbl_name.toolTip())
        if ok and name.strip():
            self.rename_requested.emit(self.sink_name, name.strip())

    def _ask_delete(self):
        dlg = DeleteConfirmDialog(self._current_name, self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self.delete_requested.emit(self.sink_name)

    def update_state(self, info: ChannelInfo):
        if self._current_name != info.name:
            self._current_name = info.name
            self._apply_dynamic_width(info.name)
            self.lbl_name.setToolTip(info.name)
        if self._pending_volume is not None:
            if abs(info.volume - self._pending_volume) <= 1:
                self._pending_volume = None
            else:
                self.btn_mute.blockSignals(True)
                self.btn_mute.setChecked(info.mute)
                self.btn_mute.setText("MUTED" if info.mute else "MUTE")
                self.btn_mute.blockSignals(False)
                return
        now = time.time()
        if not self._dragging and (now - self._last_user_change) > 1.0:
            if self.fader.value() != info.volume:
                self.fader.blockSignals(True)
                self.fader.setValue(info.volume)
                self.fader.blockSignals(False)
                self.lbl_vol.setText(f"{info.volume}%")
                self._last_volume = info.volume
        self.btn_mute.blockSignals(True)
        self.btn_mute.setChecked(info.mute)
        self.btn_mute.setText("MUTED" if info.mute else "MUTE")
        self.btn_mute.blockSignals(False)

# ======================================================================
# DELETE CONFIRM DIALOG
# ======================================================================
class DeleteConfirmDialog(QDialog):
    def __init__(self, channel_name: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Confirmar borrado")
        self.setModal(True); self.setFixedWidth(420)
        self._channel_name = channel_name
        l = QVBoxLayout(self); l.setContentsMargins(24, 24, 24, 24); l.setSpacing(14)
        title = QLabel(f"<b>¿Borrar el canal «{channel_name}»?</b>")
        title.setStyleSheet(f"color: {TEXT_MAIN}; font-size: 12pt;")
        title.setWordWrap(True); l.addWidget(title)
        warn = QLabel(f"Todas las aplicaciones asignadas a este canal se moverán "
                      f"a <b>System</b>. Esta acción no se puede deshacer.")
        warn.setObjectName("DangerWarn"); warn.setWordWrap(True); l.addWidget(warn)
        help_lbl = QLabel(f"Escribe «<b>{channel_name}</b>» para confirmar:")
        help_lbl.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 10pt;")
        help_lbl.setWordWrap(True); l.addWidget(help_lbl)
        self.edit = QLineEdit(); self.edit.setPlaceholderText(channel_name)
        self.edit.textChanged.connect(self._on_text_changed)
        self.edit.returnPressed.connect(self._on_return)
        l.addWidget(self.edit)
        bb = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok |
                              QDialogButtonBox.StandardButton.Cancel)
        self._ok_btn = bb.button(QDialogButtonBox.StandardButton.Ok)
        self._ok_btn.setObjectName("DangerBtn")
        self._ok_btn.setText("Borrar"); self._ok_btn.setEnabled(False)
        bb.accepted.connect(self.accept); bb.rejected.connect(self.reject)
        l.addWidget(bb)

    def _on_text_changed(self, text):
        self._ok_btn.setEnabled(text.strip() == self._channel_name)

    def _on_return(self):
        if self._ok_btn.isEnabled(): self.accept()

# ======================================================================
# ADD CHANNEL DIALOG
# ======================================================================
class AddChannelDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Nuevo Canal"); self.setModal(True); self.setFixedWidth(380)
        l = QVBoxLayout(self); l.setContentsMargins(24, 24, 24, 24); l.setSpacing(16)
        lbl = QLabel("Nombre del nuevo canal:")
        lbl.setStyleSheet(f"font-weight: 700; color: {TEXT_MAIN};")
        l.addWidget(lbl)
        self.edit = QLineEdit()
        self.edit.setPlaceholderText("Ej: Spotify, Discord, Navegador...")
        self.edit.returnPressed.connect(self.accept)
        l.addWidget(self.edit)
        bb = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok |
                              QDialogButtonBox.StandardButton.Cancel)
        bb.button(QDialogButtonBox.StandardButton.Ok).setObjectName("PrimaryBtn")
        bb.accepted.connect(self.accept); bb.rejected.connect(self.reject)
        l.addWidget(bb)
    def get_name(self): return self.edit.text().strip()

# ======================================================================
# CHANNELS PAGE
# ======================================================================
class ChannelsPage(QWidget):
    add_channel_requested = pyqtSignal(str)
    def __init__(self, worker):
        super().__init__()
        self.worker = worker
        self.strips: Dict[str, ChannelStrip] = {}
        self._build_ui()

    def _build_ui(self):
        l = QVBoxLayout(self); l.setContentsMargins(30, 30, 30, 30); l.setSpacing(20)
        header = QHBoxLayout()
        t = QLabel("Mezclador de Canales"); t.setObjectName("PageTitle")
        header.addWidget(t); header.addStretch()
        b = QPushButton("+ Añadir Canal"); b.setObjectName("PrimaryBtn")
        b.setCursor(Qt.CursorShape.PointingHandCursor)
        b.clicked.connect(self._on_add); header.addWidget(b)
        l.addLayout(header)
        scroll = QScrollArea(); scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        container = QWidget()
        container.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.grid = QHBoxLayout(container)
        self.grid.setSpacing(16); self.grid.setContentsMargins(0, 0, 0, 0)
        self.btn_add_strip = QPushButton("+")
        self.btn_add_strip.setObjectName("AddStripBtn")
        self.btn_add_strip.setFixedWidth(STRIP_MIN_W)
        self.btn_add_strip.setMinimumHeight(STRIP_MIN_H)
        self.btn_add_strip.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Expanding)
        self.btn_add_strip.clicked.connect(self._on_add)
        self.grid.addWidget(self.btn_add_strip)
        self.grid.addStretch(1)
        scroll.setWidget(container)
        l.addWidget(scroll, 1)

    def _on_add(self):
        d = AddChannelDialog(self)
        if d.exec() == QDialog.DialogCode.Accepted:
            n = d.get_name()
            if n: self.add_channel_requested.emit(n)

    @pyqtSlot(object)
    def on_state_updated(self, state):
        current = set(state.channels.keys())
        existing = set(self.strips.keys())
        for sn in existing - current:
            w = self.strips.pop(sn); w.setParent(None); w.deleteLater()
        ordered = sorted(current, key=lambda sn: (
            not state.channels[sn].is_system,
            state.channels[sn].name.lower()))
        current_order = []
        for i in range(self.grid.count()):
            it = self.grid.itemAt(i)
            if it is None: continue
            w = it.widget()
            if w is None or w is self.btn_add_strip: continue
            if hasattr(w, 'sink_name'): current_order.append(w.sink_name)
        if current_order != ordered:
            while self.grid.count() > 0:
                it = self.grid.takeAt(0)
                if it is None: continue
                w = it.widget()
                if w is not None and w is not self.btn_add_strip:
                    w.setParent(None)
            for sn in ordered:
                if sn not in self.strips:
                    info = state.channels[sn]
                    strip = ChannelStrip(info)
                    strip.volume_changed.connect(self.worker.set_volume)
                    strip.mute_toggled.connect(self.worker.toggle_mute)
                    strip.rename_requested.connect(self.worker.rename_channel)
                    strip.delete_requested.connect(self.worker.remove_channel)
                    self.strips[sn] = strip
                self.grid.addWidget(self.strips[sn])
            self.grid.addWidget(self.btn_add_strip)
            self.grid.addStretch(1)
        for sn in ordered:
            if sn in self.strips:
                self.strips[sn].update_state(state.channels[sn])

    @pyqtSlot(dict)
    def on_peaks_updated(self, peaks: dict):
        for sn, level in peaks.items():
            strip = self.strips.get(sn)
            if strip: strip.set_peak(level)

# ======================================================================
# APPS PAGE
# ======================================================================
class ProcessTable(QTableWidget):
    move_requested = pyqtSignal(int, str)

    def __init__(self):
        super().__init__()
        self._icon_cache: Dict[str, QIcon] = {}

        self.setColumnCount(3)
        self.setHorizontalHeaderLabels(["", "APLICACIÓN", "CANAL DE AUDIO"])
        self.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        self.setColumnWidth(0, 44)
        self.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        self.setColumnWidth(2, 280)

        self.setIconSize(QSize(24, 24))
        self.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.setShowGrid(False)
        self.verticalHeader().setVisible(False)
        self.verticalHeader().setDefaultSectionSize(ROW_HEIGHT)
        self.verticalHeader().setMinimumSectionSize(ROW_HEIGHT)
        self.horizontalHeader().setFixedHeight(44)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.setHorizontalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        self.setVerticalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        self.rows_map: Dict[int, int] = {}
        self.combos: Dict[int, QComboBox] = {}

    def _get_icon_for(self, binary: str, icon_name: str) -> QIcon:
        key = binary or icon_name or "?"
        if key in self._icon_cache:
            return self._icon_cache[key]
        candidates = []
        if icon_name: candidates.append(icon_name)
        if binary: candidates.append(binary)
        candidates += ["application-x-executable", "application-default-icon"]
        for c in candidates:
            ic = QIcon.fromTheme(c)
            if not ic.isNull():
                self._icon_cache[key] = ic
                return ic
        self._icon_cache[key] = QIcon()
        return QIcon()

    def update_state(self, state):
        current = {p.index for p in state.processes}
        existing = set(self.rows_map.keys())
        for idx in existing - current:
            row = self.rows_map.pop(idx)
            self.removeRow(row); self.combos.pop(idx, None)
        self.rows_map = {}
        for r in range(self.rowCount()):
            it = self.item(r, 0)
            if it is not None:
                si = it.data(Qt.ItemDataRole.UserRole)
                if si is not None: self.rows_map[si] = r
        ch_map = {sn: ci.name for sn, ci in state.channels.items()}
        for proc in state.processes:
            row = self.rows_map.get(proc.index)
            if row is None:
                row = self.rowCount(); self.insertRow(row)
                self.rows_map[proc.index] = row
                self._setup_row(row, proc.index, ch_map)
            self._update_row(row, proc, ch_map)

    def _setup_row(self, row, si_index, ch_map):
        it0 = QTableWidgetItem()
        it0.setData(Qt.ItemDataRole.UserRole, si_index)
        it0.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
        self.setItem(row, 0, it0)

        it1 = QTableWidgetItem()
        it1.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
        f = it1.font(); f.setBold(True); it1.setFont(f)
        self.setItem(row, 1, it1)

        combo = QComboBox()
        combo.setProperty("si_index", si_index)
        for sn, name in ch_map.items(): combo.addItem(name, sn)
        combo.setMinimumHeight(32); combo.setMaximumHeight(34)
        combo.currentIndexChanged.connect(self._on_combo_changed)
        self.setCellWidget(row, 2, combo)
        self.combos[si_index] = combo

    def _update_row(self, row, proc, ch_map):
        icon = self._get_icon_for(proc.binary, proc.icon_name)
        self.item(row, 0).setIcon(icon)
        self.item(row, 0).setToolTip(proc.name)

        pretty = pretty_app_name(proc.binary, proc.name)
        self.item(row, 1).setText(pretty)
        self.item(row, 1).setToolTip(proc.binary or proc.name)

        combo = self.combos.get(proc.index)
        if combo is not None:
            current_keys = [combo.itemData(i) for i in range(combo.count())]
            new_keys = list(ch_map.keys())
            if current_keys != new_keys:
                combo.blockSignals(True); combo.clear()
                for sn, name in ch_map.items(): combo.addItem(name, sn)
                combo.blockSignals(False)
            target = proc.current_channel_sink_name
            if target not in ch_map: target = combo.currentData()
            t_idx = combo.findData(target)
            if t_idx >= 0 and t_idx != combo.currentIndex():
                combo.blockSignals(True); combo.setCurrentIndex(t_idx); combo.blockSignals(False)

    def _on_combo_changed(self, idx):
        combo = self.sender()
        if combo is None: return
        si = combo.property("si_index")
        sn = combo.itemData(idx)
        if si is not None and sn: self.move_requested.emit(si, sn)

class AppsPage(QWidget):
    def __init__(self, worker):
        super().__init__()
        self.worker = worker
        l = QVBoxLayout(self); l.setContentsMargins(30, 30, 30, 30); l.setSpacing(20)
        h = QHBoxLayout()
        t = QLabel("Aplicaciones"); t.setObjectName("PageTitle")
        h.addWidget(t); h.addStretch()
        hint = QLabel("Cambia el canal de cada app desde el desplegable")
        hint.setObjectName("SubTitle"); h.addWidget(hint)
        l.addLayout(h)
        self.table = ProcessTable()
        self.table.move_requested.connect(self.worker.move_sink_input)
        l.addWidget(self.table, 1)

    @pyqtSlot(object)
    def on_state_updated(self, state):
        self.table.update_state(state)

# ======================================================================
# OUTPUT PAGE
# ======================================================================
class OutputPage(QWidget):
    set_output_requested = pyqtSignal(str)
    def __init__(self, worker):
        super().__init__()
        self.worker = worker
        l = QVBoxLayout(self); l.setContentsMargins(40, 40, 40, 40); l.setSpacing(24)
        l.setAlignment(Qt.AlignmentFlag.AlignTop)
        t = QLabel("Salida Maestra (Hardware)"); t.setObjectName("PageTitle"); l.addWidget(t)
        s = QLabel("Selecciona el dispositivo físico. Solo hay que configurarlo una vez.")
        s.setObjectName("SubTitle"); s.setWordWrap(True); l.addWidget(s)
        self.combo = QComboBox(); self.combo.setFixedHeight(46)
        self.combo.setStyleSheet(
            f"font-size: 11pt; font-weight: bold; background-color: {PANEL_BG};")
        self.combo.currentIndexChanged.connect(self._on_change)
        l.addWidget(self.combo)
        info = QFrame(); info.setObjectName("ChannelStrip")
        il = QVBoxLayout(info); il.setContentsMargins(24, 20, 24, 20)
        lab = QLabel("ℹ️  Asigna cada app a un canal desde la pestaña Aplicaciones.")
        lab.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 10pt; line-height: 1.4;")
        lab.setWordWrap(True); il.addWidget(lab)
        l.addWidget(info); l.addStretch()

    @pyqtSlot(object)
    def on_state_updated(self, state):
        self.combo.blockSignals(True)
        cd = self.combo.currentData(); self.combo.clear()
        for s in state.physical_sinks:
            self.combo.addItem(s["description"], s["name"])
        idx = self.combo.findData(state.current_output_sink)
        if idx < 0 and cd: idx = self.combo.findData(cd)
        if idx >= 0: self.combo.setCurrentIndex(idx)
        elif self.combo.count() > 0: self.combo.setCurrentIndex(0)
        self.combo.blockSignals(False)

    def _on_change(self, idx):
        if idx >= 0: self.set_output_requested.emit(self.combo.itemData(idx))

# ======================================================================
# SETTINGS PAGE
# ======================================================================
class SettingsPage(QWidget):
    def __init__(self):
        super().__init__()
        self._build_ui()

    def _build_ui(self):
        l = QVBoxLayout(self); l.setContentsMargins(40, 40, 40, 40); l.setSpacing(20)
        l.setAlignment(Qt.AlignmentFlag.AlignTop)
        t = QLabel("Ajustes"); t.setObjectName("PageTitle"); l.addWidget(t)
        card = QFrame(); card.setObjectName("ChannelStrip")
        cl = QVBoxLayout(card); cl.setContentsMargins(24, 20, 24, 20); cl.setSpacing(8)
        lbl_title = QLabel("Iniciar con el sistema"); lbl_title.setObjectName("SettingLabel")
        cl.addWidget(lbl_title)
        lbl_hint = QLabel("Si se activa, KORVEX Stream Deck se lanzará al iniciar sesión "
                          "(crea un .desktop en ~/.config/autostart).")
        lbl_hint.setObjectName("SettingHint"); lbl_hint.setWordWrap(True)
        cl.addWidget(lbl_hint)
        self.chk_autostart = QCheckBox("Activar autostart")
        self.chk_autostart.setChecked(is_autostart_enabled())
        self.chk_autostart.stateChanged.connect(self._on_autostart_toggled)
        cl.addWidget(self.chk_autostart)
        l.addWidget(card)
        l.addStretch()

    def _on_autostart_toggled(self, state):
        enabled = (state == Qt.CheckState.Checked.value) or (state == 2)
        if enabled:
            if not enable_autostart():
                QMessageBox.warning(self, "Error", "No se pudo activar el autostart.")
                self.chk_autostart.blockSignals(True)
                self.chk_autostart.setChecked(False)
                self.chk_autostart.blockSignals(False)
        else:
            if not disable_autostart():
                QMessageBox.warning(self, "Error", "No se pudo desactivar el autostart.")
                self.chk_autostart.blockSignals(True)
                self.chk_autostart.setChecked(True)
                self.chk_autostart.blockSignals(False)

# ======================================================================
# MAIN WINDOW
# ======================================================================
class MainWindow(QMainWindow):
    shutdown_requested = pyqtSignal()
    def __init__(self):
        super().__init__()
        self.setWindowTitle("KORVEX Stream Deck")
        self.resize(1400, 780); self.setMinimumSize(1150, 650)

        self._app_icon = _get_app_icon()
        if not self._app_icon.isNull():
            self.setWindowIcon(self._app_icon)

        self.config_dir = os.path.expanduser("~/.config/korvex-streamdeck")
        self.thread = QThread()
        self.worker = AudioWorker(self.config_dir)
        self.worker.moveToThread(self.thread)
        central = QWidget(); self.setCentralWidget(central)
        ml = QHBoxLayout(central); ml.setContentsMargins(0, 0, 0, 0); ml.setSpacing(0)
        self.sidebar = QListWidget(); self.sidebar.setObjectName("SideBar")
        self.sidebar.setFixedWidth(240)
        for label in ("🎚️  Mezclador", "🎛️  Aplicaciones", "🎧  Salida Maestra",
                      "⚙️  Ajustes"):
            self.sidebar.addItem(QListWidgetItem(label))
        self.sidebar.setCurrentRow(0)
        ml.addWidget(self.sidebar)
        self.stack = QStackedWidget()
        self.channels_page = ChannelsPage(self.worker)
        self.apps_page = AppsPage(self.worker)
        self.output_page = OutputPage(self.worker)
        self.settings_page = SettingsPage()
        self.stack.addWidget(self.channels_page)
        self.stack.addWidget(self.apps_page)
        self.stack.addWidget(self.output_page)
        self.stack.addWidget(self.settings_page)
        ml.addWidget(self.stack)
        self.sidebar.currentRowChanged.connect(self.stack.setCurrentIndex)

        self.worker.state_updated.connect(self.channels_page.on_state_updated)
        self.worker.state_updated.connect(self.apps_page.on_state_updated)
        self.worker.state_updated.connect(self.output_page.on_state_updated)
        self.worker.peaks_updated.connect(self.channels_page.on_peaks_updated)

        self.worker.error_occurred.connect(lambda m: log("SIGNAL", m))
        self.worker.operation_finished.connect(self._on_op_finished)
        self.worker.finished.connect(lambda: log("WORKER", "finished"))
        self.shutdown_requested.connect(self.worker.stop)
        self.channels_page.add_channel_requested.connect(self.worker.add_channel)
        self.output_page.set_output_requested.connect(self.worker.set_output_sink)
        self.thread.started.connect(self.worker.start)
        self.thread.start()

    def _on_op_finished(self, success, msg):
        if not success: QMessageBox.warning(self, "Error", msg)

    def closeEvent(self, event):
        self.hide()
        self.shutdown_requested.emit()
        if self.thread.isRunning():
            self.thread.quit(); self.thread.wait(2000)
        event.accept()

# ======================================================================
# ENTRY
# ======================================================================
def main():
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
    app = QApplication(sys.argv)
    app.setApplicationName("KORVEX Stream Deck")

    icon = _get_app_icon()
    if not icon.isNull():
        app.setWindowIcon(icon)

    app.setStyleSheet(STYLESHEET)
    try:
        with pulsectl.Pulse('korvex-check') as p: p.server_info()
    except Exception as e:
        QMessageBox.critical(None, "Error", f"No se pudo conectar a PulseAudio:\n{e}")
        sys.exit(1)
    w = MainWindow(); w.show(); sys.exit(app.exec())

if __name__ == "__main__":
    main()