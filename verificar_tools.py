import asyncio
import json

from tools import buscar_cliente, consultar_pedidos


async def main() -> None:
    # Buscar un cliente por su nombre.
    resultado_cliente = await buscar_cliente.ainvoke(
        {"nombre": "Luciano"}
    )

    assert resultado_cliente["estado"] == "ok"
    cliente_id = resultado_cliente["clientes"][0]["id"]
    assert cliente_id == 102

    # Usar el identificador obtenido para consultar pedidos.
    resultado_pedidos = await consultar_pedidos.ainvoke(
        {"cliente_id": cliente_id}
    )

    assert resultado_pedidos["estado"] == "ok"
    assert resultado_pedidos["cantidad"] == 3
    assert resultado_pedidos["total"] == 31500
    assert resultado_pedidos["pedidos"][-1]["id"] == 3

    # Comprobar cómo responden ante datos incorrectos.
    cliente_inexistente = await buscar_cliente.ainvoke(
        {"nombre": "Cliente inexistente"}
    )
    assert cliente_inexistente["estado"] == "sin_resultados"

    identificador_invalido = await consultar_pedidos.ainvoke(
        {"cliente_id": 999}
    )
    assert identificador_invalido["estado"] == "error"

    nombre_vacio = await buscar_cliente.ainvoke(
        {"nombre": " "}
    )
    assert nombre_vacio["estado"] == "error"

    print(json.dumps(
        resultado_pedidos,
        ensure_ascii=False,
        indent=2,
    ))
    print("\nOK: todas las comprobaciones de herramientas pasaron.")


if __name__ == "__main__":
    asyncio.run(main())