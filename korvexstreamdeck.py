#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
import json
import subprocess
import atexit
from typing import Dict, List, Optional

import pulsectl
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QSlider, QPushButton, QScrollArea, QFrame, QComboBox, QTabWidget,
    QMessageBox, QLineEdit, QDialog, QDialogButtonBox, QInputDialog,
    QSizePolicy
)
from PyQt6.QtCore import Qt, QTimer, QSize, pyqtSignal
from PyQt6.QtGui import QFont

# ----------------------------------------------------------------------
# ESTILO GLOBAL
# ----------------------------------------------------------------------
DEFAULT_STYLESHEET = """
QMainWindow { background-color: #1e1e1e; }
QWidget { background-color: #1e1e1e; color: white; }
QTabWidget::pane { border: 1px solid #3e3e42; border-radius: 5px; }
QTabBar::tab { background: #2d2d30; color: #aaa; padding: 8px 15px; border-top-left-radius: 5px; border-top-right-radius: 5px; margin-right: 2px; }
QTabBar::tab:selected { background: #3e3e42; color: white; font-weight: bold; border-bottom: 2px solid #00aaff; }
QPushButton { background-color: #333; color: white; padding: 8px 16px; border-radius: 5px; font-weight: bold; }
QPushButton:hover { background-color: #444; }
QPushButton:disabled { background-color: #252526; color: #666; }
QPushButton#addChannelBtn { background-color: #007acc; }
QPushButton#addChannelBtn:hover { background-color: #0099ff; }
QPushButton#deleteBtn { background-color: #c0392b; max-width: 30px; }
QPushButton#deleteBtn:hover { background-color: #e74c3c; }
QPushButton#renameBtn { background-color: #555; max-width: 30px; }
QPushButton#renameBtn:hover { background-color: #777; }
QPushButton#muteBtn { font-size: 18px; border: none; background: transparent; }
QPushButton#muteBtn:hover { background-color: #3e3e42; }
QComboBox { background: #2d2d30; border: 1px solid #3e3e42; padding: 5px; color: white; min-height: 25px; }
QComboBox::drop-down { border: none; }
QSlider::groove:horizontal { border: 1px solid #3e3e42; height: 8px; background: #252526; margin: 2px 0; border-radius: 4px; }
QSlider::handle:horizontal { background: #007acc; border: 1px solid #007acc; width: 18px; height: 18px; margin: -6px 0; border-radius: 9px; }
QScrollArea { border: none; background: transparent; }
QScrollBar:horizontal { border: none; background: #252526; height: 8px; border-radius: 4px; }
QScrollBar::handle:horizontal { background: #444; min-width: 20px; border-radius: 4px; }
QScrollBar::handle:horizontal:hover { background: #00aaff; }
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal { border: none; background: none; width: 0px; }
"""

