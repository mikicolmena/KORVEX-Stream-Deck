#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
import json
import re
import time
import threading
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field

import pulsectl
from pulsectl import PulseError
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QSlider, QPushButton, QScrollArea, QFrame, QComboBox, QTabWidget,
    QMessageBox, QLineEdit, QDialog, QDialogButtonBox, QInputDialog,
    QProgressBar
)
from PyQt6.QtCore import (
    Qt, QTimer, pyqtSignal, QObject, QThread, pyqtSlot, QEventLoop
)

# ----------------------------------------------------------------------
# ESTILO GLOBAL (QSS)
# ----------------------------------------------------------------------
STYLESHEET = """
QMainWindow { background-color: #1e1e1e; }
QWidget { background-color: #1e1e1e; color: #ffffff; font-family: 'Segoe UI', 'Noto Sans', sans-serif; font-size: 13px; }
QTabWidget::pane { border: 1px solid #3e3e42; border-radius: 6px; background: #252526; }
QTabBar::tab { background: #2d2d30; color: #aaa; padding: 10px 20px; border-top-left-radius: 6px; border-top-right-radius: 6px; margin-right: 2px; min-width: 120px; }
QTabBar::tab:selected { background: #3e3e42; color: #00aaff; font-weight: 600; border-bottom: 2px solid #00aaff; }
QTabBar::tab:hover:!selected { background: #333; color: #ddd; }
QPushButton { background-color: #333; color: white; padding: 8px 16px; border-radius: 5px; font-weight: 600; border: 1px solid #444; }
QPushButton:hover { background-color: #444; border-color: #555; }
QPushButton:pressed { background-color: #007acc; border-color: #0099ff; }
QPushButton:disabled { background-color: #252526; color: #666; border-color: #333; }
QPushButton#addChannelBtn { background-color: #007acc; border-color: #0099ff; padding: 8px; font-size: 18px; min-width: 40px; max-width: 40px; border-radius: 6px; }
QPushButton#addChannelBtn:hover { background-color: #0099ff; }
QPushButton#deleteBtn, QPushButton#renameBtn { background-color: transparent; border: none; padding: 4px; min-width: 28px; max-width: 28px; font-size: 14px; }
QPushButton#deleteBtn:hover { background-color: #c0392b; border-radius: 4px; color: white; }
QPushButton#renameBtn:hover { background-color: #555; border-radius: 4px; color: white; }
QPushButton#muteBtn { border: none; background: transparent; padding: 5px; font-size: 16px; min-width: 36px; }
QPushButton#muteBtn:hover { background-color: #3e3e42; border-radius: 4px; }
QComboBox { background: #2d2d30; border: 1px solid #3e3e42; padding: 6px 10px; color: white; min-height: 28px; border-radius: 4px; }
QComboBox:hover { border-color: #007acc; }
QComboBox::drop-down { border: none; width: 24px; subcontrol-origin: padding; subcontrol-position: top right; }
QComboBox::down-arrow { image: url(data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIxMiIgaGVpZ2h0PSIxMiIgdmlld0JveD0iMCAwIDI0IDI0IiBmaWxsPSJub25lIiBzdHJva2U9IiNjY2MiIHN0cm9rZS13aWR0aD0iMiIgc3Ryb2tlLWxpbmVjYXA9InJvdW5kIiBzdHJva2UtbGluZWpvaW49InJvdW5kIj48cG9seWxpbmUgcG9pbnRzPSI2IDkgMTIgMTUgMTggOSI+PC9wb2x5bGluZT48L3N2Zz4=); width: 12px; height: 12px; }
QComboBox QAbstractItemView { background: #2d2d30; border: 1px solid #3e3e42; selection-background-color: #007acc; color: white; padding: 4px; }
QSlider::groove:horizontal { border: 1px solid #3e3e42; height: 8px; background: #252526; margin: 2px 0; border-radius: 4px; }
QSlider::handle:horizontal { background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #00aaff, stop:1 #007acc); border: 1px solid #007acc; width: 18px; height: 18px; margin: -6px 0; border-radius: 9px; }
QSlider::handle:horizontal:hover { background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #00ccff, stop:1 #0099ff); }
QSlider::sub-page:horizontal { background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #007acc, stop:1 #00aaff); border: 1px solid #3e3e42; height: 8px; border-radius: 4px; }
QScrollArea { border: none; background: transparent; }
QScrollBar:vertical { border: none; background: #1e1e1e; width: 8px; border-radius: 4px; margin: 0px; }
QScrollBar::handle:vertical { background: #444; min-height: 30px; border-radius: 4px; }
QScrollBar::handle:vertical:hover { background: #00aaff; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0px; }
QScrollBar:horizontal { border: none; background: #252526; height: 8px; border-radius: 4px; }
QScrollBar::handle:horizontal { background: #444; min-width: 20px; border-radius: 4px; }
QScrollBar::handle:horizontal:hover { background: #00aaff; }
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal { width: 0px; }
QFrame#channelCard { background: #252526; border: 1px solid #3e3e42; border-radius: 8px; }
QFrame#channelCard:hover { border-color: #4a4a4f; }
QLabel#channelName { font-weight: bold; font-size: 14px; color: #fff; padding-bottom: 4px; }
QLabel#volumeLabel { color: #00aaff; font-weight: bold; font-size: 13px; min-width: 45px; text-align: right; }
QLabel#processName { color: #ddd; font-weight: 500; }
QLabel#processBinary { color: #888; font-size: 11px; }
QLineEdit { background: #2d2d30; border: 1px solid #3e3e42; padding: 8px; color: white; border-radius: 4px; }
QLineEdit:focus { border-color: #007acc; }
QDialog { background-color: #1e1e1e; }
QMessageBox { background-color: #252526; }
QMessageBox QLabel { color: white; }
QMessageBox QPushButton { min-width: 80px; }
"""

