# Historias de usuario — Autos Colombia

Historias asociadas a los requerimientos de [01-requerimientos.md](01-requerimientos.md).
**Todas están implementadas.** Cada criterio de
aceptación se puede comprobar en la pantalla indicada o en `/docs` (Swagger) y
tiene una prueba automática asociada ([05-plan-de-pruebas.md](05-plan-de-pruebas.md)).

Actores: **Operador** (atiende el parqueadero, con sesión iniciada) y
**Administrador de catálogos** (mantiene operadores, clientes, vehículos y
celdas). Ambos inician sesión como operador.

Mockups: ver [03-mockups-figma.md](03-mockups-figma.md).

| Historia | HU-01 | HU-02 | HU-03 | HU-04 | HU-05 | HU-06 | HU-07 | HU-08 | HU-09 | HU-10 | HU-11 | HU-12 | HU-13 | HU-14 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Requerimiento | RF-01 | RF-02 | RF-03 | RF-04 | RF-05 | RF-06 | RF-07 | RF-08, RF-09 | RF-10 | RF-11 | RF-12, RF-13 | RF-14 | RF-15 | RF-16 |

## Iteración 1 — Entrada y salida de vehículos

### HU-01 · Registrar vehículo
**Como** administrador **quiero** registrar un vehículo con su cliente **para** poder controlar su entrada y salida.
- **Dado** que abro *Vehículos* y pulso *Nuevo vehículo*, **cuando** completo placa, color, marca, modelo, tipo y cliente y guardo, **entonces** el vehículo aparece en el listado con la placa en mayúsculas.
- **Cuando** repito una placa existente, **entonces** veo el mensaje «Ya existe un vehículo con esa placa» (409).
- **Cuando** el modelo está fuera de 1900–2200 o hay campos vacíos, **entonces** no se guarda y se señala el campo.
- **Cuando** no elijo cliente, **entonces** no se puede guardar (todo vehículo tiene dueño).

### HU-02 · Consultar, editar y eliminar vehículos
**Como** administrador **quiero** mantener la lista de vehículos **para** corregir datos o retirar los que ya no se usan.
- El listado es paginado (10 por página) con *Anterior* y *Siguiente*.
- **Cuando** edito un vehículo y guardo, **entonces** se actualiza y se muestra confirmación.
- **Cuando** elimino un vehículo sin registros relacionados, **entonces** desaparece tras confirmar.
- **Cuando** el vehículo tiene estancias o pagos, **entonces** no se elimina y se explica el motivo (409).

### HU-03 · Registrar entrada
**Como** operador **quiero** registrar la entrada de un vehículo a una celda **para** saber qué celda ocupa.
- **Dado** que inicié sesión, **cuando** escribo la placa (con espacios o minúsculas) y elijo una celda libre, **entonces** se registra la entrada con la fecha en hora de Bogotá y mi usuario como operador.
- **Cuando** el vehículo no tiene mensualidad vigente, **entonces** se rechaza con 402 «El vehículo no tiene mensualidad vigente».
- **Cuando** el vehículo ya está dentro, **entonces** se rechaza con 409 «El vehículo ya está dentro».
- **Cuando** la celda está ocupada, **entonces** se rechaza con 409 «La celda está ocupada».
- **Cuando** no hay sesión, **entonces** la pantalla redirige a *Iniciar sesión* y la API responde 401.

### HU-04 · Registrar salida
**Como** operador **quiero** registrar la salida de un vehículo **para** liberar su celda.
- **Cuando** consulto un vehículo *dentro* y confirmo la salida, **entonces** la estancia se cierra con fecha y operador, y la celda vuelve a estar disponible.
- **Cuando** el vehículo no tiene estancia abierta, **entonces** se rechaza con 409.
- **Cuando** cambio la placa consultada, **entonces** se descarta el resultado anterior y no se puede cerrar la estancia de otra placa.

### HU-05 · Consultar estado de un vehículo
**Como** operador **quiero** consultar una placa **para** saber si está dentro y en qué celda.
- **Dentro**: muestra celda y fecha de entrada. **Fuera**: vehículo registrado sin estancia abierta. **No registrado**: la placa no existe.

## Iteración 2 — Gestión de usuarios y de celdas

### HU-06 · Gestionar celdas
**Como** administrador **quiero** crear, editar y eliminar celdas **para** reflejar la capacidad real del parqueadero.
- **Cuando** creo una celda con código y tipo, **entonces** el código se guarda en mayúsculas y recortado.
- **Cuando** repito un código, **entonces** veo «Ya existe una celda con ese código» (409).
- **Cuando** elimino una celda con estancias registradas, **entonces** no se elimina (409).
- Código y tipo vacíos se rechazan (422).

### HU-07 · Gestionar operadores
**Como** administrador **quiero** registrar operadores con usuario, contraseña y turno **para** que puedan iniciar sesión.
- **Cuando** creo un operador con usuario único, contraseña y turno DIA o NOCHE, **entonces** queda registrado y la respuesta **no** incluye la contraseña.
- **Cuando** edito sin escribir contraseña, **entonces** la contraseña actual no cambia.
- **Cuando** repito el usuario, **entonces** veo «Ya existe un operador con ese usuario» (409).
- **Cuando** elimino un operador con estancias o pagos registrados, **entonces** no se elimina (409).

