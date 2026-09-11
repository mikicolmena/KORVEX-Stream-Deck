#!/bin/bash
# build_deb.sh — Construye el paquete .deb de KORVEX Stream Deck
set -e

PKG_NAME="korvex-streamdeck"
PKG_VERSION="1.0.0"
PKG_ARCH="all"
BUILD_DIR="$(pwd)/build_deb"
ROOT="${BUILD_DIR}/${PKG_NAME}_${PKG_VERSION}_${PKG_ARCH}"

echo "🔨 Construyendo ${PKG_NAME} ${PKG_VERSION}..."

# =============================================================================
# Comprobaciones previas
# =============================================================================
if [ ! -f korvexstreamdeck.py ]; then
    echo "❌ Falta korvexstreamdeck.py"
    exit 1
fi

for f in KorvexLogo-256.png KorvexLogo-128.png; do
    if [ ! -f "$f" ]; then
        echo "⚠️  Falta $f"
        echo "    Genera primero los iconos reducidos:"
        echo "      sudo apt install imagemagick"
        echo "      convert KorvexLogo.png -resize 256x256 KorvexLogo-256.png"
        echo "      convert KorvexLogo.png -resize 128x128 KorvexLogo-128.png"
        exit 1
    fi
done

# =============================================================================
# Limpiar
# =============================================================================
rm -rf "${BUILD_DIR}"
mkdir -p "${ROOT}"

mkdir -p "${ROOT}/DEBIAN"
mkdir -p "${ROOT}/usr/bin"
mkdir -p "${ROOT}/usr/lib/${PKG_NAME}"
mkdir -p "${ROOT}/usr/share/applications"
mkdir -p "${ROOT}/usr/share/icons/hicolor/128x128/apps"
mkdir -p "${ROOT}/usr/share/icons/hicolor/256x256/apps"
mkdir -p "${ROOT}/usr/share/doc/${PKG_NAME}"

# =============================================================================
# Código Python
# =============================================================================
cp korvexstreamdeck.py "${ROOT}/usr/lib/${PKG_NAME}/korvexstreamdeck.py"
chmod 644 "${ROOT}/usr/lib/${PKG_NAME}/korvexstreamdeck.py"

# =============================================================================
# Launcher
# =============================================================================
cat > "${ROOT}/usr/bin/${PKG_NAME}" <<EOF
#!/bin/bash
exec python3 /usr/lib/${PKG_NAME}/korvexstreamdeck.py "\$@"
EOF
chmod 755 "${ROOT}/usr/bin/${PKG_NAME}"

# =============================================================================
# .desktop
# =============================================================================
cat > "${ROOT}/usr/share/applications/${PKG_NAME}.desktop" <<EOF
[Desktop Entry]
Type=Application
Name=KORVEX Stream Deck
GenericName=Audio Mixer
Comment=Virtual audio mixer for streaming on PipeWire/PulseAudio
Exec=${PKG_NAME}
Icon=${PKG_NAME}
Terminal=false
Categories=Audio;AudioVideo;Mixer;
Keywords=audio;mixer;streaming;pipewire;pulseaudio;
StartupNotify=true
StartupWMClass=KORVEX Stream Deck
EOF
chmod 644 "${ROOT}/usr/share/applications/${PKG_NAME}.desktop"

# =============================================================================
# Iconos
# =============================================================================
cp KorvexLogo-256.png "${ROOT}/usr/share/icons/hicolor/256x256/apps/${PKG_NAME}.png"
cp KorvexLogo-128.png "${ROOT}/usr/share/icons/hicolor/128x128/apps/${PKG_NAME}.png"

# =============================================================================
# Copyright
# =============================================================================
cat > "${ROOT}/usr/share/doc/${PKG_NAME}/copyright" <<'EOF'
Format: https://www.debian.org/doc/packaging-manuals/copyright-format/1.0/
Upstream-Name: KORVEX Stream Deck
Source: https://github.com/TU_USUARIO/KORVEX-Stream-Deck

Files: *
Copyright: 2024 KORVEX
License: MIT
EOF
chmod 644 "${ROOT}/usr/share/doc/${PKG_NAME}/copyright"

# =============================================================================
# DEBIAN/control
# =============================================================================
cat > "${ROOT}/DEBIAN/control" <<EOF
Package: ${PKG_NAME}
Version: ${PKG_VERSION}
Section: sound
Priority: optional
Architecture: ${PKG_ARCH}
Depends: python3 (>= 3.10),
         python3-pyqt6,
         pulseaudio-utils
Recommends: python3-pulsectl
Suggests: wireplumber
Maintainer: KORVEX <tu@email.com>
Homepage: https://github.com/TU_USUARIO/KORVEX-Stream-Deck
Description: Virtual audio mixer for streaming on Linux
 KORVEX Stream Deck is a modern PyQt6 audio mixer built on top of
 PipeWire/PulseAudio. It creates virtual sinks per channel, allows
 assigning applications to channels, provides independent volume
 control and mute per channel, and routes the master output to any
 physical device.
 .
 Features:
  - Virtual channels (System, Gaming, Music, ...)
  - App-to-channel assignment with persistence
  - Per-channel volume and mute
  - Real-time peak meters
  - Autostart at login
  - Modern Qt6-based UI
EOF
chmod 644 "${ROOT}/DEBIAN/control"

# =============================================================================
# postinst
# =============================================================================
cat > "${ROOT}/DEBIAN/postinst" <<'EOF'
#!/bin/bash
set -e

if command -v gtk-update-icon-cache >/dev/null 2>&1; then
    gtk-update-icon-cache -q -t -f /usr/share/icons/hicolor 2>/dev/null || true
fi

if command -v update-desktop-database >/dev/null 2>&1; then
    update-desktop-database -q /usr/share/applications 2>/dev/null || true
fi

# Instalar pulsectl si no está
if ! python3 -c "import pulsectl" 2>/dev/null; then
    echo "KORVEX: instalando dependencia 'pulsectl' vía pip..."
    pip3 install --break-system-packages 'pulsectl>=23.5.0,<25.0.0' 2>/dev/null || \
    pip3 install --user 'pulsectl>=23.5.0,<25.0.0' 2>/dev/null || \
    echo "KORVEX: AVISO — instala manualmente con: pip3 install --user pulsectl"
fi

echo ""
echo "  ✅ KORVEX Stream Deck instalado."
echo "  Búscalo en el menú como 'KORVEX Stream Deck' o ejecuta: korvex-streamdeck"
echo ""

exit 0
EOF
chmod 755 "${ROOT}/DEBIAN/postinst"

# =============================================================================
# prerm
# =============================================================================
cat > "${ROOT}/DEBIAN/prerm" <<'EOF'
#!/bin/bash
set -e
exit 0
EOF
chmod 755 "${ROOT}/DEBIAN/prerm"

# =============================================================================
# Construir
# =============================================================================
echo "📦 Empaquetando..."
dpkg-deb --build --root-owner-group "${ROOT}"

mv "${BUILD_DIR}/${PKG_NAME}_${PKG_VERSION}_${PKG_ARCH}.deb" .

echo ""
echo "✅ Listo: ${PKG_NAME}_${PKG_VERSION}_${PKG_ARCH}.deb"
ls -lh "${PKG_NAME}_${PKG_VERSION}_${PKG_ARCH}.deb"
echo ""
echo "Para instalar:"
echo "  sudo apt install ./${PKG_NAME}_${PKG_VERSION}_${PKG_ARCH}.deb"
echo ""
echo "Para desinstalar:"
echo "  sudo apt remove ${PKG_NAME}"
echo ""
