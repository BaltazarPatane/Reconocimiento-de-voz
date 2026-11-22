# Bubba — Reconocimiento de voz para un robot bartender

Bubba usa el micrófono integrado de una notebook, **Vosk** para pasar voz a texto y un **Qwen de texto local** para identificar el trago pedido. El resultado se muestra en la terminal de VS Code, VSCodium o una consola normal.

**[Instalación sencilla para Windows](INSTALACION_WINDOWS.md)**

## Qué hace esta versión

1. Espera que se diga **Bubba**. También acepta las transcripciones **Buba** y **bu ba**.
2. Acepta el nombre y el pedido en una frase, o un saludo con el nombre y después el pedido.
3. Qwen decide si se pidió uno de los **cuatro tragos disponibles**.
4. Si reconoce un pedido válido, imprime **`Preparando [nombre del trago].`**. En cualquier otro caso imprime **`Error: ...`**.
5. Después de responder, vuelve a esperar el nombre, tanto si reconoció el trago como si hubo un error.

El mensaje «Preparando» es la salida de este prototipo en consola. Esta versión no se comunica con bombas, válvulas ni otra placa.

Todo el procesamiento se ejecuta en la computadora. Internet se necesita para instalar y descargar los modelos; durante el uso no se necesitan servicios remotos, cuentas ni claves API. El programa no guarda grabaciones.

## Tragos y alias

| Trago | Formas configuradas | Identificador interno |
| --- | --- | --- |
| Fernet con cola | fernet, Fernando, fernecito | `fernet_cola` |
| Gin tonic | gin tonic, gin con tónica, gincito | `gin_tonic` |
| Gancia batido | gancia, gancito, gancia batido | `gancia_batido` |
| Daiquiri de frutilla | daiquiri, daikiri, daiquiri de frutilla | `daiquiri_frutilla` |

Los alias son referencias para Qwen; el pedido puede estar expresado con otras palabras. No se hace un reemplazo automático de nombres: **«Fernando quiere un gin tonic»** debe interpretarse como Gin tonic, no como Fernet.

En este menú, «gancia» significa Gancia batido y «daiquiri» sin sabor significa frutilla. Otro sabor o cambios de receta no se sustituyen automáticamente por el trago de la carta: se consideran un error.

## Casos contemplados

| Entrada | Comportamiento esperado |
| --- | --- |
| «Un Fernando» sin haber llamado a Bubba | Se ignora; no se consulta a Qwen. |
| «Hola, Bubba» | Se activa y pregunta qué trago querés. |
| Después, «un Fernando, por favor» | `Preparando Fernet con cola.` |
| «Buenas tardes Buba, haceme un gincito» | `Preparando Gin tonic.` |
| «Bubba, un gancito» | `Preparando Gancia batido.` |
| «Bubba, un daikiri» | `Preparando Daiquiri de frutilla.` |
| «Bubba, no quiero un Fernando; haceme un gin tonic» | `Preparando Gin tonic.` |
| «Bubba, Fernando quiere un gin tonic» | `Preparando Gin tonic.` |
| «Bubba, me llamo Fernando» | `Error: ...` |
| «Bubba, no quiero un fernet» | `Error: ...` |
| «Bubba, un mojito» | `Error: ...` |
| «Bubba, un daiquiri de durazno» | `Error: ...` |
| «Bubba, un fernet y un gin tonic» | `Error: ...`; se admite un tipo por pedido. |
| «Bubba, dos fernecitos» | `Preparando 2 × Fernet con cola.` |
| «Bubba, ¿qué tragos tenés?» | `Error: ...`; esta versión clasifica pedidos, no conversa sobre la carta. |

El saludo con nombre abre una espera de **20 segundos**. Si vence, hay que llamar nuevamente a Bubba. Se puede cambiar con `--espera-pedido 30`.

No hay una conversación de aclaración ni memoria entre pedidos. Ante un pedido desconocido se muestra Error y se vuelve al estado de espera del nombre. El programa procesa una frase por vez; el micrófono se pausa mientras Qwen decide.

## Uso rápido

Después de completar la [instalación](INSTALACION_WINDOWS.md), desde la carpeta del proyecto:

```powershell
.\.venv\Scripts\python.exe asistente_voz.py
```

Prueba por texto, sin micrófono ni modelo Vosk:

