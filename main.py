import argparse
import asyncio
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.runnables import RunnableConfig
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
from langgraph.errors import GraphRecursionError

from agent import crear_agente


CARPETA_PROYECTO = Path(__file__).resolve().parent
RUTA_MEMORIA = CARPETA_PROYECTO / "memoria.sqlite"
CARPETA_TRAZAS = CARPETA_PROYECTO / "trazas"


async def main(thread_id: str) -> None:
    """Ejecuta una conversación con memoria persistente."""
    CARPETA_TRAZAS.mkdir(exist_ok=True)

    config: RunnableConfig = {
        "configurable": {"thread_id": thread_id},
        "recursion_limit": 10,
    }

    async with AsyncSqliteSaver.from_conn_string(
        str(RUTA_MEMORIA)
    ) as checkpointer:
        agente = crear_agente(checkpointer)

        print(f"\nSesión: {thread_id}")
        print("Escribí una consulta o 'salir' para terminar.")
        print(
            "Ejemplo: ¿Cuántos pedidos tiene Luciano "
            "y cuánto gastó en total?\n"
        )

        while True:
            consulta = (
                await asyncio.to_thread(input, "Vos: ")
            ).strip()

            if consulta.casefold() in {"salir", "exit"}:
                print("Conversación guardada. ¡Hasta luego!")
                break

            if not consulta:
                continue

            traza: dict[str, Any] = {
                "thread_id": thread_id,
                "fecha": datetime.now(timezone.utc).isoformat(),
                "consulta": consulta,
                "eventos": [],
                "cantidad_llamadas_herramientas": 0,
                "estado": "en_progreso",
            }

            try:
                async for actualizacion in agente.astream(
                    {"messages": [HumanMessage(content=consulta)]},
                    config=config,
                    stream_mode="updates",
                ):
                    for nodo, datos in actualizacion.items():
                        for mensaje in datos.get("messages", []):
                            evento: dict[str, Any] = {
                                "nodo": nodo,
                                "tipo": mensaje.type,
                                "contenido": mensaje.content,
                            }

                            if isinstance(mensaje, AIMessage):
                                evento["llamadas_herramientas"] = (
                                    mensaje.tool_calls
                                )

                                traza[
                                    "cantidad_llamadas_herramientas"
                                ] += len(mensaje.tool_calls)

                                for llamada in mensaje.tool_calls:
                                    print(
                                        "\nHerramienta solicitada:",
                                        llamada["name"],
                                        llamada["args"],
                                    )

                                if not mensaje.tool_calls:
                                    print(
                                        f"\nAgente: {mensaje.content}\n"
                                    )

                            if mensaje.type == "tool":
                                evento["herramienta"] = mensaje.name
                                evento["tool_call_id"] = (
                                    mensaje.tool_call_id
                                )
                                print(
                                    "Resultado:",
                                    mensaje.content,
                                )

                            traza["eventos"].append(evento)

                traza["estado"] = "completado"

            except GraphRecursionError:
                traza["estado"] = "limite_de_recursion"
                traza["error"] = (
                    "El agente alcanzó el límite de pasos."
                )
                print(
                    "\nSe alcanzó el límite de pasos. "
                    "Revisemos la traza antes de continuar."
                )

            except Exception as error:
                traza["estado"] = "error"
                traza["error"] = type(error).__name__
                print(
                    f"\nLa ejecución falló: "
                    f"{type(error).__name__}: {error}"
                )

            finally:
                ruta_traza = (
                    CARPETA_TRAZAS
                    / f"traza_{uuid4().hex}.json"
                )

                ruta_traza.write_text(
                    json.dumps(
                        traza,
                        ensure_ascii=False,
                        indent=2,
                    ),
                    encoding="utf-8",
                )

                print(f"Traza guardada: {ruta_traza.name}\n")

            # Si hubo un fallo, detenemos esta ejecución para revisarlo.
            if traza["estado"] != "completado":
                break


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Agente de consultas con memoria persistente."
    )
    parser.add_argument(
        "--thread-id",
        default="sesion-demo",
        help="Identificador de la conversación que se quiere continuar.",
    )

    argumentos = parser.parse_args()

    asyncio.run(main(argumentos.thread_id))