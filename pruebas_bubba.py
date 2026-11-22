#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Pruebas locales. --qwen-real agrega consultas al modelo instalado en Ollama."""

import contextlib
from http.server import BaseHTTPRequestHandler, HTTPServer
import io
import json
import sys
import threading
import unittest
from unittest.mock import patch

import asistente_voz as app


QWEN_REAL = "--qwen-real" in sys.argv
if QWEN_REAL:
    sys.argv.remove("--qwen-real")


def pedido(trago="fernet_cola", cantidad=1):
    return {"trago": trago, "cantidad": cantidad}


def desconocido():
    return {"trago": None, "cantidad": None}


class PruebasConversacion(unittest.TestCase):
    def setUp(self):
        self.ahora = 100.0
        self.conversacion = app.ConversacionBubba(reloj=lambda: self.ahora)
        self.salida = contextlib.redirect_stdout(io.StringIO())
        self.salida.__enter__()

    def tearDown(self):
        self.salida.__exit__(None, None, None)

    def test_pedido_sin_nombre_no_consulta_qwen(self):
        with patch.object(app, "interpretar_texto") as qwen:
            self.assertEqual(self.conversacion.procesar("Un Fernando")["estado"], "ignorado")
            qwen.assert_not_called()

    def test_distintos_saludos_y_formas_del_nombre(self):
        for frase in ["Bubba", "Hola Buba", "Buenas tardes BUBBA", "Qué onda, bu ba"]:
            with self.subTest(frase=frase), patch.object(app, "interpretar_texto") as qwen:
                self.conversacion.cerrar()
                self.assertEqual(self.conversacion.procesar(frase)["estado"], "activado")
                self.assertTrue(self.conversacion.activa)
                qwen.assert_not_called()

    def test_nombre_completo_sin_coincidencias_parciales(self):
        for frase in ["bubbaloo", "bubbas", "buda", "tuba"]:
            with self.subTest(frase=frase):
                self.assertFalse(app.buscar_nombre(frase)[0])

    def test_pedido_en_la_misma_frase_del_nombre(self):
        frase = "Buenas tardes Bubba, haceme un Fernando"
        with patch.object(app, "interpretar_texto", return_value=pedido()) as qwen:
            evento = self.conversacion.procesar(frase)
        self.assertEqual(evento["resultado"], pedido())
        self.assertEqual(qwen.call_args.args[0], frase)
        self.assertFalse(self.conversacion.activa)

    def test_pedido_despues_del_saludo(self):
        self.conversacion.procesar("Hola Buba")
        with patch.object(app, "interpretar_texto", return_value=pedido("gin_tonic")):
            evento = self.conversacion.procesar("Un gincito")
        self.assertEqual(evento["resultado"]["trago"], "gin_tonic")
        self.assertFalse(self.conversacion.activa)

    def test_un_error_tambien_cierra_la_consulta(self):
        self.conversacion.procesar("Bubba")
        with patch.object(app, "interpretar_texto", return_value=desconocido()) as qwen:
            evento = self.conversacion.procesar("Un mojito")
            self.assertEqual(evento["resultado"], desconocido())
            self.assertEqual(self.conversacion.procesar("Un Fernando")["estado"], "ignorado")
            self.assertEqual(qwen.call_count, 1)

    def test_despues_de_un_pedido_se_necesita_otro_llamado(self):
        with patch.object(app, "interpretar_texto", return_value=pedido()) as qwen:
            self.conversacion.procesar("Bubba, un Fernando")
            self.assertEqual(self.conversacion.procesar("Otro fernet")["estado"], "ignorado")
            self.assertEqual(qwen.call_count, 1)

    def test_vence_la_espera(self):
        self.conversacion.procesar("Bubba")
        self.ahora += app.ESPERA_PEDIDO + 1
        with patch.object(app, "interpretar_texto") as qwen:
            self.assertEqual(self.conversacion.procesar("Un Fernando")["estado"], "ignorado")
            qwen.assert_not_called()

    def test_error_de_ollama_tambien_reinicia_la_consulta(self):
        with patch.object(app, "interpretar_texto", side_effect=RuntimeError("sin servidor")):
            with self.assertRaises(RuntimeError):
                self.conversacion.procesar("Bubba, un Fernando")
        self.assertFalse(self.conversacion.activa)

    def test_alias_de_nombre_observado(self):
        conversacion = app.ConversacionBubba(alias_nombres=(*app.ALIAS_NOMBRE, "buva"))
        self.assertEqual(conversacion.procesar("Hola Buva")["estado"], "activado")

    def test_modo_texto_sin_dependencias_de_audio(self):
        salida = io.StringIO()
        with patch.dict(sys.modules, {"vosk": None, "sounddevice": None}):
            with patch.object(sys, "argv", ["asistente_voz.py", "--texto", "Hola Bubba", "--texto", "Un Fernando"]):
                with patch.object(app, "interpretar_texto", return_value=pedido()):
                    with contextlib.redirect_stdout(salida):
                        self.assertEqual(app.main(), 0)
        self.assertIn("Preparando Fernet con cola.", salida.getvalue())


