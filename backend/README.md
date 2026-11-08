# Backend de Autos Colombia

## CRUD de operadores

Disponible únicamente en la API bajo `/operadores`, con POST, GET paginado,
GET por id, PATCH parcial y DELETE. Reutiliza el modelo y la tabla `operador`
de `0001`, cuya existencia y restricciones se comprobaron antes de implementar.
No se modificaron tablas, migraciones ni Angular.

Consulta el [README principal](../README.md#crud-de-operadores-solo-backend)
para contratos, reglas, ejemplo de `/docs`, comandos PowerShell del entorno
virtual existente, resultados comprobados y verificaciones pendientes.

## Gestión de celdas

Se revisó PostgreSQL antes de implementar el CRUD: la tabla `celda` y la revisión
`0001` ya existían y no había migraciones pendientes. Se verificaron `id BIGINT
GENERATED ALWAYS AS IDENTITY`, clave primaria, `codigo` único, campos `NOT NULL`
y los CHECK de código normalizado y textos no vacíos. No se modificaron migraciones
aplicadas ni se recrearon tablas.

El CRUD sigue la organización de vehículos: `app/schemas/celda.py`,
`app/services/celda.py` y `app/routers/celdas.py`.

| Operación | Resultado |
| --- | --- |
| POST `/celdas` con `codigo` y `tipo` | 201 con la celda creada |
| GET `/celdas?offset=0&limit=20` | 200 con items, total, offset y limit |
| GET `/celdas/{id}` | 200 o 404 |
| PATCH `/celdas/{id}` | 200; solo campos enviados, sin id ni valores nulos |
| DELETE `/celdas/{id}` | 204 sin cuerpo |

`codigo` se recorta y convierte a mayúsculas. `tipo` es texto libre obligatorio,
sin categorías ni compatibilidades con vehículos. Blancos y datos inválidos
devuelven 422; código duplicado y conflictos de relaciones devuelven 409, con
rollback. No se borran registros relacionados. Usa `/docs`, sección **Celdas**,
con un ejemplo como `{"codigo":"A-01","tipo":"Espacio general"}`.

Las pruebas `tests/test_celdas_postgres.py` se habilitan con `RUN_POSTGRES_TESTS=1`,
igual que las de vehículos. Verifican restricciones y CRUD reales dentro de
transacciones revertidas; las secuencias pueden avanzar. No ejecutan DDL.

Desde `backend`, en PowerShell:

```powershell
.\.venv\Scripts\python.exe -m alembic -c .\alembic.ini current
.\.venv\Scripts\python.exe -m alembic -c .\alembic.ini heads
$env:RUN_POSTGRES_TESTS = '1'
try {
    .\.venv\Scripts\python.exe -m pytest -q
} finally {
    Remove-Item Env:RUN_POSTGRES_TESTS -ErrorAction SilentlyContinue
}
```

Entorno verificado: Python 3.13.16 en Windows.
Ejecuta los siguientes comandos desde la carpeta `backend` en PowerShell.

## Preparar el entorno

```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

`requirements.txt` fija todas las dependencias de ejecución y pruebas, incluidas
las transitivas. No es necesario activar el entorno virtual.

## Ejecutar la API

```powershell
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

`GET http://127.0.0.1:8000/health` devuelve `{"status": "ok"}` con estado HTTP 200.
La documentación interactiva está en `http://127.0.0.1:8000/docs`.

## Ejecutar las pruebas

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

## PostgreSQL local

1. Instala e inicia PostgreSQL localmente y prepara una base de datos y un usuario.
   Este proyecto no instala PostgreSQL ni crea bases de datos. Las tablas se crean
   únicamente cuando ejecutas explícitamente las migraciones descritas más abajo.
2. Si no existe `.env`, copia la plantilla sin sobrescribir un archivo existente:

   ```powershell
   if (-not (Test-Path -LiteralPath .env)) {
       Copy-Item -LiteralPath .env.example -Destination .env
   }
   ```

3. Edita `.env` localmente. Completa `DB_NAME`, `DB_USER` y `DB_PASSWORD`.
   Confirma `DB_HOST` y `DB_PORT` (ejemplos: `127.0.0.1` y `5432`).
   `DB_CONNECT_TIMEOUT` es un entero entre 1 y 60 segundos.
   Los valores `CAMBIAR_...` son marcadores: no permiten intentar una conexión.
   Si la contraseña contiene espacios o `#`, usa comillas simples en `.env`.
   No se interpolan expresiones `${...}` dentro de los valores.
4. Comprueba la conexión:

   ```powershell
   .\.venv\Scripts\python.exe .\check_db.py
   $LASTEXITCODE
   ```

El comando solo ejecuta `SELECT 1`, sin crear ni modificar tablas. Devuelve 0
únicamente tras verificar una respuesta real; 2 si faltan variables o son
inválidas; 1 si la conexión o la consulta fallan. No imprime credenciales, URL
de conexión ni detalles del controlador que pudieran contener datos privados.

Desde cualquier carpeta puedes usar rutas absolutas:

```powershell
& 'C:\Users\user\Documents\IU DIGITAL\Clase Ingeniería de Software\AutosColombia\backend\.venv\Scripts\python.exe' 'C:\Users\user\Documents\IU DIGITAL\Clase Ingeniería de Software\AutosColombia\backend\check_db.py'
```

`app/config.py` localiza `.env` respecto a su propio archivo, independientemente
de la carpeta de ejecución. Las variables de entorno tienen prioridad sobre
`.env`. Reinicia los procesos después de cambiar la configuración.

`app/database.py` proporciona `get_engine()` y la dependencia `get_session()`
para futuros endpoints. No conecta al importar ni ejecuta `create_all` o
migraciones. `/health` sigue comprobando la API, no PostgreSQL, y funciona sin
configurar la base de datos. Las pruebas usan datos ficticios y conexiones
simuladas; la verificación real se hace con `check_db.py`.

`.env` está excluido de Git. `.env.example` se conserva como plantilla pública;
nunca copies contraseñas reales a ella.

## Modelos y migración inicial

Los modelos están en `app/models.py`, separados de la conexión (`app/database.py`)
y de la configuración (`app/config.py`). La revisión `0001`, en
`migrations/versions/0001_modelos_iniciales.py`, crea estas tablas:

| Clase | Tabla | Atributos |
| --- | --- | --- |
| Vehiculo | vehiculo | id, placa, color, modelo, marca, tipo |
| Celda | celda | id, codigo, tipo |
| Operador | operador | id, nombre, telefono |

- `id` usa `BIGINT GENERATED ALWAYS AS IDENTITY` y clave primaria. Se omite al insertar.
- Todos los campos son `NOT NULL`. Los textos tienen comprobaciones contra valores
  vacíos o formados únicamente por espacios, tabulaciones o saltos de línea.
- El ORM elimina espacios exteriores y convierte `placa` y `codigo` a mayúsculas,
  tanto al construir objetos como al asignar estos atributos. PostgreSQL exige
  esa forma normalizada mediante `CHECK` y garantiza su unicidad con `UNIQUE`.
  SQL directo y operaciones masivas que omiten validadores deben normalizar antes;
  la base rechaza valores sin normalizar en lugar de transformarlos silenciosamente.
- `modelo` es un año entero, no un nombre comercial: el modelo ORM y la base
  admiten 1–9999, pero la API solo acepta 1900–2200; no se impone
  un límite vinculado al año actual. `telefono` es texto y conserva prefijos y ceros.
- El tipo de vehículo admite únicamente `MOTO`, `AUTOMOVIL` y `CAMIONETA`.
  El tipo de celda es texto no vacío, sin catálogo ni reglas de compatibilidad todavía.
- No hay relaciones ni Estancia ni creación automática de tablas al iniciar
  FastAPI. `/health` conserva su funcionamiento independiente.

Al preparar esta revisión no se encontraron tablas de usuario ni revisiones
anteriores. Al implementar el CRUD se verificó que la revisión **0001 ya estaba
aplicada en autos_colombia**; no se modificó ni se volvió a aplicar.
Alembic reutiliza `backend/.env` y no almacena una URL con credenciales en su INI.

### Instalar y revisar sin modificar PostgreSQL

```powershell
Set-Location -LiteralPath 'C:\Users\user\Documents\IU DIGITAL\Clase Ingeniería de Software\AutosColombia\backend'
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m pip check
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe .\check_db.py
.\.venv\Scripts\python.exe -m alembic -c .\alembic.ini history
.\.venv\Scripts\python.exe -m alembic -c .\alembic.ini heads
Get-Content -LiteralPath .\migrations\versions\0001_modelos_iniciales.py
.\.venv\Scripts\python.exe -m alembic -c .\alembic.ini upgrade head --sql
```

El último comando **solo imprime SQL**: no conecta a PostgreSQL ni aplica cambios.
Incluye las tres tablas y `alembic_version`, que Alembic utiliza para registrar
las revisiones aplicadas. Las pruebas comparan modelos y migración y compilan
DDL PostgreSQL, pero no crean tablas ni prueban inserciones reales en la base local.

### Aplicar después de revisar (estos comandos sí modifican el esquema)

Ejecuta este bloque únicamente cuando decidas aplicar la migración:

```powershell
Set-Location -LiteralPath 'C:\Users\user\Documents\IU DIGITAL\Clase Ingeniería de Software\AutosColombia\backend'
.\.venv\Scripts\python.exe .\check_db.py
if ($LASTEXITCODE -ne 0) { throw 'La conexión no está disponible; no aplicar migraciones.' }
.\.venv\Scripts\python.exe -m alembic -c .\alembic.ini upgrade head
if ($LASTEXITCODE -ne 0) { throw 'La migración no se completó; revisar el esquema antes de continuar.' }
.\.venv\Scripts\python.exe -m alembic -c .\alembic.ini current
```

El resultado esperado de `current` después de aplicar es `0001 (head)`.
No uses `stamp` para dar por aplicada una migración que no se ejecutó. Si ya hay
tablas con los mismos nombres, detente y revisa su estructura: esta migración no
las borra ni las recrea y fallará ante un conflicto. Su `downgrade` elimina las
tres tablas y sus datos; no lo ejecutes como parte de la instalación.

Los paths de Alembic se resuelven respecto a `alembic.ini`. Desde otra carpeta,
utiliza rutas absolutas para el intérprete y `-c`, igual que con `check_db.py`.

## CRUD de vehículos

La implementación se divide en `app/schemas/vehiculo.py` (validación y respuestas),
`app/routers/vehiculos.py` (APIRouter) y `app/services/vehiculo.py` (operaciones y
transacciones). Reutiliza el modelo `Vehiculo`, `get_session()` y las tablas existentes.

| Método y ruta | Resultado |
| --- | --- |
| `POST /vehiculos` | 201 y vehículo registrado, incluido su id |
| `GET /vehiculos?offset=0&limit=20` | 200 con `items`, `total`, `offset` y `limit` |
| `GET /vehiculos/{id}` | 200 y vehículo, o 404 |
| `PATCH /vehiculos/{id}` | 200 y vehículo actualizado, o 404 |
| `DELETE /vehiculos/{id}` | 204 sin cuerpo, o 404 |

La lista se ordena por id ascendente; `offset` empieza en 0 y `limit` admite de
1 a 100 (20 por defecto). `total` es el número total de vehículos, no solo el de
la página. Los ids deben ser enteros positivos dentro del rango de BIGINT.

Al crear se requieren placa, color, modelo, marca y tipo. El año debe ser un
entero JSON entre 1900 y 2200 (la restricción de base de datos y el modelo ORM
conservan el rango más amplio 1–9999; la API es la que acota); no se aceptan cadenas, booleanos ni decimales. Los
textos no pueden estar vacíos. La placa se recorta y se convierte a mayúsculas.
Los tipos admitidos son `MOTO`, `AUTOMOVIL` y `CAMIONETA`.

PATCH aplica solo los campos enviados, rechaza valores nulos y campos desconocidos,
incluido `id`. Un objeto vacío conserva el vehículo. Los errores de validación
devuelven 422, una placa duplicada devuelve 409 y un vehículo inexistente, 404.
La unicidad se comprueba en PostgreSQL, también ante peticiones concurrentes;
las transacciones fallidas se revierten. Una clave foránea que impida borrar
devuelve 409 sin eliminar registros relacionados. No hay borrado en cascada en
el servicio. Los fallos generales de base de datos devuelven 503 sin detalles privados.

### Probar desde /docs

Inicia o reinicia el servidor para cargar las nuevas rutas:

```powershell
Set-Location -LiteralPath 'C:\Users\user\Documents\IU DIGITAL\Clase Ingeniería de Software\AutosColombia\backend'
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Abre <http://127.0.0.1:8000/docs>, despliega **Vehículos** y usa **Try it out**.
Crea un vehículo con POST, copia el id devuelto y úsalo para GET, PATCH y DELETE.
Repite el POST con la misma placa para comprobar 409; prueba PATCH con
`{"color": null}` para comprobar 422. Después de borrar el registro, GET devuelve
404. Estas acciones desde `/docs` sí guardan cambios en tu base.

### Probar desde otra terminal de PowerShell

Este ejemplo crea una placa de prueba aleatoria y elimina solo el vehículo que
acaba de crear. Mantén el backend en ejecución en la primera terminal.

```powershell
$apiUrl = 'http://127.0.0.1:8000'
$testPlate = 'TEST-' + [guid]::NewGuid().ToString('N').Substring(0, 12).ToUpperInvariant()
$payload = @{
    placa = $testPlate
    color = 'Azul'
    modelo = 2025
    marca = 'Prueba'
    tipo = 'AUTOMOVIL'
} | ConvertTo-Json
$vehicle = Invoke-RestMethod -Method Post -Uri "$apiUrl/vehiculos" -ContentType 'application/json; charset=utf-8' -Body ([Text.Encoding]::UTF8.GetBytes($payload))
try {
    $vehicle
    Invoke-RestMethod -Uri "$apiUrl/vehiculos?offset=0&limit=20"
    Invoke-RestMethod -Uri "$apiUrl/vehiculos/$($vehicle.id)"
    Invoke-RestMethod -Method Patch -Uri "$apiUrl/vehiculos/$($vehicle.id)" -ContentType 'application/json' -Body '{"color":"Rojo"}'
} finally {
    $response = Invoke-WebRequest -Method Delete -Uri "$apiUrl/vehiculos/$($vehicle.id)" -UseBasicParsing
    $response.StatusCode # 204
}
```

### Pruebas automatizadas

Las pruebas habituales no requieren PostgreSQL; la integración se omite por defecto:

```powershell
Set-Location -LiteralPath 'C:\Users\user\Documents\IU DIGITAL\Clase Ingeniería de Software\AutosColombia\backend'
.\.venv\Scripts\python.exe -m pytest -q
```

Para comprobar el CRUD real, usando la base `autos_colombia` de `.env` y la
migración `0001` ya aplicada:

```powershell
$env:RUN_POSTGRES_TESTS = '1'
try {
    .\.venv\Scripts\python.exe -m pytest -q
    if ($LASTEXITCODE -ne 0) { throw 'Fallaron las pruebas.' }
} finally {
    Remove-Item Env:RUN_POSTGRES_TESTS -ErrorAction SilentlyContinue
}
```

No necesita un servidor HTTP iniciado: TestClient llama a la aplicación y esta
usa PostgreSQL real. Los registros se ejecutan dentro de una transacción exterior
con savepoints que se revierte al terminar, incluso si falla una prueba. No se
crean tablas ni se modifica el esquema; las secuencias de ids pueden avanzar
porque PostgreSQL no revierte sus valores. No se borran registros existentes.
La prueba de conflicto por relación es simulada, ya que el esquema actual no
tiene claves foráneas hacia vehículos; no se añaden relaciones para probarla.

## Clientes, mensualidades, disponibilidad, reasignación de celda y login (RF-10 a RF-16)

Backend únicamente; el frontend de estas pantallas queda pendiente. Resumen de
lo añadido (ver el documento de requerimientos para el detalle completo):

- **`POST/GET/PATCH/DELETE /clientes`**: catálogo de clientes (RF-12).
- **`vehiculo.cliente_id`** (obligatorio): todo vehículo pertenece a un
  cliente. `PATCH /vehiculos/{id}` con `cliente_id` reasigna el vehículo a
  otro cliente (RF-13).
- **`GET /celdas/disponibles`**: celdas sin una estancia abierta en este
  momento, paginado igual que `GET /celdas` (RF-10).
- **`PATCH /estancias/celda`** (`{"placa", "celda_id"}`, requiere sesión
  iniciada): mueve la estancia abierta de un vehículo a otra celda, para
  corregir una celda equivocada (RF-11).
- **`POST /pagos`** (`{"vehiculo_id", "periodo_inicio"?}`, requiere sesión
  iniciada): registra el pago de la mensualidad; el monto lo calcula el
  servidor según el tipo de vehículo ($100.000 moto, $250.000
  automóvil/camioneta) y **nunca** lo acepta del cliente. El periodo cubre
  un mes calendario completo desde `periodo_inicio` (hoy, si se omite).
- **`GET /pagos?vehiculo_id=`** y **`GET /vehiculos/{id}/mensualidad`**:
  historial de pagos y si la mensualidad está vigente hoy.
- **`POST /estancias/entrada`** ahora rechaza con **402** si el vehículo no
  tiene mensualidad vigente, sin excepción (RF-14).
- **`GET /reportes/resumen`**: celdas totales/disponibles y clientes
  registrados, en cualquier momento (RF-15).
- **Inicio de sesión de operador (RF-16)**: `operador` gana `usuario`
  (único), `password` (se guarda como `password_hash` con PBKDF2-SHA256,
  nunca en claro) y `turno` (`DIA` o `NOCHE`, sin límite de cuántos
  operadores hay por turno). `POST /auth/login` devuelve un token (JWT,
  firmado con `JWT_SECRET` de `backend/.env`) que debe enviarse como
  `Authorization: Bearer <token>` en `/estancias/entrada`, `/estancias/salida`,
  `/estancias/celda` y `POST /pagos`: el operador que actúa se toma del
  token, **ya no viaja en el cuerpo de la solicitud** (antes `operador_id` era
  parte de `EntradaCrear`/`SalidaCrear`; eliminarlo fue un cambio incompatible
  a propósito, para que el token sea la única fuente de verdad sobre
  quién actúa).

### Migración `0003` y datos iniciales

`migrations/versions/0003_cliente_pago_login.py` crea `cliente` y `pago`, y
agrega las columnas nuevas de `vehiculo` y `operador`, todas `NOT NULL` y sin
valor por defecto. Si la base ya tiene vehículos u operadores, esta
migración **falla** hasta que cada fila reciba un valor válido (un
cliente de respaldo y `cliente_id` en cada vehículo; `usuario`,
`password_hash` y `turno` en cada operador) antes de aplicarla; no incluye un
backfill automático porque no hay un valor "por defecto" razonable para
datos reales. Revisar primero sin aplicar, con el intérprete de `.venv`:

```powershell
.\.venv\Scripts\python.exe -m alembic -c alembic.ini upgrade 0002:0003 --sql
```

`seed_data.py` carga las 80 celdas iniciales de RF-10 (10 `MOTO-01`..`MOTO-10`
y 70 `CARRO-001`..`CARRO-070`) de forma idempotente; no crea operadores
(usuario y contraseña se registran desde `POST /operadores`, nunca con
valores de ejemplo en un script):

```powershell
.\.venv\Scripts\python.exe seed_data.py
```

### Migración `0004`: rango de año de `vehiculo.modelo`

`migrations/versions/0004_vehiculo_modelo_1900_2200.py` cambia el `CHECK` de
`vehiculo.modelo` de `1-9999` a `1900-2200`, para que el modelo físico
coincida con el rango que ya exigía el esquema Pydantic de la API
(`app/schemas/vehiculo.py`) y con el documento del proyecto. Si ya existen
vehículos con `modelo` fuera de 1900-2200, esta migración **falla** hasta
corregir esas filas manualmente. Revisar primero sin aplicar:

```powershell
.\.venv\Scripts\python.exe -m alembic -c alembic.ini upgrade 0003:0004 --sql
```

### Variable nueva en `backend/.env`

```
JWT_SECRET=<genera un valor propio y secreto>
JWT_EXPIRATION_MINUTES=480
```

Generar un valor, por ejemplo:

```powershell
.\.venv\Scripts\python.exe -c "import secrets; print(secrets.token_urlsafe(48))"
```

### Pendiente

- Frontend: pantallas de clientes, mensualidades/pagos, inicio de sesión de
  operador (con el token guardado para las llamadas protegidas) y el aviso de
  celdas disponibles/reasignación en Control de acceso.
- Verificar `tests/test_estancias_postgres.py`,
  `tests/test_operadores_postgres.py` y `tests/test_vehiculos_postgres.py`
  actualizados con `RUN_POSTGRES_TESTS=1` contra la base real (se escribieron
  y revisaron con cuidado, pero no hay PostgreSQL disponible en el entorno
  donde se implementaron para ejecutarlos).
- Decidir si se requiere imponer el límite de 10 celdas MOTO / 70 no-MOTO y
  de 2 operadores de día / 1 de noche (hoy son solo datos iniciales, sin
  límite impuesto por el sistema, por decisión explícita).