# ----------------------------------------------------------------------
# GESTOR DE AUDIO
# ----------------------------------------------------------------------
class AudioManager:
    """Clase que encapsula todas las operaciones con PulseAudio/PipeWire."""

    MASTER_SINK_NAME = "korvex_master"
    SYSTEM_CHANNEL_NAME = "System"
    CHANNEL_PREFIX = "korvex_ch_"
    CONFIG_PATH = os.path.expanduser("~/.config/korvex-streamdeck")

    def __init__(self):
        self.pulse = pulsectl.Pulse('korvex-streamdeck')
        self.channels: Dict[str, dict] = {}       # nombre visible -> info
        self.output_sink_name: str = ""
        self.module_ids: List[int] = []           # IDs de módulos creados por nosotros
        self.config = {}
        self.load_config()
        self.cleanup_previous_instances()  # Eliminar sinks virtuales antiguos
        self.ensure_audio_graph()
        atexit.register(self.cleanup)      # Limpiar al salir

    # ------------------------------------------------------------------
    # Configuración persistente
    # ------------------------------------------------------------------
    def load_config(self):
        os.makedirs(self.CONFIG_PATH, exist_ok=True)
        self.config_file = os.path.join(self.CONFIG_PATH, "config.json")
        self.config = {}
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, "r", encoding="utf-8") as f:
                    self.config = json.load(f)
            except Exception as e:
                print(f"Error loading config: {e}")

        self.config.setdefault("channels", [])
        self.config.setdefault("assignments", {})
        self.config.setdefault("output_sink", "")
        self.output_sink_name = self.config.get("output_sink", "")

    def save_config(self):
        self.config["channels"] = [{"name": name, "sink_name": info["sink_name"]}
                                   for name, info in self.channels.items()]
        self.config["assignments"] = self.assignments
        self.config["output_sink"] = self.output_sink_name
        try:
            with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump(self.config, f, indent=4)
        except Exception as e:
            print(f"Error saving config: {e}")

    @property
    def assignments(self):
        return self.config.setdefault("assignments", {})

    # ------------------------------------------------------------------
    # Limpieza
    # ------------------------------------------------------------------
    def cleanup_previous_instances(self):
        """Elimina cualquier sink virtual creado por una ejecución anterior."""
        for sink in self.pulse.sink_list():
            if sink.name.startswith(self.CHANNEL_PREFIX) or sink.name == self.MASTER_SINK_NAME:
                try:
                    # Descargar módulo del sink
                    if sink.owner_module is not None:
                        self.pulse.module_unload(sink.owner_module)
                except Exception as e:
                    print(f"Error unloading module for sink {sink.name}: {e}")

        # También eliminar loopbacks creados por nosotros (owner_module de sink_inputs)
        for si in self.pulse.sink_input_list():
            if si.name.startswith("Loopback from") and (
                self.MASTER_SINK_NAME in si.proplist.get("media.name", "") or
                self.CHANNEL_PREFIX in si.proplist.get("media.name", "")
            ):
                try:
                    self.pulse.module_unload(si.owner_module)
                except Exception as e:
                    print(f"Error unloading loopback module: {e}")

    def cleanup(self):
        """Limpia todos los módulos creados por esta sesión."""
        # Descargar loopbacks
        for si in self.pulse.sink_input_list():
            if si.name.startswith("Loopback from") and (
                self.MASTER_SINK_NAME in si.proplist.get("media.name", "") or
                self.CHANNEL_PREFIX in si.proplist.get("media.name", "")
            ):
                try:
                    self.pulse.module_unload(si.owner_module)
                except Exception as e:
                    print(f"Error unloading loopback: {e}")

        # Descargar sinks virtuales
        for sink in self.pulse.sink_list():
            if sink.name.startswith(self.CHANNEL_PREFIX) or sink.name == self.MASTER_SINK_NAME:
                try:
                    self.pulse.module_unload(sink.owner_module)
                except Exception as e:
                    print(f"Error unloading sink {sink.name}: {e}")

        # Restaurar sink por defecto anterior (opcional)
        # No lo hacemos para no interferir.

    # ------------------------------------------------------------------
    # Creación de sinks virtuales
    # ------------------------------------------------------------------
    def _load_module(self, module_name: str, args: str) -> Optional[int]:
        try:
            idx = self.pulse.module_load(module_name, args)
            if idx is not None:
                self.module_ids.append(idx)
            return idx
        except Exception as e:
            print(f"Error loading module {module_name} with args {args}: {e}")
            return None

    def _sink_exists(self, sink_name: str) -> bool:
        for sink in self.pulse.sink_list():
            if sink.name == sink_name:
                return True
        return False

    def _create_null_sink(self, sink_name: str, description: str) -> bool:
        if self._sink_exists(sink_name):
            return True
        args = f"sink_name={sink_name} sink_properties=device.description='{description}'"
        idx = self._load_module("module-null-sink", args)
        if idx is not None:
            return self._sink_exists(sink_name)
        return False

    def _create_loopback(self, source_name: str, sink_name: str) -> Optional[int]:
        args = f"source={source_name} sink={sink_name}"
        return self._load_module("module-loopback", args)

    def ensure_audio_graph(self):
        try:
            # 1. Crear sink maestro
            if not self._create_null_sink(self.MASTER_SINK_NAME, "KORVEX Master Mix"):
                raise RuntimeError("No se pudo crear el sink maestro.")

            # 2. Crear canal System
            system_sink_name = self.CHANNEL_PREFIX + "system"
            if not self._create_null_sink(system_sink_name, self.SYSTEM_CHANNEL_NAME):
                raise RuntimeError("No se pudo crear el canal System.")

            # 3. Crear canales adicionales desde config
            for ch in self.config.get("channels", []):
                if ch["name"] != self.SYSTEM_CHANNEL_NAME:
                    sink_name = ch.get("sink_name", self.CHANNEL_PREFIX + ch["name"].lower().replace(" ", "_"))
                    self._create_null_sink(sink_name, ch["name"])

            # 4. Refrescar lista de canales
            self.refresh_channels()

            # 5. Loopbacks de canales al maestro
            self._ensure_loopbacks_to_master()

            # 6. Establecer sink por defecto = System
            self.set_default_sink(self.SYSTEM_CHANNEL_NAME)

            # 7. Enrutar maestro a salida física
            self.update_output_routing()
        except Exception as e:
            raise RuntimeError(f"Error al configurar el grafo de audio: {e}")

    def refresh_channels(self):
        self.channels = {}
        for sink in self.pulse.sink_list():
            if sink.name.startswith(self.CHANNEL_PREFIX):
                description = sink.description
                self.channels[description] = {
                    "sink_name": sink.name,
                    "sink_index": sink.index,
                }
        # Garantizar que System existe
        if self.SYSTEM_CHANNEL_NAME not in self.channels:
            # Buscar el sink system
            sys_sink_name = self.CHANNEL_PREFIX + "system"
            for sink in self.pulse.sink_list():
                if sink.name == sys_sink_name:
                    self.channels[self.SYSTEM_CHANNEL_NAME] = {
                        "sink_name": sink.name,
                        "sink_index": sink.index,
                    }
                    break

    def _is_physical_sink(self, sink) -> bool:
        return not sink.name.startswith(self.CHANNEL_PREFIX) and sink.name != self.MASTER_SINK_NAME

    def _ensure_loopbacks_to_master(self):
        master_idx = self._get_sink_index_by_name(self.MASTER_SINK_NAME)
        if master_idx is None:
            return

        existing_sources = set()
        for si in self.pulse.sink_input_list():
            if si.name.startswith("Loopback from"):
                source_name = si.proplist.get("media.name", "")
                if source_name:
                    existing_sources.add(source_name)

        for ch_name, info in self.channels.items():
            monitor_source = f"{info['sink_name']}.monitor"
            if monitor_source not in existing_sources:
                self._create_loopback(monitor_source, self.MASTER_SINK_NAME)

    def set_default_sink(self, channel_name: str):
        if channel_name not in self.channels:
            raise KeyError(f"El canal '{channel_name}' no existe")
        sink_name = self.channels[channel_name]["sink_name"]
        try:
            subprocess.run(["pactl", "set-default-sink", sink_name], check=True)
        except Exception as e:
            print(f"Error setting default sink: {e}")

    def update_output_routing(self):
        master_idx = self._get_sink_index_by_name(self.MASTER_SINK_NAME)
        if master_idx is None:
            return

        # Obtener loopbacks existentes desde master.monitor
        current_loopbacks = []
        for si in self.pulse.sink_input_list():
            if si.name.startswith("Loopback from") and si.proplist.get("media.name") == f"{self.MASTER_SINK_NAME}.monitor":
                current_loopbacks.append(si)

        if not self.output_sink_name:
            physical = [s for s in self.pulse.sink_list() if self._is_physical_sink(s)]
            if physical:
                self.output_sink_name = physical[0].name
                self.save_config()

        if not self.output_sink_name:
            return

        # Eliminar loopbacks incorrectos
        for si in current_loopbacks:
            if si.sink != self._get_sink_index_by_name(self.output_sink_name):
                try:
                    self.pulse.module_unload(si.owner_module)
                except Exception as e:
                    print(f"Error unloading loopback: {e}")

        # Crear loopback si no existe
        target_sink_idx = self._get_sink_index_by_name(self.output_sink_name)
        if target_sink_idx is not None:
            exists = any(si.sink == target_sink_idx for si in current_loopbacks)
            if not exists:
                self._create_loopback(f"{self.MASTER_SINK_NAME}.monitor", self.output_sink_name)

    def set_output_sink(self, sink_name: str):
        self.output_sink_name = sink_name
        self.save_config()
        self.update_output_routing()

    def get_physical_sinks(self) -> List[dict]:
        return [{"name": s.name, "description": s.description}
                for s in self.pulse.sink_list() if self._is_physical_sink(s)]

    def get_channel_sink_index(self, channel_name: str) -> Optional[int]:
        info = self.channels.get(channel_name)
        return info["sink_index"] if info else None

    # ... (resto de métodos de canales, volumen, procesos, etc., sin cambios conceptuales)
    # ... (pero adaptando add_channel, remove_channel, rename_channel al nuevo prefijo)
    def add_channel(self, name: str) -> bool:
        if not name or name in self.channels:
            return False
        sink_name = self.CHANNEL_PREFIX + name.lower().replace(" ", "_")
        if self._create_null_sink(sink_name, name):
            self.refresh_channels()
            self._ensure_loopbacks_to_master()
            self.save_config()
            return True
        return False

    def remove_channel(self, name: str) -> bool:
        if name == self.SYSTEM_CHANNEL_NAME:
            return False
        info = self.channels.get(name)
        if not info:
            return False
        # Mover streams a System
        system_idx = self.get_channel_sink_index(self.SYSTEM_CHANNEL_NAME)
        if system_idx is not None:
            for si in self.pulse.sink_input_list():
                if si.sink == info["sink_index"]:
                    try:
                        self.pulse.move_sink_input(si.index, system_idx)
                    except Exception as e:
                        print(f"Error moving sink input: {e}")
        # Descargar sink
        try:
            for sink in self.pulse.sink_list():
                if sink.name == info["sink_name"]:
                    self.pulse.module_unload(sink.owner_module)
                    break
        except Exception as e:
            print(f"Error unloading sink: {e}")
        self.refresh_channels()
        self.save_config()
        self._ensure_loopbacks_to_master()
        return True

    def rename_channel(self, old_name: str, new_name: str) -> bool:
        if new_name in self.channels or new_name == old_name:
            return False
        info = self.channels.get(old_name)
        if not info:
            return False
        try:
            self.pulse.sink_proplist_update(info["sink_index"], {"device.description": new_name})
        except Exception as e:
            print(f"Error renaming sink: {e}")
            return False
        self.channels[new_name] = self.channels.pop(old_name)
        # Actualizar asignaciones
        for binary, ch in list(self.assignments.items()):
            if ch == old_name:
                self.assignments[binary] = new_name
        self.save_config()
        return True

    # ------------------------------------------------------------------
    # Volumen y mute
    # ------------------------------------------------------------------
    def set_channel_volume(self, channel_name: str, volume: int):
        idx = self.get_channel_sink_index(channel_name)
        if idx is not None:
            try:
                self.pulse.sink_volume_set(idx, pulsectl.PulseVolumeInfo([volume/100.0]*2))
            except Exception as e:
                print(f"Error setting volume: {e}")

    def toggle_channel_mute(self, channel_name: str) -> bool:
        idx = self.get_channel_sink_index(channel_name)
        if idx is not None:
            try:
                mute_state = self.pulse.sink_mute(idx)
                self.pulse.sink_mute(idx, not mute_state)
                return not mute_state
            except Exception as e:
                print(f"Error toggling mute: {e}")
        return False

    def get_channel_volume(self, channel_name: str) -> int:
        idx = self.get_channel_sink_index(channel_name)
        if idx is not None:
            try:
                vol = self.pulse.sink_volume(idx)
                return int(vol.value_flat * 100)
            except:
                pass
        return 0

    def get_channel_mute(self, channel_name: str) -> bool:
        idx = self.get_channel_sink_index(channel_name)
        if idx is not None:
            try:
                return self.pulse.sink_mute(idx)
            except:
                pass
        return False

    # ------------------------------------------------------------------
    # Procesos
    # ------------------------------------------------------------------
    def get_active_sink_inputs(self) -> List[dict]:
        inputs = []
        for si in self.pulse.sink_input_list():
            if si.name.startswith("Loopback from"):
                continue
            binary = si.proplist.get("application.process.binary", "")
            if not binary:
                binary = si.proplist.get("application.name", si.name)
            channel_name = self._get_channel_of_sink(si.sink)
            inputs.append({
                "index": si.index,
                "name": si.name,
                "binary": binary,
                "channel": channel_name,
                "mute": si.mute,
                "volume": int(si.volume.value_flat * 100) if si.volume else 0,
                "peak": getattr(si, "peak", 0.0)
            })
        return inputs

    def _get_channel_of_sink(self, sink_index: int) -> str:
        for ch_name, info in self.channels.items():
            if info["sink_index"] == sink_index:
                return ch_name
        return "Desconocido"

    def move_sink_input_to_channel(self, sink_input_index: int, channel_name: str):
        channel_idx = self.get_channel_sink_index(channel_name)
        if channel_idx is not None:
            try:
                self.pulse.move_sink_input(sink_input_index, channel_idx)
                return True
            except Exception as e:
                print(f"Error moving sink input: {e}")
        return False

    def assign_binary_to_channel(self, binary: str, channel_name: str):
        self.assignments[binary] = channel_name
        self.save_config()

    def get_assigned_channel(self, binary: str) -> Optional[str]:
        return self.assignments.get(binary)

    def _get_sink_index_by_name(self, name: str) -> Optional[int]:
        for sink in self.pulse.sink_list():
            if sink.name == name:
                return sink.index
        return None

