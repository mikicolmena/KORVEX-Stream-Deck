# 🎚️ KORVEX Stream Deck

Mezclador de audio virtual para Linux sobre PipeWire/PulseAudio.
Crea canales independientes, asigna aplicaciones a cada uno y controla su volumen sin cambiar nada en el sistema.

![Versión](https://img.shields.io/badge/versión-1.0.0-5E6AD2?style=for-the-badge)
![Plataformas](https://img.shields.io/badge/plataforma-Linux-FCC624?style=for-the-badge&logo=linux&logoColor=black)
![Licencia](https://img.shields.io/badge/licencia-MIT-3EC775?style=for-the-badge)

---

## ✨ Características

- 🎛️ **Canales virtuales ilimitados** (System, Gaming, Music, Discord, …).
- 🧭 **Enrutamiento de apps por canal** con persistencia entre reinicios.
- 🔊 **Fader y mute independientes** por canal.
- 📊 **Vúmetros en tiempo real** calculados desde el monitor de cada sink.
- 🎧 **Salida maestra configurable** hacia cualquier dispositivo físico (una sola vez).
- 🖼️ **Iconos de las aplicaciones** tomados del tema del sistema.
- ⚙️ **Autostart con el sistema** activable desde la propia app.
- 💾 **Configuración persistente** en `~/.config/korvex-streamdeck/config.json`.
- 🔄 **Reconexión automática** si PipeWire/PulseAudio se reinicia.
- 🚫 **Filtro de streams internos** (loopbacks, speech-dispatcher, etc.).
- 🐧 Interfaz moderna en **PyQt6**.

---

## 📥 Descarga e instalación

### Linux (Debian/Ubuntu) — Recomendado

Descarga el `.deb` desde la sección [**Releases**](../../releases/latest) y ejecuta:

```bash
sudo apt install ./korvex-streamdeck_1.0.0_all.deb
```

El paquete instala automáticamente las dependencias necesarias y añade el lanzador al menú de aplicaciones con su icono.

> **Nota:** usa `apt install ./ruta.deb` (con el `./` delante) en lugar de `dpkg -i` para que `apt` resuelva dependencias automáticamente.

### Otras distribuciones (Arch, Fedora, openSUSE…)

Desde el código fuente con `pip`:

```bash
git clone https://github.com/mikicolmena/KORVEX-Stream-Deck.git
cd KORVEX-Stream-Deck
pip3 install --user -r requirements.txt
python3 korvexstreamdeck.py
```

### Requisitos

| Componente | Versión mínima | Notas |
|-----------|---------------|-------|
| Python | 3.10 | |
| PyQt6 | 6.4 | GUI |
| pulsectl | 23.5 – 24.x | Control de PulseAudio/PipeWire |
| `pactl` | — | Incluido en `pulseaudio-utils` |
| `parec` | — | Incluido en `pulseaudio-utils` |
| `pw-metadata`, `pw-dump` | — | Opcional, para WirePlumber |
| PipeWire o PulseAudio | — | Servidor de audio |

---

## 🚀 Uso

1. Abre **KORVEX Stream Deck** desde el menú de aplicaciones.
2. En **Salida Maestra**, elige tu dispositivo físico (auriculares, altavoces, interfaz USB…). Solo hay que hacerlo una vez.
3. Ve a **Aplicaciones** y asigna cada app a un canal desde el desplegable.
4. En **Mezclador**, ajusta el volumen o mutea cada canal de forma independiente.

### Reglas de oro

- 🔀 Las apps se enrutan **siempre** a un canal `korvex_ch_*` (System, Gaming…), nunca al **Master** directamente.
- 💾 Las asignaciones se guardan automáticamente y se restauran al arrancar la app o al reiniciar el PC.
- 🎚️ El fader de un canal controla **solo** las apps asignadas a ese canal.
- 🔇 El botón MUTE silencia **solo** ese canal.

---

## 🛠️ Construir el .deb desde el código fuente

```bash
git clone https://github.com/mikicolmena/KORVEX-Stream-Deck.git
cd KORVEX-Stream-Deck
./build_deb.sh
sudo apt install ./korvex-streamdeck_1.0.0_all.deb
```

El script `build_deb.sh` genera el paquete listo para distribuir en `./korvex-streamdeck_1.0.0_all.deb`.

---

## 📂 Estructura del proyecto

```
KORVEX-Stream-Deck/
├── korvexstreamdeck.py     # Código principal
├── build_deb.sh            # Script de empaquetado
├── requirements.txt        # Dependencias pip
├── KorvexLogo-128.png      # Icono 128×128
├── KorvexLogo-256.png      # Icono 256×256
└── README.md
```

---

## 🐛 Problemas conocidos

- **Los vúmetros no se mueven**: verifica que `parec` está instalado (`sudo apt install pulseaudio-utils`).
- **La app no ve mis canales**: asegúrate de que PipeWire/PulseAudio está corriendo y que tu usuario tiene acceso al socket de audio.
- **`speech-dispatcher` u otros streams internos aparecen**: están filtrados por defecto, pero si ves alguno más, abre un issue con el nombre del stream.
- **Al arrancar con el PC no se inicia**: activa el autostart desde **Ajustes → Iniciar con el sistema**.

---

## 🤝 Contribuir

Las contribuciones son bienvenidas. Para cambios importantes, abre primero un **issue** explicando qué quieres cambiar.

1. Haz un fork del repo.
2. Crea tu rama: `git checkout -b feature/mi-mejora`.
3. Commit: `git commit -m "feat: descripción"`.
4. Push: `git push origin feature/mi-mejora`.
5. Abre un **Pull Request**.

---

## 📄 Licencia

Este proyecto está bajo la licencia **MIT**. Consulta [LICENSE](LICENSE) para más detalles.

---

Hecho con ❤️ por [@mikicolmena](https://github.com/mikicolmena)