# ----------------------------------------------------------------------
# DATACLASSES
# ----------------------------------------------------------------------
@dataclass
class ChannelInfo:
    sink_name: str
    name: str
    sink_index: int
    volume: int = 0
    mute: bool = False
    peak: float = 0.0

@dataclass
class ProcessInfo:
    index: int
    name: str
    binary: str
    current_channel_sink_name: str
    volume: int = 0
    mute: bool = False

@dataclass
class AppState:
    channels: Dict[str, ChannelInfo] = field(default_factory=dict)
    processes: List[ProcessInfo] = field(default_factory=list)
    physical_sinks: List[Dict[str, str]] = field(default_factory=list)
    current_output_sink: str = ""
    system_channel_sink_name: str = ""

# ----------------------------------------------------------------------
# UTILIDADES
# ----------------------------------------------------------------------
def slugify(text: str) -> str:
    text = text.strip().lower()
    text = re.sub(r'[^\w\s-]', '', text, flags=re.UNICODE)
    text = re.sub(r'[-\s]+', '_', text)
    return text[:50]

def generate_sink_name(base_name: str) -> str:
    return f"korvex_ch_{slugify(base_name)}"

def parse_module_args(args_str: str) -> Dict[str, str]:
    res = {}
    for match in re.finditer(r'(\w+)=("([^"]*)"|(\S+))', args_str or ""):
        key = match.group(1)
        val = match.group(3) if match.group(3) is not None else match.group(4)
        res[key] = val
    return res

