# Preentrega 5: agente con memoria persistente

Agente asíncrono desarrollado con Python y LangGraph para consultar
clientes y pedidos ficticios de Ca’Lu Impresiones 3D.

El modelo de OpenAI decide qué herramientas utilizar. El grafo permite
ejecutarlas, devolver sus resultados al modelo y continuar hasta obtener
una respuesta o solicitar una aclaración.

## Tecnologías

- Python 3.12.10.
- LangGraph: StateGraph y estado derivado de MessagesState.
- ChatOpenAI con herramientas vinculadas mediante bind_tools().
- Herramientas personalizadas con el decorador @tool.
- Persistencia SQLite mediante AsyncSqliteSaver.
- asyncio para ejecución asíncrona.

Se utiliza AsyncSqliteSaver, la variante asíncrona de SqliteSaver,
para mantener compatibilidad con la ejecución del agente.

## Archivos

| Archivo | Función |
|---|---|
| tools.py | Herramientas y datos ficticios de clientes y pedidos. |
| agent.py | Configuración del modelo y construcción del grafo. |
| main.py | Conversación por terminal, persistencia y registro de trazas. |
| verificar_tools.py | Comprobaciones de herramientas sin llamadas a OpenAI. |
| requirements.txt | Versiones de las dependencias. |
| .env.example | Plantilla de configuración sin credenciales. |
| .gitignore | Exclusión de claves, entorno virtual y memoria local. |

## Instalación en Windows PowerShell

Desde la carpeta del proyecto:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

También puede utilizarse el entorno virtual creado por PyCharm.

## Configuración

Copiar la plantilla:

```powershell
Copy-Item .env.example .env
```

Editar .env con una API key propia que tenga acceso al modelo y saldo:

```dotenv
OPENAI_API_KEY=colocar_clave_real
OPENAI_MODEL=gpt-4o-mini
```

El modelo puede cambiarse mediante OPENAI_MODEL por otro modelo
compatible con llamadas a herramientas y disponible en la cuenta.

La ejecución con OpenAI consume créditos de la API.
La API key no debe subirse al repositorio.

## Ejecución

```powershell
python main.py --thread-id prueba-1
```

Escribir una consulta cuando aparezca "Vos:".
Para terminar, escribir "salir".

## Funcionamiento del grafo

1. El nodo modelo recibe las instrucciones y el historial.
2. El modelo puede solicitar una herramienta.
3. tools_condition dirige la ejecución al nodo tools o finaliza.
4. ToolNode ejecuta las herramientas solicitadas.
5. Los resultados regresan al nodo modelo.
6. El ciclo continúa hasta que el modelo responde.

La selección de herramientas depende del modelo; no se utilizan
rutas manuales basadas en palabras del usuario.

Las instrucciones indican cómo actuar ante resultados incompletos,
clientes ambiguos o errores. Su comportamiento requiere validación
con el modelo real.

Se establece recursion_limit=10 para limitar los pasos del grafo.

## Prueba de herramientas sin API

```powershell
python verificar_tools.py
```

Verifica:

- Búsqueda de Luciano Castillo.
- Recuperación de su identificador: 102.
- Consulta de sus 3 pedidos por un total de ARS 31.500.
- Orden de pedidos por fecha.
- Respuestas ante nombres vacíos, clientes inexistentes
  e identificadores inválidos.

Estas comprobaciones pasaron localmente.
No requieren una API key ni consumen créditos.

## Prueba pendiente de ejecución con el modelo

Utilizar una sesión nueva:

```powershell
python main.py --thread-id evaluacion-1
```

Consultar:

"¿Cuántos pedidos tiene Luciano y cuánto gastó en total?"

El comportamiento esperado es:

1. Llamada a buscar_cliente para obtener el identificador.
2. Llamada a consultar_pedidos con el identificador obtenido.
3. Respuesta indicando 3 pedidos y ARS 31.500.

Comprobar en la traza que hubo al menos dos llamadas a herramientas
y que los resultados se utilizaron correctamente.

## Prueba pendiente de memoria persistente

Después de la consulta anterior:

1. Escribir "salir".
2. Ejecutar nuevamente el programa con el mismo thread_id:

```powershell
python main.py --thread-id evaluacion-1
```

3. Preguntar: "¿Y cuál fue su último pedido?"

El agente debería recuperar el contexto de Luciano e indicar
el pedido de Portacelular del 28/09/2026 por ARS 6.500.

La memoria se guarda en memoria.sqlite.
Cambiar el thread_id inicia un historial separado.

## Prueba pendiente de recuperación ante información incorrecta

En una sesión nueva, consultar:

"Buscá a Luciano Pérez. Si no aparece, probá solo con Luciano
y consultá sus pedidos."

Verificar que el modelo interprete el resultado sin coincidencias,
realice una nueva búsqueda y continúe con el cliente encontrado.

También puede consultarse un identificador inexistente para comprobar
si solicita una aclaración.

## Trazas

main.py crea la carpeta trazas y guarda un JSON por consulta.

Cada archivo incluye:

- Identificador de sesión.
- Fecha y consulta.
- Eventos de los nodos.
- Llamadas a herramientas y argumentos.
- Resultados de herramientas.
- Respuesta del modelo.
- Cantidad de llamadas y estado de la ejecución.

La traza registra eventos observables de ejecución.

## Estado de validación

Las herramientas fueron verificadas localmente sin utilizar OpenAI.

La ejecución completa con el LLM, la recuperación de memoria a través
del agente y el comportamiento ante errores quedaron pendientes
por falta de saldo en la API.

No se incluye una traza real de ejecución del LLM ni se presenta
la prueba manual de herramientas como evidencia de autonomía.

El proyecto incluye la configuración para que el evaluador pueda
ejecutarlo con su propia API key y generar las trazas reales.

## Alcance

Los datos de clientes y pedidos son ficticios y están definidos
en tools.py. SQLite almacena el estado de las conversaciones.

El historial se acumula dentro de cada thread_id. Este ejercicio
no implementa resumen ni recorte del historial; para pruebas
independientes se recomienda utilizar sesiones nuevas.