class PruebasResultados(unittest.TestCase):
    def test_solo_cuatro_tragos_y_tres_alias_por_trago(self):
        self.assertEqual(set(app.TRAGOS), {"fernet_cola", "gin_tonic", "gancia_batido", "daiquiri_frutilla"})
        self.assertTrue(all(len(t["alias"]) == 3 for t in app.TRAGOS.values()))

    def test_preparando_el_trago_especifico(self):
        for identificador, trago in app.TRAGOS.items():
            with self.subTest(trago=identificador):
                salida = io.StringIO()
                with contextlib.redirect_stdout(salida):
                    app.mostrar_resultado(pedido(identificador))
                self.assertEqual(salida.getvalue(), f"Preparando {trago['nombre']}.\n")

    def test_desconocido_muestra_error_y_nunca_preparando(self):
        salida = io.StringIO()
        with contextlib.redirect_stdout(salida):
            app.mostrar_resultado(desconocido())
        self.assertIn("Error:", salida.getvalue())
        self.assertNotIn("Preparando", salida.getvalue())

    def test_trago_eliminado_no_es_valido(self):
        self.assertEqual(app.validar_resultado({"estado": "pedido_valido", **pedido("negroni")}), desconocido())

    def test_cantidades_invalidas(self):
        for cantidad in [0, -1, True, "dos", 1.5]:
            with self.subTest(cantidad=cantidad), self.assertRaises(RuntimeError):
                app.validar_resultado({"estado": "pedido_valido", **pedido(cantidad=cantidad)})

    def test_pedido_incompleto_es_error(self):
        self.assertEqual(app.validar_resultado({"estado": "pedido_valido", **pedido(cantidad=None)}), desconocido())
        self.assertEqual(app.validar_resultado({"estado": "pedido_valido", **pedido(None, 2)}), desconocido())

    def test_estado_invalido_no_prepara_aunque_haya_un_trago(self):
        resultado = app.validar_resultado({"estado": "fuera_del_menu", **pedido("gin_tonic")})
        self.assertEqual(resultado, desconocido())

    def test_cantidad_varios_del_mismo_trago(self):
        salida = io.StringIO()
        with contextlib.redirect_stdout(salida):
            app.mostrar_resultado(pedido(cantidad=2))
        self.assertEqual(salida.getvalue(), "Preparando 2 × Fernet con cola.\n")


