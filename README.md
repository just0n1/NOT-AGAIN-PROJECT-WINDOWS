# 🛡️ Not Again (Windows v1.0)

> **"Sobre toda cosa guardada, guarda tu corazón; porque de él mana la vida."**  
> — *Proverbios 4:23*

**Not Again** es un guardián de escritorio en segundo plano para Windows, diseñado para combatir la adicción a la pornografía mediante **visión artificial en tiempo real (IA local)**, **análisis semántico de títulos** y una **pantalla de enfriamiento ineludible con versículos bíblicos**.

Es **100% privado, local y ético**: no envía telemetría ni capturas a servidores externos. Todo el procesamiento corre en tu propia GPU/CPU.

---

## ✨ Características Principales

1. **Visión por Computadora Local (IA con ViT ONNX):**
   - Escanea el navegador activo mediante recortes inteligentes del reproductor a ~30-40 ms.
   - Aceleración por hardware mediante **DirectML (NVIDIA / AMD / Intel)** sin necesidad de CUDA pesado.
   - Detección binaria instantánea (>= 90%) y detección suave por acumulación de ventana deslizante para videoclips y fast-cuts.
2. **Capa Semántica y Control de Disparadores:**
   - Cierre inmediato al detectar dominios pornográficos o palabras explícitas en el título de la ventana.
   - Monitorización de artistas de riesgo y videoclips musicales, respetando contenidos seguros (audios, letras, instrumentales).
   - Inmunidad a tutoriales de producción musical y páginas de navegación limpia para prevenir falsos positivos.
3. **Pantalla de Bloqueo Ineludible (60 Segundos):**
   - Al detectar contenido explícito, mata el proceso del navegador inmediatamente (`taskkill /F`).
   - Lanza una pantalla completa bloqueada durante 60 segundos con versículos bíblicos para cortar el bucle de dopamina y forzar una pausa consciente. Sin atajos de escape (`Alt+F4` y `Esc` interceptados).
4. **Panel de Control Glassmorphism (Dashboard):**
   - Interfaz gráfica oscura con contador de días en victoria, racha de pureza, lista de bloqueo personalizada y registro histórico de eventos.
5. **Anti-Tamper (Resistencia a Cierres Impulsivos):**
   - Bloqueo de descriptores en memoria para impedir borrados o ediciones en caliente durante momentos de debilidad.
   - Tareas programadas de auto-reinicio (Watchdog) en Windows.

---

## 📋 Requisitos del Sistema

- **Sistema Operativo:** Windows 10 o Windows 11 (64-bit).
- **Python:** Python 3.10 o 3.11 recomendado.
- **Hardware:** GPU compatible con DirectX 12 / DirectML (NVIDIA, AMD o Intel) o CPU multi-núcleo moderna.

---

## 🚀 Guía de Instalación Rápida (Windows)

Sigue estos sencillos pasos desde la terminal de Windows (PowerShell o CMD):

### 1. Clonar el repositorio
```bash
git clone https://github.com/TU_USUARIO/not_again.git
cd not_again
```

### 2. Instalar dependencias
Asegúrate de tener Python instalado y agregado al PATH de Windows:
```bash
pip install -r requirements.txt
```

### 3. Descargar el modelo de IA
Para que el repositorio sea ligero, los pesos del modelo ONNX se descargan automáticamente con un script:
```bash
python download_model.py
```
*(Opcional: Si dispones de una tarjeta gráfica dedicada como RTX/GTX, puedes ejecutar `python download_model_fp32.py` para mayor precisión).*

---

## 🎮 Uso del Guardián

### Iniciar el Guardián:
- **Modo prueba (sin cerrar ventanas):**
  ```bash
  python guardian.py --dry-run
  ```
- **Modo activo silencioso:**  
  Haz doble clic en `start_background.bat` o ejecuta:
  ```bash
  pythonw guardian.py
  ```

### Abrir el Panel de Control:
Haz doble clic en `abrir_panel.bat` o ejecuta:
```bash
python dashboard.py
```

### Instalación como Servicio Automático de Windows:
- Para que se inicie solo cada vez que enciendes el PC: haz clic derecho en `install_autostart.bat` y selecciona **Ejecutar como Administrador**.
- Para activar el vigilante que lo revive si se intenta cerrar: haz clic derecho en `install_watchdog.bat` y selecciona **Ejecutar como Administrador**.

---

## 🛡️ Estructura del Proyecto

```text
not_again/
├── assets/                  # Logos e iconos del proyecto
├── models/                  # Carpeta de modelos ONNX (descargados por script)
├── guardian.py              # Bucle principal de vigilancia en tiempo real
├── detector.py              # Inferencia de IA mediante onnxruntime-directml
├── lockscreen.py            # Pantalla completa de bloqueo con versículos
├── dashboard.py             # Panel de control e interfaz gráfica
├── verses.json              # Base de datos de versículos bíblicos
├── triggers.json            # Palabras clave y artistas vigilados
├── user_blocklist.txt       # Lista negra personalizable por el usuario
├── download_model.py        # Descarga automática del modelo estándar
├── download_model_fp32.py   # Descarga automática del modelo de alta precisión
├── install_autostart.bat    # Registro en Windows al iniciar sesión
├── install_watchdog.bat     # Vigilante de auto-resurrección
├── abrir_panel.bat          # Acceso directo al Dashboard
└── requirements.txt         # Librerías necesarias de Python
```

---

## 📜 Licencia y Propósito

Este proyecto fue creado con una motivación de fe, dominio propio y ayuda comunitaria. Es software libre para que cualquier persona que luche por guardar su corazón y su mente pueda instalarlo, auditarlo y adaptarlo a su vida.
