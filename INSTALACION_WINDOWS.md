# Instalar Bubba en Windows

Esta guía usa Windows 10 22H2 o Windows 11 de 64 bits, el micrófono integrado de la notebook y la terminal de VS Code o VSCodium.

## 1. Instalar los programas

- **Python 3.13 de 64 bits:** [descargas oficiales para Windows](https://www.python.org/downloads/windows/). Buscá Python 3.13 y **Windows installer (64-bit)**. En el instalador, habilitá **Add python.exe to PATH** y el lanzador `py`.
- **Ollama:** [instalador para Windows](https://ollama.com/download/windows). Abrilo después de instalarlo; queda ejecutándose en segundo plano.
- **Editor:** VS Code, si ya lo usás, o [VSCodium](https://vscodium.com/) para una distribución libre. No se necesitan extensiones de IA.

Si ya tenés Python 3.12, también sirve: reemplazá `py -3.13` por `py -3.12` en el paso 3. El código fue probado con Python 3.12; la guía también permite usar la rama 3.13.

## 2. Guardar los archivos y abrir la carpeta

Creá una carpeta llamada `Reconocimiento-de-voz` y guardá en ella estos archivos del repositorio, usando **Download raw file** en la página de cada archivo:

- [asistente_voz.py](asistente_voz.py)
- [requirements.txt](requirements.txt)
- Opcional: [pruebas_bubba.py](pruebas_bubba.py)

Comprobá que no queden nombres como `asistente_voz.py.txt`.

Abrí esa carpeta desde **Archivo → Abrir carpeta** y después **Terminal → Nueva terminal**. Los siguientes comandos se ejecutan en esa terminal, usando PowerShell.

Si preferís Git y ya lo tenés instalado, podés obtener todos los archivos con:

```powershell
git clone https://github.com/BaltazarPatane/Reconocimiento-de-voz.git
```

## 3. Instalar las bibliotecas de Python

```powershell
py -3.13 --version
py -3.13 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Se usa directamente el Python de `.venv`; no hace falta activar scripts de PowerShell ni cambiar su política de ejecución. En Windows, sounddevice instala PortAudio con pip.

## 4. Descargar Qwen

Con Ollama abierto:

```powershell
ollama pull qwen3:1.7b
```

Esperá a que termine. Es una descarga de aproximadamente 1,4 GB, además de los archivos del programa Ollama. Durante el reconocimiento se utiliza ese modelo local, sin iniciar sesión ni pagar una API.

Si `ollama` no se reconoce después de instalarlo, cerrá el editor y volvé a abrirlo.

## 5. Descargar el modelo de voz en español

Desde la carpeta del proyecto:

```powershell
Invoke-WebRequest -Uri "https://alphacephei.com/vosk/models/vosk-model-small-es-0.42.zip" -OutFile "modelo-vosk.zip"
Expand-Archive -Path ".\modelo-vosk.zip" -DestinationPath "."
```

El modelo ocupa unos 39 MB de descarga. Al terminar, debe existir `vosk-model-small-es-0.42\am\final.mdl` dentro de la carpeta del proyecto. Si ya tenés ese modelo correctamente descomprimido, omití este paso. El archivo `modelo-vosk.zip` puede borrarse después.

## 6. Comprobar Qwen por texto

Esta prueba no abre el micrófono:

```powershell
.\.venv\Scripts\python.exe asistente_voz.py --texto "Bubba, haceme un Fernando"
```

La decisión esperada es:

```text
Preparando Fernet con cola.
```

Probá también un pedido fuera del menú:

```powershell
.\.venv\Scripts\python.exe asistente_voz.py --texto "Bubba, un mojito"
```

Debe mostrar `Error: ...`. Después de cada decisión hay que llamar nuevamente a Bubba.

## 7. Usar el micrófono integrado

En los ajustes de sonido de Windows, elegí el micrófono de la notebook como entrada y comprobá que detecta tu voz. Habilitá el acceso al micrófono para las aplicaciones de escritorio.

Ejecutá:

```powershell
.\.venv\Scripts\python.exe asistente_voz.py
```

Decí **«Hola, Bubba»**, hacé una pausa y, cuando pregunte qué trago querés, decí **«un Fernando»**. También podés decir todo junto: **«Bubba, preparame un gincito»**.

Si elige otra entrada, listá los micrófonos:

```powershell
.\.venv\Scripts\python.exe asistente_voz.py --listar-microfonos
```

Después agregá `--microfono NUMERO` al comando, con el número real del micrófono de la notebook.

Para comprobar lo que escuchó Vosk:

```powershell
.\.venv\Scripts\python.exe asistente_voz.py --debug
```

Vosk puede transcribir mal nombres de tragos; la versión necesita pruebas con tu voz. El README explica esta limitación y cómo ajustar una transcripción del nombre con `--alias-nombre`.

## Qué debe quedar abierto

- **Ollama**, ejecutándose en segundo plano.
- **La terminal donde corre el programa**; podés minimizar el editor.
- **La notebook encendida y sin suspenderse**, con el micrófono habilitado.

No hace falta mantener un navegador, ChatGPT ni una conversación de Ollama abiertos. Internet ya no es necesario después de las instalaciones y descargas.

Para detenerlo, usá **Ctrl+C** en la terminal. Para iniciar otra vez, repetí el comando del paso 7.

## Problemas frecuentes

| Problema | Qué revisar |
| --- | --- |
| `py -3.13` no encuentra Python | Instalá esa versión o usá `py -3.12` si ya tenés 3.12. |
| Error al consultar Ollama | Abrí Ollama. Si hace falta, usá otra terminal con `ollama serve` y dejala abierta. Si el puerto ya está ocupado, normalmente ya hay un servidor. |
| Falta el modelo Qwen | Ejecutá `ollama pull qwen3:1.7b` y esperá a que termine. |
| Falta el modelo Vosk | Revisá el paso 5 y que la carpeta del modelo no esté duplicada dentro de otra con el mismo nombre. |
| No se activa o reconoce otro trago | Probá `--debug`, revisá el micrófono elegido y la transcripción `Vosk:`. |
| Qwen demora más que el tiempo de espera | La primera carga es más lenta. Podés agregar `--timeout 240` al comando. |

Para volver a consultar la descripción, los alias y los casos previstos, abrí el [README](README.md).