### HU-08 · Validación e integridad de datos
**Como** equipo **quiero** que las reglas se cumplan siempre **para** no tener datos inconsistentes.
- Textos con solo espacios, año fuera de rango, tipos desconocidos y campos extra devuelven 422.
- La base de datos aplica las mismas reglas (CHECK, únicos y claves foráneas `RESTRICT`).

### HU-09 · Cargar celdas iniciales y consultar disponibles *(RF-10)*
**Como** administrador **quiero** cargar las celdas iniciales y ver cuáles están libres **para** asignar una celda sin adivinar.
- **Dado** que ejecuto `seed_data.py`, **entonces** existen 80 celdas (10 MOTO-01…MOTO-10 y 70 CARRO-001…CARRO-070); si lo ejecuto otra vez no se duplican.
- **Cuando** consulto `GET /celdas/disponibles`, **entonces** solo aparecen las celdas sin estancia abierta, paginadas igual que el listado general.
- **Cuando** un vehículo entra a una celda, **entonces** esa celda deja de aparecer como disponible; **cuando** sale, vuelve a aparecer.

### HU-10 · Corregir la celda de una estancia *(RF-11)*
**Como** operador **quiero** cambiar la celda de un vehículo que ya entró **para** corregir un error de digitación.
- **Cuando** indico placa y nueva celda libre en *Control de acceso*, **entonces** la estancia abierta pasa a esa celda y la anterior queda libre.
- **Cuando** la nueva celda está ocupada, **entonces** veo «La celda está ocupada» (409) y nada cambia.
- **Cuando** el vehículo no tiene estancia abierta, **entonces** veo «El vehículo no tiene una estancia abierta» (409).
- **Cuando** no hay sesión, **entonces** se exige iniciar sesión (401).

### HU-11 · Gestionar clientes y reasignar vehículos *(RF-12, RF-13)*
**Como** administrador **quiero** registrar clientes y asignarles vehículos **para** saber a quién pertenece cada vehículo.
- **Cuando** creo un cliente con nombre, documento y teléfono, **entonces** aparece en el listado.
- **Cuando** repito un documento, **entonces** veo «Ya existe un cliente con ese documento» (409).
- **Cuando** edito un vehículo y elijo otro cliente, **entonces** el vehículo queda asociado al nuevo cliente.
- **Cuando** elimino un cliente con vehículos, **entonces** no se elimina (409).

### HU-12 · Registrar mensualidad y validarla en la entrada *(RF-14)*
**Como** operador **quiero** registrar la mensualidad de un vehículo **para** que pueda entrar.
- **Cuando** registro el pago de un vehículo en *Mensualidades*, **entonces** el sistema calcula el monto según el tipo (MOTO $100.000; AUTOMOVIL o CAMIONETA $250.000) y el periodo de un mes calendario desde hoy (o desde la fecha indicada).
- **Cuando** intento enviar un monto desde el cliente, **entonces** la API lo rechaza (422): el monto no se acepta del cliente.
- **Cuando** consulto la vigencia, **entonces** veo si hoy está dentro del periodo pagado y las fechas del periodo.
- **Cuando** registro la entrada de un vehículo sin mensualidad vigente, **entonces** se rechaza con 402.
- **Cuando** no hay sesión, **entonces** registrar un pago exige iniciar sesión (401).

### HU-13 · Consultar el resumen del parqueadero *(RF-15)*
**Como** administrador **quiero** ver cuántas celdas hay libres y cuántos clientes están registrados **para** tomar decisiones rápidas.
- **Cuando** abro *Reportes*, **entonces** veo celdas disponibles, celdas totales y clientes registrados.
- **Cuando** un vehículo entra o sale y pulso *Actualizar*, **entonces** las celdas disponibles cambian en consecuencia.

### HU-14 · Iniciar sesión *(RF-16)*
**Como** operador **quiero** iniciar sesión **para** que mis acciones queden registradas a mi nombre.
- **Cuando** ingreso usuario y contraseña correctos, **entonces** accedo y veo mi nombre con la opción *Cerrar sesión*.
- **Cuando** ingreso datos incorrectos, **entonces** veo «Usuario o contraseña incorrectos» sin revelar cuál falló (401).
- **Cuando** intento abrir *Control de acceso* sin sesión, **entonces** la pantalla redirige a *Iniciar sesión*.
- **Cuando** cierro sesión, **entonces** se elimina el token y se exige iniciar sesión de nuevo.

> **La retroalimentación de la Actividad 1 pedía completar los criterios de
> aceptación de HU-09 a HU-12:** quedan completos arriba (celdas iniciales y
> disponibles, corrección de celda, clientes y mensualidad). Si tu documento de
> la Actividad 1 numera las historias distinto, conserva esa numeración y
> reutiliza el contenido de cada criterio.