# ----------------------------------------------------------------------
# AUDIO WORKER
# ----------------------------------------------------------------------
class AudioWorker(QObject):
    state_updated = pyqtSignal(object)
    error_occurred = pyqtSignal(str)
    operation_finished = pyqtSignal(bool, str)
    finished = pyqtSignal()

    MASTER_SINK_NAME = "korvex_master"
    CHANNEL_PREFIX = "korvex_ch_"
    SYSTEM_CHANNEL_KEY = "System"

    def __init__(self, config_path: str):
        super().__init__()
        self.config_path = config_path
        self.config = self._load_config()
        self.pulse: Optional[pulsectl.Pulse] = None
        
        self._running = False
        self._stopping = False          # NUEVO: Flag para abortar reconexión durante cierre
        self._reconnecting = False
        self._reconnect_attempts = 0
        self._reconnect_timer: Optional[QTimer] = None # NUEVO: Objeto QTimer real para cancelación
        self._ops_lock = threading.Lock()

        self._master_sink_mod_id: Optional[int] = None
        self._system_sink_mod_id: Optional[int] = None
        self._channel_sink_mod_ids: Dict[str, int] = {}
        self._channel_lb_mod_ids: Dict[str, int] = {}
        self._master_out_lb_mod_id: Optional[int] = None
        self._original_default_sink_name: Optional[str] = None

        self._poll_timer = QTimer(self)
        self._poll_timer.setInterval(1000)
        self._poll_timer.timeout.connect(self._poll_loop)

    # -------------------- LIFECYCLE --------------------
    @pyqtSlot()
    def start(self):
        if self._running: return
        try:
            self.pulse = pulsectl.Pulse('korvex-worker')
            self._original_default_sink_name = self.pulse.server_info().default_sink_name
            print(f"[Korvex] Default sink original: {self._original_default_sink_name}")
            self._cleanup_ghost_modules()
            self._ensure_audio_graph()
            self._running = True
            self._stopping = False
            self._reconnecting = False
            self._reconnect_attempts = 0
            self._poll_timer.start()
            self._poll_loop()
        except Exception as e:
            self.error_occurred.emit(f"Fatal Audio Error: {e}")
            self.finished.emit()

    @pyqtSlot()
    def stop(self):
        print("[Korvex] Stop requested (worker thread).")
        self._stopping = True
        self._running = False
        self._poll_timer.stop()

        # 1. Cancelar timer de reconexión pendiente (CORREGIDO PyQt6)
        if self._reconnect_timer:
            self._reconnect_timer.stop()
            self._reconnect_timer.deleteLater()
            self._reconnect_timer = None

        # 2. Esperar lock (max 1.0s)
        acquired = self._ops_lock.acquire(timeout=1.0)
        if not acquired:
            print("[Korvex] CRITICAL: Could not acquire lock on stop. Forcing cleanup.")

        if not self.pulse:
            if acquired: self._ops_lock.release()
            self.finished.emit()
            return

        try:
            # Restaurar Default Sink
            if self._original_default_sink_name:
                try:
                    sinks = {s.name: s for s in self.pulse.sink_list()}
                    target = self._original_default_sink_name
                    if target not in sinks:
                        physical = [s for s in sinks.values() if not s.name.startswith(self.CHANNEL_PREFIX) and s.name != self.MASTER_SINK_NAME]
                        if physical: target = physical[0].name
                    self.pulse.set_default_sink(target)
                    print(f"[Korvex] Default sink restaurado: {target}")
                except Exception as e: print(f"[Korvex] Error restaurando default: {e}")

            # Mover huérfanos
            real_idx = self._get_sink_index(self._original_default_sink_name or "")
            if real_idx is None:
                physical = [s for s in self.pulse.sink_list() if not s.name.startswith(self.CHANNEL_PREFIX) and s.name != self.MASTER_SINK_NAME]
                if physical: real_idx = physical[0].index

            if real_idx is not None:
                our_sinks = set(self._channel_sink_mod_ids.keys()) | {self.MASTER_SINK_NAME, f"{self.CHANNEL_PREFIX}system"}
                for si in self.pulse.sink_input_list():
                    if si.name.startswith("Loopback from"): continue
                    try:
                        sink_obj = self.pulse.sink_info(si.sink)
                        if sink_obj.name in our_sinks:
                            self.pulse.move_sink_input(si.index, real_idx)
                    except: pass

            self._unload_tracked_modules()

        except Exception as e:
            print(f"[Korvex] Error en stop: {e}")
        finally:
            try:
                if self.pulse: self.pulse.close()
            except: pass
            self.pulse = None
            if acquired: self._ops_lock.release()
            print("[Korvex] Worker stopped cleanly.")
            self.finished.emit()

    # -------------------- PULSE GRAPH MANAGEMENT --------------------
    def _load_module_tracked(self, module_name: str, args: str) -> Optional[int]:
        if not self.pulse: return None
        try: return self.pulse.module_load(module_name, args)
        except Exception as e:
            self.error_occurred.emit(f"Module load failed ({module_name}): {e}")
            return None

    def _unload_module_safe(self, module_index: Optional[int]):
        if module_index is None or not self.pulse: return
        try: self.pulse.module_unload(module_index)
        except Exception as e:
            if "No such entity" not in str(e): print(f"[Korvex] Unload error {module_index}: {e}")

    def _unload_tracked_modules(self):
        print("[Korvex] Unloading tracked modules...")
        for mod_id in list(self._channel_lb_mod_ids.values()): self._unload_module_safe(mod_id)
        self._channel_lb_mod_ids.clear()
        self._unload_module_safe(self._master_out_lb_mod_id); self._master_out_lb_mod_id = None
        for mod_id in list(self._channel_sink_mod_ids.values()): self._unload_module_safe(mod_id)
        self._channel_sink_mod_ids.clear()
        self._unload_module_safe(self._system_sink_mod_id); self._system_sink_mod_id = None
        self._unload_module_safe(self._master_sink_mod_id); self._master_sink_mod_id = None

    def _sink_exists(self, name: str) -> bool:
        if not self.pulse: return False
        try: return any(s.name == name for s in self.pulse.sink_list())
        except: return False

    def _get_sink_by_name(self, name: str) -> Optional[pulsectl.PulseSinkInfo]:
        if not self.pulse: return None
        try:
            for s in self.pulse.sink_list():
                if s.name == name: return s
        except: pass
        return None

    def _get_sink_index(self, name: str) -> Optional[int]:
        s = self._get_sink_by_name(name)
        return s.index if s else None

    def _create_null_sink(self, sink_name: str, description: str) -> Optional[int]:
        if self._sink_exists(sink_name):
            sink = self._get_sink_by_name(sink_name)
            return sink.owner_module if sink else None
        args = f"sink_name={sink_name} sink_properties=device.description='{description}'"
        return self._load_module_tracked("module-null-sink", args)

    def _create_loopback(self, source: str, sink: str) -> Optional[int]:
        args = f"source={source} sink={sink} source_dont_move=true sink_dont_move=true"
        return self._load_module_tracked("module-loopback", args)

    def _ensure_audio_graph(self):
        print("[Korvex] Building/Verifying audio graph...")
        # Master
        mod_id = self._create_null_sink(self.MASTER_SINK_NAME, "KORVEX Master Mix")
        if mod_id is None: raise RuntimeError("Master Sink failed")
        self._master_sink_mod_id = mod_id

        # System Channel
        sys_sink_name = f"{self.CHANNEL_PREFIX}system"
        mod_id = self._create_null_sink(sys_sink_name, self.SYSTEM_CHANNEL_KEY)
        if mod_id is None: raise RuntimeError("System Sink failed")
        self._system_sink_mod_id = mod_id  # FIX TYPO

        # User Channels
        for ch_cfg in self.config.get("channels", []):
            name = ch_cfg["name"]
            if name == self.SYSTEM_CHANNEL_KEY: continue
            sink_name = ch_cfg.get("sink_name", generate_sink_name(name))
            if not sink_name.startswith(self.CHANNEL_PREFIX): sink_name = generate_sink_name(name)
            mod_id = self._create_null_sink(sink_name, name)
            if mod_id:
                self._channel_sink_mod_ids[sink_name] = mod_id
                for c in self.config["channels"]:
                    if c["name"] == name: c["sink_name"] = sink_name

        self._recreate_channel_loopbacks()
        self._update_output_routing()
        self._set_default_sink(sys_sink_name)

    def _recreate_channel_loopbacks(self):
        if not self.pulse: return
        for mod_id in list(self._channel_lb_mod_ids.values()): self._unload_module_safe(mod_id)
        self._channel_lb_mod_ids.clear()
        master_idx = self._get_sink_index(self.MASTER_SINK_NAME)
        if master_idx is None: return
        raw = self._get_current_channels_raw()
        for sink_name in raw.keys():
            mod_id = self._create_loopback(f"{sink_name}.monitor", self.MASTER_SINK_NAME)
            if mod_id: self._channel_lb_mod_ids[sink_name] = mod_id

    def _update_output_routing(self):
        if not self.pulse: return
        master_idx = self._get_sink_index(self.MASTER_SINK_NAME)
        if master_idx is None: return
        self._unload_module_safe(self._master_out_lb_mod_id)
        self._master_out_lb_mod_id = None
        target = self.config.get("output_sink", "")
        if not target:
            physical = self._get_physical_sinks_raw()
            if physical: target = physical[0]["name"]
        if target:
            target_idx = self._get_sink_index(target)
            if target_idx is not None:
                mod_id = self._create_loopback(f"{self.MASTER_SINK_NAME}.monitor", target)
                if mod_id:
                    self._master_out_lb_mod_id = mod_id
                    if self.config.get("output_sink") != target:
                        self.config["output_sink"] = target
                        self._save_config()

    def _set_default_sink(self, sink_name: str):
        if self.pulse:
            try: self.pulse.set_default_sink(sink_name)
            except: pass

    def _get_current_channels_raw(self) -> Dict[str, dict]:
        res = {}
        if not self.pulse: return res
        for s in self.pulse.sink_list():
            if s.name == self.MASTER_SINK_NAME: continue
            if s.name.startswith(self.CHANNEL_PREFIX):
                res[s.name] = {"sink_name": s.name, "sink_index": s.index, "description": s.description}
        return res

    def _get_physical_sinks_raw(self) -> List[Dict[str, str]]:
        if not self.pulse: return []
        return [{"name": s.name, "description": s.description}
                for s in self.pulse.sink_list()
                if not s.name.startswith(self.CHANNEL_PREFIX) and s.name != self.MASTER_SINK_NAME]

    # -------------------- POLLING & RECONNECTION --------------------
    def _poll_loop(self):
        if not self._running or self._stopping: return
        if self._reconnecting: return

        if not self._ops_lock.acquire(blocking=False):
            return # Ocupado, saltar tick

        try:
            if not self.pulse: raise PulseError("No pulse connection")
            state = self._collect_state()
            self.state_updated.emit(state)
        except (PulseError, ConnectionResetError, OSError, BrokenPipeError) as e:
            print(f"[Korvex] PulseAudio connection lost: {e}. Attempting reconnect...")
            self._ops_lock.release()
            self._handle_pulse_disconnect()
            return
        except Exception as e:
            self.error_occurred.emit(f"Poll error: {e}")
        finally:
            if self._ops_lock.locked(): self._ops_lock.release()

    def _handle_pulse_disconnect(self):
        if self._reconnecting or self._stopping: return
        self._reconnecting = True
        self._poll_timer.stop()
        
        try:
            if self.pulse: self.pulse.close()
        except: pass
        self.pulse = None

        # Reset tracking ANTES de reconstruir (evita duplicados si server no murió)
        self._master_sink_mod_id = None
        self._system_sink_mod_id = None
        self._channel_sink_mod_ids.clear()
        self._channel_lb_mod_ids.clear()
        self._master_out_lb_mod_id = None

        wait_time = min(0.5 * (2 ** self._reconnect_attempts), 30.0)
        self._reconnect_attempts += 1
        print(f"[Korvex] Reconnecting in {wait_time:.1f}s (attempt {self._reconnect_attempts})...")
        
        # CORRECCIÓN PyQt6: Usar QTimer objeto, no singleShot static (no devuelve ID)
        self._reconnect_timer = QTimer(self)
        self._reconnect_timer.setSingleShot(True)
        self._reconnect_timer.timeout.connect(self._attempt_reconnect)
        self._reconnect_timer.start(int(wait_time * 1000))

    @pyqtSlot()
    def _attempt_reconnect(self):
        self._reconnect_timer = None
        if self._stopping: 
            print("[Korvex] Stopping flag set, aborting reconnect.")
            return
            
        try:
            self.pulse = pulsectl.Pulse(f'korvex-worker-reconnect-{self._reconnect_attempts}')
            print("[Korvex] Reconnected to PulseAudio.")
            self._cleanup_ghost_modules()
            self._ensure_audio_graph()
            self._reconnecting = False
            self._reconnect_attempts = 0
            self._running = True
            self._poll_timer.start()
        except Exception as e:
            self.error_occurred.emit(f"Reconnection failed: {e}. Retrying...")
            # Reintentar
            self._reconnect_timer = QTimer(self)
            self._reconnect_timer.setSingleShot(True)
            self._reconnect_timer.timeout.connect(self._attempt_reconnect)
            self._reconnect_timer.start(1000)

    # -------------------- STATE COLLECTION --------------------
    def _collect_state(self) -> AppState:
        state = AppState()
        raw_channels = self._get_current_channels_raw()
        assignments = self.config.get("assignments", {})
        all_sinks = {s.name: s for s in self.pulse.sink_list()}

        for sink_name, info in raw_channels.items():
            vol, mute, peak = 0, False, 0.0
            try:
                v_info = self.pulse.sink_volume(info["sink_index"])
                vol = int(v_info.value_flat * 100)
                mute = self.pulse.sink_mute(info["sink_index"])
                peak = self._get_sink_peak(sink_name)
            except: pass
            ch = ChannelInfo(sink_name=sink_name, name=info["description"], sink_index=info["sink_index"], volume=vol, mute=mute, peak=peak)
            state.channels[sink_name] = ch
            if info["description"] == self.SYSTEM_CHANNEL_KEY:
                state.system_channel_sink_name = sink_name

        for si in self.pulse.sink_input_list():
            if si.name.startswith("Loopback from"): continue
            binary = si.proplist.get("application.process.binary", "") or si.proplist.get("application.name", si.name)
            ch_sink = "unknown"
            sink_obj = all_sinks.get(si.sink)
            if sink_obj and sink_obj.name in raw_channels: ch_sink = sink_obj.name
            
            p = ProcessInfo(index=si.index, name=si.name, binary=binary, current_channel_sink_name=ch_sink,
                            volume=int(si.volume.value_flat * 100) if si.volume else 0, mute=si.mute)
            state.processes.append(p)

            if binary in assignments:
                target_vis = assignments[binary]
                target_sink = next((sn for sn, ci in raw_channels.items() if ci["description"] == target_vis), None)
                if target_sink and si.sink != raw_channels[target_sink]["sink_index"]:
                    try: self.pulse.move_sink_input(si.index, raw_channels[target_sink]["sink_index"])
                    except: pass

        state.physical_sinks = self._get_physical_sinks_raw()
        state.current_output_sink = self.config.get("output_sink", "")
        return state

    def _get_sink_peak(self, sink_name: str) -> float:
        if not self.pulse: return 0.0
        monitor_name = f"{sink_name}.monitor"
        try:
            monitor_src = next((s for s in self.pulse.source_list() if s.name == monitor_name), None)
            if not monitor_src: return 0.0

            peak_val = 0.0
            for so in self.pulse.source_output_list():
                if so.source == monitor_src.index:
                    if hasattr(so, 'peak') and so.peak:
                        try: peak_val = max(peak_val, max(so.peak))
                        except: pass
            return min(1.0, peak_val)
        except Exception:
            return 0.0

    # -------------------- CONFIG --------------------
    def _load_config(self) -> dict:
        os.makedirs(self.config_path, exist_ok=True)
        fpath = os.path.join(self.config_path, "config.json")
        default = {"channels": [], "assignments": {}, "output_sink": ""}
        if os.path.exists(fpath):
            try:
                with open(fpath, "r", encoding="utf-8") as f: default.update(json.load(f))
            except: pass
        return default

    def _save_config(self):
        fpath = os.path.join(self.config_path, "config.json")
        try:
            with open(fpath, "w", encoding="utf-8") as f: json.dump(self.config, f, indent=4)
        except Exception as e: print(f"Config save error: {e}")

    # -------------------- HELPERS THREAD-SAFE --------------------
    def _try_lock_silent(self) -> bool:
        """Para operaciones de alta frecuencia (vol, mute, move). No emite señales, solo True/False."""
        if not self._running or self._reconnecting or self._stopping: return False
        return self._ops_lock.acquire(blocking=False)

    def _check_state_and_lock(self) -> bool:
        """Para operaciones estructurales (add, remove, rename). Emite error si falla."""
        if not self._running or self._reconnecting or self._stopping:
            self.operation_finished.emit(False, "Sistema no listo o reconectando")
            return False
        if not self._ops_lock.acquire(blocking=False):
            self.operation_finished.emit(False, "Sistema ocupado, intente de nuevo")
            return False
        if not self.pulse:
            self._ops_lock.release()
            self.operation_finished.emit(False, "Sin conexión de audio")
            return False
        return True

    def _release_lock(self):
        if self._ops_lock.locked(): self._ops_lock.release()

    # -------------------- PUBLIC SLOTS --------------------
    @pyqtSlot(str, int)
    def set_volume(self, sink_name: str, volume: int):
        if not self._try_lock_silent(): return
        try:
            idx = self._get_sink_index(sink_name)
            if idx is not None:
                cv = self.pulse.sink_volume(idx)
                self.pulse.sink_volume_set(idx, pulsectl.PulseVolumeInfo([volume/100.0]*len(cv.values)))
        except Exception as e: self.error_occurred.emit(f"Vol error: {e}")
        finally: self._release_lock()

    @pyqtSlot(str)
    def toggle_mute(self, sink_name: str):
        if not self._try_lock_silent(): return
        try:
            idx = self._get_sink_index(sink_name)
            if idx is not None:
                self.pulse.sink_mute(idx, not self.pulse.sink_mute(idx))
        except Exception as e: self.error_occurred.emit(f"Mute error: {e}")
        finally: self._release_lock()

    @pyqtSlot(int, str)
    def move_sink_input(self, si_index: int, target_sink_name: str):
        if not self._try_lock_silent(): return
        try:
            idx = self._get_sink_index(target_sink_name)
            if idx is not None:
                self.pulse.move_sink_input(si_index, idx)
        except Exception as e: self.error_occurred.emit(f"Move error: {e}")
        finally: self._release_lock()

    @pyqtSlot(str)
    def add_channel(self, visible_name: str):
        visible_name = visible_name.strip()
        if not visible_name:
            self.operation_finished.emit(False, "Nombre vacío"); return
        if not self._check_state_and_lock(): return
        try:
            raw = self._get_current_channels_raw()
            if any(i["description"] == visible_name for i in raw.values()):
                raise ValueError("Ya existe un canal con ese nombre")
            
            sink_name = generate_sink_name(visible_name)
            if self._sink_exists(sink_name):
                base, i = sink_name, 2
                while self._sink_exists(f"{base}_{i}"): i += 1
                sink_name = f"{base}_{i}"

            mod_id = self._create_null_sink(sink_name, visible_name)
            if mod_id is None: raise RuntimeError("No se pudo crear sink nulo")
            
            self._channel_sink_mod_ids[sink_name] = mod_id
            
            lb = self._create_loopback(f"{sink_name}.monitor", self.MASTER_SINK_NAME)
            if lb is None:
                self._unload_module_safe(mod_id)
                del self._channel_sink_mod_ids[sink_name]
                raise RuntimeError("No se pudo crear loopback a Master")
            
            self._channel_lb_mod_ids[sink_name] = lb
            
            self.config.setdefault("channels", []).append({"name": visible_name, "sink_name": sink_name})
            self._save_config()
            self.operation_finished.emit(True, "Canal creado")
        except Exception as e:
            self.operation_finished.emit(False, str(e))
        finally: self._release_lock()

    @pyqtSlot(str)
    def remove_channel(self, sink_name: str):
        if not self._check_state_and_lock(): return
        try:
            raw = self._get_current_channels_raw()
            info = raw.get(sink_name)
            if not info: raise ValueError("Canal no encontrado")
            if info["description"] == self.SYSTEM_CHANNEL_KEY:
                raise ValueError("No se puede borrar el canal System")

            sys_idx = self._get_sink_index(f"{self.CHANNEL_PREFIX}system")
            if sys_idx is not None:
                for si in self.pulse.sink_input_list():
                    if si.sink == info["sink_index"] and not si.name.startswith("Loopback from"):
                        try: self.pulse.move_sink_input(si.index, sys_idx)
                        except: pass

            self._unload_module_safe(self._channel_lb_mod_ids.pop(sink_name, None))
            self._unload_module_safe(self._channel_sink_mod_ids.pop(sink_name, None))
            
            self.config["channels"] = [c for c in self.config.get("channels", []) if c.get("sink_name") != sink_name]
            dead = info["description"]
            self.config["assignments"] = {b: c for b, c in self.config.get("assignments", {}).items() if c != dead}
            self._save_config()
            self.operation_finished.emit(True, "Canal borrado")
        except Exception as e:
            self.operation_finished.emit(False, str(e))
        finally: self._release_lock()

    @pyqtSlot(str, str)
    def rename_channel(self, old_sink_name: str, new_visible_name: str):
        new_visible_name = new_visible_name.strip()
        if not new_visible_name:
            self.operation_finished.emit(False, "Nombre vacío"); return
        if not self._check_state_and_lock(): return
        try:
            raw = self._get_current_channels_raw()
            info = raw.get(old_sink_name)
            if not info: raise ValueError("Canal no encontrado")
            if info["description"] == self.SYSTEM_CHANNEL_KEY:
                raise ValueError("No se puede renombrar el canal System")
            if info["description"] == new_visible_name: 
                self.operation_finished.emit(True, "Sin cambios")
                return
            if any(i["description"] == new_visible_name for i in raw.values()):
                raise ValueError("Ya existe un canal con ese nombre")

            self.pulse.sink_proplist_update(info["sink_index"], {"device.description": new_visible_name})
            for c in self.config.get("channels", []):
                if c.get("sink_name") == old_sink_name: c["name"] = new_visible_name
            for b, c in self.config.get("assignments", {}).items():
                if c == info["description"]: self.config["assignments"][b] = new_visible_name
            self._save_config()
            self.operation_finished.emit(True, "Renombrado")
        except Exception as e:
            self.operation_finished.emit(False, str(e))
        finally: self._release_lock()

    @pyqtSlot(str, str)
    def assign_binary(self, binary: str, target_visible_name: str):
        if not self._check_state_and_lock(): return
        try:
            raw = self._get_current_channels_raw()
            target_sink = next((sn for sn, ci in raw.items() if ci["description"] == target_visible_name), None)
            if not target_sink: raise ValueError("Canal destino no encontrado")
            
            self.config.setdefault("assignments", {})[binary] = target_visible_name
            self._save_config()
            
            target_idx = raw[target_sink]["sink_index"]
            for si in self.pulse.sink_input_list():
                b = si.proplist.get("application.process.binary", "") or si.proplist.get("application.name", "")
                if b == binary and si.sink != target_idx:
                    try: self.pulse.move_sink_input(si.index, target_idx)
                    except: pass
        except Exception as e:
            self.error_occurred.emit(f"Assign error: {e}")
        finally: self._release_lock()

    @pyqtSlot(str)
    def set_output_sink(self, sink_name: str):
        if not self._check_state_and_lock(): return
        try:
            # PROTECCIÓN: No permitir sinks virtuales ni master como salida física
            if sink_name.startswith(self.CHANNEL_PREFIX) or sink_name == self.MASTER_SINK_NAME:
                raise ValueError("No se puede enrutar la salida maestra a un canal virtual")
            
            if not self._sink_exists(sink_name):
                raise ValueError("Sink destino no existe")
            
            if self.config.get("output_sink") != sink_name:
                self.config["output_sink"] = sink_name
                self._save_config()
                self._update_output_routing()
            self.operation_finished.emit(True, "Salida actualizada")
        except Exception as e:
            self.operation_finished.emit(False, str(e))
        finally: self._release_lock()

    def _cleanup_ghost_modules(self):
        if not self.pulse: return
        print("[Korvex] Limpiando módulos fantasma...")
        try:
            for mod in self.pulse.module_list():
                args = parse_module_args(mod.argument or "")
                name = mod.name or ""
                
                sink_name = args.get("sink_name", "")
                source = args.get("source", "")
                sink = args.get("sink", "")
                
                is_our_sink = (name == "module-null-sink" and 
                               (sink_name == self.MASTER_SINK_NAME or sink_name.startswith(self.CHANNEL_PREFIX)))
                
                is_our_lb = (name == "module-loopback" and (
                    source == f"{self.MASTER_SINK_NAME}.monitor" or
                    (source.startswith(self.CHANNEL_PREFIX) and source.endswith(".monitor")) or
                    sink == self.MASTER_SINK_NAME or
                    sink.startswith(self.CHANNEL_PREFIX)
                ))

                if is_our_sink or is_our_lb:
                    print(f"[Korvex] Unload ghost: idx={mod.index} name={name}")
                    try: self.pulse.module_unload(mod.index)
                    except: pass
        except Exception as e: print(f"[Korvex] Ghost cleanup error: {e}")