class PruebasHTTP(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.estado = {}
        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *args):
                pass
            def do_POST(self):
                cls.estado["peticion"] = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
                self.send_response(cls.estado.get("status", 200))
                self.end_headers()
                cuerpo = cls.estado.get("cuerpo", json.dumps({"message": {"content": json.dumps({"estado": "pedido_valido", **pedido("gin_tonic", 2)})}}))
                self.wfile.write(cuerpo.encode())
        cls.servidor = HTTPServer(("127.0.0.1", 0), Handler)
        cls.hilo = threading.Thread(target=cls.servidor.serve_forever, daemon=True)
        cls.hilo.start()

    @classmethod
    def tearDownClass(cls):
        cls.servidor.shutdown()
        cls.servidor.server_close()
        cls.hilo.join()

    def setUp(self):
        self.estado.clear()
        self.parche = patch.object(app, "URL_OLLAMA", f"http://127.0.0.1:{self.servidor.server_port}/api/chat")
        self.parche.start()

    def tearDown(self):
        self.parche.stop()

    def test_conserva_negacion_y_no_reemplaza_fernando(self):
        frase = "Fernando no quiere fernet; haceme dos gin con tónica"
        self.assertEqual(app.interpretar_texto(frase), pedido("gin_tonic", 2))
        self.assertEqual(self.estado["peticion"]["messages"][-1]["content"], frase)
        self.assertFalse(self.estado["peticion"]["think"])

    def test_modelo_faltante(self):
        self.estado.update(status=404, cuerpo='{"error":"model not found"}')
        with self.assertRaisesRegex(RuntimeError, "ollama pull"):
            app.interpretar_texto("Un Fernando")

    def test_json_roto(self):
        self.estado["cuerpo"] = "no es json"
        with self.assertRaises(RuntimeError):
            app.interpretar_texto("Un Fernando")

    def test_contenido_del_modelo_roto(self):
        self.estado["cuerpo"] = json.dumps({"message": {"content": "sin decision"}})
        with self.assertRaises(RuntimeError):
            app.interpretar_texto("Un Fernando")


class PruebasAudio(unittest.TestCase):
    def test_audio_perdido_no_se_interpreta(self):
        class Reconocedor:
            def __init__(self, *args):
                pass
            def AcceptWaveform(self, datos):
                raise AssertionError("No debe procesarse audio incompleto")
        class Flujo:
            def __init__(self, **kwargs):
                self.callback = kwargs["callback"]
            def __enter__(self):
                for _ in range(21):
                    self.callback(b"\x00\x00", 1, None, False)
            def __exit__(self, *args):
                pass
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertIsNone(app.escuchar_frase(type("SD", (), {"RawInputStream": Flujo}),
                                               Reconocedor, object(), None, 48000))


@unittest.skipUnless(QWEN_REAL, "Agregá --qwen-real para probar el modelo instalado")
class PruebasQwenReal(unittest.TestCase):
    def test_los_doce_alias(self):
        for identificador, trago in app.TRAGOS.items():
            for alias in trago["alias"]:
                with self.subTest(alias=alias):
                    self.assertEqual(app.interpretar_texto(f"Haceme un {alias}, por favor"), pedido(identificador))

    def test_negacion_y_correccion(self):
        self.assertEqual(app.interpretar_texto("No quiero un Fernando; haceme dos gin con tónica"), pedido("gin_tonic", 2))

    def test_fernando_como_persona(self):
        self.assertEqual(app.interpretar_texto("Fernando quiere un gincito"), pedido("gin_tonic"))
        self.assertEqual(app.interpretar_texto("Me llamo Fernando"), desconocido())

    def test_nombre_y_plural(self):
        self.assertEqual(app.interpretar_texto("Buenas tardes Bubba, ¿me preparás dos fernecitos?"), pedido(cantidad=2))

    def test_fuera_de_menu_y_no_pedidos(self):
        for frase in ["Un Negroni", "Un mojito", "Un daiquiri de durazno", "No quiero un fernet",
                      "Un fernet y un gin tonic", "¿Qué tragos tenés?", "Un gin con pomelo"]:
            with self.subTest(frase=frase):
                self.assertEqual(app.interpretar_texto(frase), desconocido())


if __name__ == "__main__":
    unittest.main(verbosity=2)