# ----------------------------------------------------------------------
# WIDGET DE CANAL (sin cambios importantes, pero se mantiene)
# ----------------------------------------------------------------------
class ChannelWidget(QFrame):
    # ... (código similar al anterior)
    pass

# ----------------------------------------------------------------------
# DIÁLOGO PARA AÑADIR CANAL
# ----------------------------------------------------------------------
class AddChannelDialog(QDialog):
    # ... (igual)
    pass

# ----------------------------------------------------------------------
# PESTAÑA DE CANALES
# ----------------------------------------------------------------------
class ChannelsTab(QWidget):
    # ... (igual, pero sin cambios)
    pass

# ----------------------------------------------------------------------
# PESTAÑA DE PROCESOS
# ----------------------------------------------------------------------
class ProcessesTab(QWidget):
    # ... (igual)
    pass

# ----------------------------------------------------------------------
# VENTANA PRINCIPAL
# ----------------------------------------------------------------------
class MainWindow(QMainWindow):
    # ... (igual)
    pass

# ----------------------------------------------------------------------
# MAIN
# ----------------------------------------------------------------------
def main():
    app = QApplication(sys.argv)
    app.setApplicationName("KORVEX Stream Deck")
    app.setStyleSheet(DEFAULT_STYLESHEET)

    try:
        audio = AudioManager()
    except Exception as e:
        QMessageBox.critical(None, "Error", f"No se pudo conectar con PulseAudio/PipeWire.\n{e}")
        sys.exit(1)

    window = MainWindow(audio)
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()