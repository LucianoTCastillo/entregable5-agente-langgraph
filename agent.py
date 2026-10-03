import os

from dotenv import load_dotenv
from langchain_core.messages import BaseMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
from langgraph.graph import END, START, MessagesState, StateGraph
from langgraph.graph.state import CompiledStateGraph
from langgraph.prebuilt import ToolNode, tools_condition

from tools import HERRAMIENTAS


class EstadoAgente(MessagesState):
    """Estado que conserva los mensajes de la conversación."""

    pass


INSTRUCCIONES = """
Sos un asistente de consultas de clientes y pedidos de Ca'Lu.
Los datos disponibles son ficticios y se utilizan para un ejercicio.

Respondé en español y utilizá las herramientas cuando necesites
consultar información de clientes o pedidos.

Nunca inventes identificadores, pedidos ni importes.
Si solo conocés el nombre del cliente, buscá su identificador
antes de consultar sus pedidos.

Si una búsqueda no encuentra resultados, intentá con una parte
del nombre cuando tenga sentido. Si sigue sin haber resultados,
pedí una aclaración.

Si hay varios clientes coincidentes, pedí al usuario que indique
a cuál se refiere antes de consultar pedidos.

Si una herramienta devuelve un error, revisá el resultado y
corregí los argumentos si tenés información suficiente.
Si no podés resolverlo, explicá el problema y pedí una aclaración.
No repitas indefinidamente una consulta que falla.

Usá el historial para interpretar preguntas como "¿y el último?".
Los importes están expresados en pesos argentinos.
Respondé de forma breve y basada en los resultados disponibles.
"""


def crear_agente(
    checkpointer: AsyncSqliteSaver,
) -> CompiledStateGraph:
    """Construye el grafo y lo conecta con la persistencia."""
    load_dotenv()

    if not os.getenv("OPENAI_API_KEY"):
        raise ValueError(
            "Falta OPENAI_API_KEY. Configurala en el archivo .env."
        )

    modelo = ChatOpenAI(
        model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        temperature=0,
        timeout=30,
        max_retries=0,
    )

    modelo_con_herramientas = modelo.bind_tools(HERRAMIENTAS)

    async def llamar_modelo(
        estado: EstadoAgente,
    ) -> dict[str, list[BaseMessage]]:
        """Envía las instrucciones y el historial al modelo."""
        mensajes = [
            SystemMessage(content=INSTRUCCIONES),
            *estado["messages"],
        ]

        respuesta = await modelo_con_herramientas.ainvoke(mensajes)

        return {"messages": [respuesta]}

    grafo = StateGraph(EstadoAgente)

    grafo.add_node("modelo", llamar_modelo)
    grafo.add_node(
        "tools",
        ToolNode(HERRAMIENTAS, handle_tool_errors=True),
    )

    grafo.add_edge(START, "modelo")

    grafo.add_conditional_edges(
        "modelo",
        tools_condition,
        {
            "tools": "tools",
            "__end__": END,
        },
    )

    grafo.add_edge("tools", "modelo")

    return grafo.compile(checkpointer=checkpointer)