# ----------------------------------------------------------------------
# WIDGETS UI
# ----------------------------------------------------------------------
class ChannelWidget(QFrame):
    volume_changed = pyqtSignal(str, int)
    mute_toggled = pyqtSignal(str)
    rename_requested = pyqtSignal(str, str)
    delete_requested = pyqtSignal(str)

    def __init__(self, ch_info: ChannelInfo, is_system: bool = False):
        super().__init__()
        self.setObjectName("channelCard")
        self.setFixedWidth(220)
        self.sink_name = ch_info.sink_name
        self.is_system = is_system
        self._build_ui(ch_info)

    def _build_ui(self, info: ChannelInfo):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(12, 12, 12, 12); lay.setSpacing(8)
        hdr = QHBoxLayout()
        self.lbl_name = QLabel(info.name); self.lbl_name.setObjectName("channelName")
        hdr.addWidget(self.lbl_name); hdr.addStretch()
        if not self.is_system:
            btn_rename = QPushButton("✏️"); btn_rename.setObjectName("renameBtn"); btn_rename.clicked.connect(self._ask_rename)
            btn_del = QPushButton("🗑️"); btn_del.setObjectName("deleteBtn"); btn_del.clicked.connect(lambda: self.delete_requested.emit(self.sink_name))
            hdr.addWidget(btn_rename); hdr.addWidget(btn_del)
        lay.addLayout(hdr)

        ctrl = QHBoxLayout()
        self.btn_mute = QPushButton(); self.btn_mute.setObjectName("muteBtn"); self.btn_mute.setCheckable(True)
        self.btn_mute.clicked.connect(lambda: self.mute_toggled.emit(self.sink_name))
        ctrl.addWidget(self.btn_mute)
        self.slider = QSlider(Qt.Orientation.Horizontal)
        self.slider.setRange(0, 150); self.slider.setValue(info.volume)
        self.slider.valueChanged.connect(lambda v: self.volume_changed.emit(self.sink_name, v))
        ctrl.addWidget(self.slider, 1)
        self.lbl_vol = QLabel(f"{info.volume}%"); self.lbl_vol.setObjectName("volumeLabel"); self.lbl_vol.setFixedWidth(45)
        ctrl.addWidget(self.lbl_vol)
        lay.addLayout(ctrl)

        self.peak_bar = QProgressBar()
        self.peak_bar.setRange(0, 1000); self.peak_bar.setValue(0); self.peak_bar.setTextVisible(False)
        self.peak_bar.setFixedHeight(4)
        self.peak_bar.setStyleSheet("QProgressBar { background: #1e1e1e; border: 1px solid #333; border-radius: 2px; } QProgressBar::chunk { background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #007acc, stop:1 #00ff88); border-radius: 2px; }")
        lay.addWidget(self.peak_bar)
        self.update_state(info)

    def _ask_rename(self):
        new_name, ok = QInputDialog.getText(self, "Renombrar", "Nuevo nombre:", text=self.lbl_name.text())
        if ok and new_name.strip(): self.rename_requested.emit(self.sink_name, new_name.strip())

    def update_state(self, info: ChannelInfo):
        self.slider.blockSignals(True); self.btn_mute.blockSignals(True)
        self.lbl_name.setText(info.name)
        self.slider.setValue(info.volume)
        self.lbl_vol.setText(f"{info.volume}%")
        self.btn_mute.setChecked(info.mute)
        self.btn_mute.setText("🔇" if info.mute else "🔊")
        self.peak_bar.setValue(int(info.peak * 1000))
        self.slider.blockSignals(False); self.btn_mute.blockSignals(False)

class AddChannelDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent); self.setWindowTitle("Nuevo Canal"); self.setModal(True)
        lay = QVBoxLayout(self)
        lay.addWidget(QLabel("Nombre del canal:"))
        self.edit = QLineEdit(); self.edit.setPlaceholderText("Ej: Discord, Juego, Navegador, Música..."); lay.addWidget(self.edit)
        btns = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        btns.accepted.connect(self.accept); btns.rejected.connect(self.reject); lay.addWidget(btns)
    def get_name(self) -> str: return self.edit.text().strip()

class ChannelsTab(QWidget):
    def __init__(self, worker: AudioWorker):
        super().__init__(); self.worker = worker; self.widgets: Dict[str, ChannelWidget] = {}; self._build_ui()
    def _build_ui(self):
        main = QVBoxLayout(self); main.setContentsMargins(10, 10, 10, 10)
        bar = QHBoxLayout(); bar.addWidget(QLabel("<b>Canales Virtuales</b>")); bar.addStretch()
        btn = QPushButton("+"); btn.setObjectName("addChannelBtn"); btn.setToolTip("Añadir Canal"); btn.clicked.connect(self._on_add)
        bar.addWidget(btn); main.addLayout(bar)
        scroll = QScrollArea(); scroll.setWidgetResizable(True); scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded); scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.cont = QWidget(); self.hbox = QHBoxLayout(self.cont); self.hbox.setAlignment(Qt.AlignmentFlag.AlignLeft); self.hbox.setSpacing(10); self.hbox.addStretch()
        scroll.setWidget(self.cont); main.addWidget(scroll)
    def _on_add(self):
        dlg = AddChannelDialog(self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            n = dlg.get_name()
            if n: self.worker.add_channel.emit(n)
    @pyqtSlot(object)
    def on_state_updated(self, state: AppState):
        cur = set(state.channels.keys())
        ext = set(self.widgets.keys())
        for sn in ext - cur: w = self.widgets.pop(sn); w.deleteLater()
        for sn, info in state.channels.items():
            if sn in self.widgets: self.widgets[sn].update_state(info)
            else:
                w = ChannelWidget(info, is_system=(sn == state.system_channel_sink_name))
                w.volume_changed.connect(self.worker.set_volume)
                w.mute_toggled.connect(self.worker.toggle_mute)
                w.rename_requested.connect(self.worker.rename_channel)
                w.delete_requested.connect(self.worker.remove_channel)
                self.hbox.insertWidget(self.hbox.count()-1, w)
                self.widgets[sn] = w

class ProcessRow(QWidget):
    move_requested = pyqtSignal(int, str)
    assign_requested = pyqtSignal(str, str)

    def __init__(self, proc: ProcessInfo, channels: Dict[str, ChannelInfo], worker: AudioWorker):
        super().__init__(); self.proc = proc; self.worker = worker
        lay = QHBoxLayout(self); lay.setContentsMargins(8, 4, 8, 4); lay.setSpacing(10)
        info_l = QVBoxLayout()
        info_l.addWidget(QLabel(proc.name, objectName="processName"))
        info_l.addWidget(QLabel(proc.binary, objectName="processBinary"))
        lay.addLayout(info_l, 1)

        self.combo = QComboBox()
        self._rebuild_combo(channels)
        idx = self.combo.findData(proc.current_channel_sink_name)
        if idx >= 0: self.combo.setCurrentIndex(idx)
        self.combo.currentIndexChanged.connect(self._on_combo)
        lay.addWidget(self.combo)

        btn = QPushButton("📌"); btn.setFixedWidth(32); btn.setToolTip(f"Asignar '{proc.binary}' a este canal")
        btn.clicked.connect(lambda: self.assign_requested.emit(self.proc.binary, self.combo.currentText()))
        lay.addWidget(btn)

    def _rebuild_combo(self, channels: Dict[str, ChannelInfo]):
        current_data = self.combo.currentData()
        self.combo.blockSignals(True)
        self.combo.clear()
        for ch in channels.values(): self.combo.addItem(ch.name, ch.sink_name)
        idx = self.combo.findData(current_data)
        if idx >= 0: self.combo.setCurrentIndex(idx)
        self.combo.blockSignals(False)

    def _on_combo(self, idx: int):
        sn = self.combo.itemData(idx)
        if sn: self.move_requested.emit(self.proc.index, sn)

    def update_state(self, proc: ProcessInfo, channels: Dict[str, ChannelInfo]):
        self.proc = proc
        self._rebuild_combo(channels)
        idx = self.combo.findData(proc.current_channel_sink_name)
        if idx >= 0: self.combo.setCurrentIndex(idx)

class ProcessesTab(QWidget):
    def __init__(self, worker: AudioWorker):
        super().__init__(); self.worker = worker; self.widgets: Dict[int, ProcessRow] = {}; self._build_ui()
    def _build_ui(self):
        lay = QVBoxLayout(self); lay.setContentsMargins(10, 10, 10, 10)
        lay.addWidget(QLabel("<b>Aplicaciones Activas</b><br><i>Selecciona canal. 📌 = Regla persistente.</i>"))
        self.scroll = QScrollArea(); self.scroll.setWidgetResizable(True)
        self.cont = QWidget(); self.vbox = QVBoxLayout(self.cont); self.vbox.setAlignment(Qt.AlignmentFlag.AlignTop); self.vbox.setSpacing(2)
        self.scroll.setWidget(self.cont); lay.addWidget(self.scroll)
    @pyqtSlot(object)
    def on_state_updated(self, state: AppState):
        cur_idx = {p.index for p in state.processes}
        ext_idx = set(self.widgets.keys())
        for idx in ext_idx - cur_idx:
            w = self.widgets.pop(idx); w.deleteLater()
        ch_map = state.channels
        for proc in state.processes:
            if proc.index in self.widgets:
                self.widgets[proc.index].update_state(proc, ch_map)
            else:
                row = ProcessRow(proc, ch_map, self.worker)
                row.move_requested.connect(self.worker.move_sink_input)
                row.assign_requested.connect(self.worker.assign_binary)
                self.vbox.insertWidget(self.vbox.count()-1, row)
                self.widgets[proc.index] = row

class OutputTab(QWidget):
    def __init__(self, worker: AudioWorker):
        super().__init__(); self.worker = worker; self._build_ui()
    def _build_ui(self):
        lay = QVBoxLayout(self); lay.setContentsMargins(10, 10, 10, 10)
        lay.addWidget(QLabel("<b>Salida Física (Master Output)</b>"))
        lay.addWidget(QLabel("Selecciona dónde escuchas la mezcla final:"))
        self.combo = QComboBox(); self.combo.currentIndexChanged.connect(self._on_change); lay.addWidget(self.combo); lay.addStretch()
    @pyqtSlot(object)
    def on_state_updated(self, state: AppState):
        self.combo.blockSignals(True)
        self.combo.clear()
        for s in state.physical_sinks: self.combo.addItem(s["description"], s["name"])
        idx = self.combo.findData(state.current_output_sink)
        if idx >= 0: self.combo.setCurrentIndex(idx)
        elif self.combo.count() > 0: self.combo.setCurrentIndex(0)
        self.combo.blockSignals(False)
    def _on_change(self, idx: int):
        if idx >= 0: self.worker.set_output_sink.emit(self.combo.itemData(idx))

# ----------------------------------------------------------------------
# MAIN WINDOW
# ----------------------------------------------------------------------
class MainWindow(QMainWindow):
    shutdown_requested = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setWindowTitle("KORVEX Stream Deck"); self.resize(1100, 700); self.setStyleSheet(STYLESHEET)
        self.config_dir = os.path.expanduser("~/.config/korvex-streamdeck")

        self.thread = QThread()
        self.worker = AudioWorker(self.config_dir)
        self.worker.moveToThread(self.thread)

        self.tabs = QTabWidget()
        self.channels_tab = ChannelsTab(self.worker)
        self.processes_tab = ProcessesTab(self.worker)
        self.output_tab = OutputTab(self.worker)
        self.tabs.addTab(self.channels_tab, "🎚️ Canales")
        self.tabs.addTab(self.processes_tab, "📦 Procesos")
        self.tabs.addTab(self.output_tab, "🔊 Salida")
        self.setCentralWidget(self.tabs)

        self.worker.state_updated.connect(self.channels_tab.on_state_updated)
        self.worker.state_updated.connect(self.processes_tab.on_state_updated)
        self.worker.state_updated.connect(self.output_tab.on_state_updated)
        self.worker.error_occurred.connect(lambda m: print(f"[AUDIO ERROR] {m}"))
        self.worker.operation_finished.connect(lambda s, m: (not s and QMessageBox.warning(self, "Error", m)))
        self.worker.finished.connect(self._on_worker_finished)
        self.shutdown_requested.connect(self.worker.stop)

        self.thread.started.connect(self.worker.start)
        self.thread.start()

    def closeEvent(self, event):
        print("MainWindow: Close event received. Shutting down audio...")
        self.shutdown_requested.emit()
        
        if self.thread.isRunning():
            loop = QEventLoop()
            self.worker.finished.connect(loop.quit)
            QTimer.singleShot(3000, loop.quit)
            loop.exec()
        
        self.thread.quit()
        self.thread.wait(1000)
        print("MainWindow: Thread joined. Exiting.")
        event.accept()

    @pyqtSlot()
    def _on_worker_finished(self):
        print("MainWindow: Worker finished signal received.")

# ----------------------------------------------------------------------
# ENTRY POINT
# ----------------------------------------------------------------------
def main():
    QApplication.setHighDpiScaleFactorRoundingPolicy(Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
    app = QApplication(sys.argv)
    app.setApplicationName("KORVEX Stream Deck")
    app.setStyleSheet(STYLESHEET)
    try:
        with pulsectl.Pulse('korvex-check') as p: p.server_info()
    except Exception as e:
        QMessageBox.critical(None, "Error de Audio", f"No se pudo conectar a PipeWire/PulseAudio.\n\n¿Servidor corriendo?\n\n{e}")
        sys.exit(1)
    win = MainWindow()
    win.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
