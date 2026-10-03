import asyncio
from typing import Any

from langchain_core.tools import tool


# Datos ficticios para simular una base de datos.
CLIENTES: list[dict[str, Any]] = [
    {"id": 101, "nombre": "Camila Monroy"},
    {"id": 102, "nombre": "Luciano Castillo"},
]

PEDIDOS: list[dict[str, Any]] = [
    {
        "id": 1,
        "cliente_id": 102,
        "producto": "Llaveros personalizados",
        "total": 15000,
        "fecha": "2026-09-10",
    },
    {
        "id": 2,
        "cliente_id": 102,
        "producto": "Miniaturas",
        "total": 10000,
        "fecha": "2026-09-20",
    },
    {
        "id": 3,
        "cliente_id": 102,
        "producto": "Portacelular",
        "total": 6500,
        "fecha": "2026-09-28",
    },
    {
        "id": 4,
        "cliente_id": 101,
        "producto": "Marcapáginas",
        "total": 8000,
        "fecha": "2026-09-25",
    },
]


@tool
async def buscar_cliente(nombre: str) -> dict[str, Any]:
    """Busca clientes por nombre completo o parcial, sin distinguir mayúsculas.

    Utiliza esta herramienta cuando el usuario mencione un nombre y necesites
    obtener su cliente_id para consultar pedidos. Devuelve los clientes
    coincidentes con su identificador. Si hay varias coincidencias, solicita
    al usuario que aclare cuál corresponde. Si no hay coincidencias, puedes
    intentar con una parte del nombre o pedir una aclaración.
    """
    await asyncio.sleep(0.1)

    consulta = nombre.strip().casefold()

    if not consulta:
        return {
            "estado": "error",
            "mensaje": "El nombre está vacío. Solicita un nombre al usuario.",
        }

    coincidencias = [
        cliente
        for cliente in CLIENTES
        if consulta in cliente["nombre"].casefold()
    ]

    if not coincidencias:
        return {
            "estado": "sin_resultados",
            "mensaje": "No se encontraron clientes. Prueba con un nombre parcial.",
        }

    return {
        "estado": "ok",
        "clientes": coincidencias,
    }


@tool
async def consultar_pedidos(cliente_id: int) -> dict[str, Any]:
    """Consulta todos los pedidos de un cliente mediante su identificador.

    Utiliza esta herramienta para conocer la cantidad de pedidos, el importe
    total gastado, los productos o el último pedido de un cliente.
    El cliente_id debe provenir del usuario, de buscar_cliente o del historial;
    nunca lo inventes. Devuelve los pedidos ordenados por fecha, la cantidad
    y el total en pesos argentinos. Si el identificador no existe, devuelve
    un error: busca al cliente por nombre o pide una aclaración.
    """
    await asyncio.sleep(0.1)

    cliente = next(
        (cliente for cliente in CLIENTES if cliente["id"] == cliente_id),
        None,
    )

    if cliente is None:
        return {
            "estado": "error",
            "mensaje": "No existe un cliente con ese identificador.",
        }

    pedidos = sorted(
        [
            pedido
            for pedido in PEDIDOS
            if pedido["cliente_id"] == cliente_id
        ],
        key=lambda pedido: pedido["fecha"],
    )

    return {
        "estado": "ok",
        "cliente_id": cliente_id,
        "nombre": cliente["nombre"],
        "moneda": "ARS",
        "cantidad": len(pedidos),
        "total": sum(pedido["total"] for pedido in pedidos),
        "pedidos": pedidos,
    }


HERRAMIENTAS = [buscar_cliente, consultar_pedidos]