```powershell
.\.venv\Scripts\python.exe asistente_voz.py --texto "Bubba, un Fernando"
.\.venv\Scripts\python.exe asistente_voz.py --texto "Hola Buba" --texto "Un gincito"
```

Para mostrar lo que transcribió Vosk:

```powershell
.\.venv\Scripts\python.exe asistente_voz.py --debug
```

Detener el programa: **Ctrl+C**.

En Linux, instalá `python3-venv`, `python3-pip` y `libportaudio2`, creá el entorno con `python3 -m venv .venv` e instalá `requirements.txt`. Usá `.venv/bin/python` en lugar de `.\.venv\Scripts\python.exe`.

## Archivos

| Archivo | Función |
| --- | --- |
| `asistente_voz.py` | Captura de audio, activación, clasificación y salida en consola. |
| `requirements.txt` | Dependencias de Python. |
| `pruebas_bubba.py` | Pruebas de lógica y consultas opcionales al Qwen real. |
| `INSTALACION_WINDOWS.md` | Guía de instalación y solución de problemas. |
| `LICENSE` | Licencia MIT de este código. |

Los modelos se descargan por separado y no se incluyen en el repositorio.

## Modelos y configuración

- Vosk inicial: `vosk-model-small-es-0.42`, español.
- Qwen inicial: `qwen3:1.7b`, ejecutado localmente mediante Ollama.
- Conexión local: `http://127.0.0.1:11434/api/chat`.
- `TRAGOS`, al inicio de `asistente_voz.py`, contiene el menú y los alias.
- `--microfono NUMERO` elige una entrada de audio.
- `--modelo-vosk RUTA` permite usar otro modelo Vosk descomprimido.
- `--modelo-qwen NOMBRE` elige otro Qwen descargado en Ollama; requiere volver a evaluar la interpretación.
- `--alias-nombre "FORMA_OBSERVADA"` agrega una transcripción del nombre obtenida con tu micrófono.

La velocidad depende del procesador, la memoria y la aceleración disponible. La primera consulta puede tardar más porque se carga Qwen.

## Pruebas

Pruebas de lógica, consola y respuestas HTTP simuladas, sin modelos ni micrófono:

```powershell
.\.venv\Scripts\python.exe pruebas_bubba.py
```

Para consultar además al Qwen real instalado en Ollama:

```powershell
.\.venv\Scripts\python.exe pruebas_bubba.py --qwen-real
```

Estas pruebas evalúan los 12 alias, negaciones, el nombre Fernando como persona y pedidos fuera del menú. Las pruebas con modelo pueden tardar varios minutos. Las expectativas de la tabla deben comprobarse también con la voz real; las pruebas por texto no validan el reconocimiento del micrófono.

En esta versión pasaron **24 pruebas de lógica y conexión HTTP simulada** y **23 frases con los pesos reales de Qwen3:1.7b ejecutados en CPU mediante llama.cpp**. La prueba opcional del repositorio usa Ollama. La captura con el micrófono de la notebook y la ejecución en Windows todavía deben verificarse en ese equipo.

## Límite actual del reconocimiento de voz

Vosk recibe frases libres, pero su diccionario no contiene cualquier nombre o marca. En el modelo pequeño comprobado están `bubba` y `fernando`, pero faltan las formas exactas `fernet`, `gancia` y `daiquiri`. Puede transcribir esos sonidos con otras palabras, y las pruebas previas con voz sintética produjeron errores.

Usá `--debug` y mirá la línea `Vosk:`. Si la transcripción es incorrecta, Qwen recibe ese error. Los alias de Python no agregan pronunciaciones al diccionario de Vosk: una mala transcripción puede requerir calibración, adaptación del modelo o probar otro modelo español.

## Software abierto

El código de este repositorio es MIT. Vosk y los modelos seleccionados se publican con Apache 2.0; sounddevice, PortAudio y Ollama usan MIT, y Python usa su licencia PSF. Para una distribución libre del editor se puede usar [VSCodium](https://vscodium.com/).

Fuentes oficiales: [Vosk](https://github.com/alphacep/vosk-api), [modelos](https://alphacephei.com/vosk/models), [adaptación](https://alphacephei.com/vosk/adaptation), [Ollama](https://github.com/ollama/ollama), [Qwen3:1.7b](https://ollama.com/library/qwen3:1.7b), [sounddevice](https://python-sounddevice.readthedocs.io/).
