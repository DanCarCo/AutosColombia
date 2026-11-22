# Diagramas — Autos Colombia

Versión en **Mermaid** de los diagramas del proyecto. GitHub y la vista previa
de Markdown de VS Code los dibujan directamente, así que sirven como evidencia
verificable en el repositorio y como guía para dibujarlos en StarUML.

El modelo de StarUML está en
[`../entrega-ingenieria-software/staruml/AutosColombia.mdj`](../entrega-ingenieria-software/staruml/AutosColombia.mdj);
cómo abrirlo y exportar las imágenes del PDF: [06-staruml.md](06-staruml.md).

> **StarUML 7 puede importar estos diagramas de secuencia directamente:** menú
> **Tools ▸ Generate Diagram by Mermaid…**, pega el bloque (sin las líneas ```) y se crea el
> diagrama. Los actores se escriben como `participant` porque esa importación no admite `actor`.

| # | Diagrama | Entregable | Sección |
| --- | --- | --- | --- |
| 1 | Casos de uso — gestión de usuarios y celdas (iteración 2) | B | [1](#1-casos-de-uso--gestión-de-usuarios-y-celdas-iteración-2) |
| 2 | Casos de uso — operación y pagos (iteración 1 y mensualidades) | B | [2](#2-casos-de-uso--operación-y-pagos) |
| 3 | Diagrama de clases (incluye Cliente y Pago) | Retroalimentación | [3](#3-diagrama-de-clases) |
| 4–10 | Diagramas de secuencia (iteraciones 1 y 2) | E | [4](#diagramas-de-secuencia) |
| 11 | Diagrama de componentes (iteraciones 1 y 2) | F | [11](#11-diagrama-de-componentes) |

## 1. Casos de uso — gestión de usuarios y celdas (iteración 2)

```mermaid
flowchart LR
    adm(["Administrador de catálogos"])
    op(["Operador de parqueadero"])
    subgraph Sistema["Sistema Autos Colombia — Iteración 2"]
        cu01(["CU-01 Iniciar sesión"])
        cu09(["CU-09 Gestionar operadores"])
        cu10(["CU-10 Gestionar clientes"])
        cu06(["CU-06 Gestionar vehículos"])
        cu07(["CU-07 Gestionar celdas"])
        cu08(["CU-08 Consultar celdas disponibles"])
        cu14(["CU-14 Consultar resumen"])
    end
    adm --- cu01
    adm --- cu09
    adm --- cu10
    adm --- cu06
    adm --- cu07
    adm --- cu08
    adm --- cu14
    op --- cu01
    op --- cu08
    op --- cu14
```

## 2. Casos de uso — operación y pagos

```mermaid
flowchart LR
    op(["Operador de parqueadero"])
    subgraph Sistema["Sistema Autos Colombia — Operación y pagos"]
        cu01(["CU-01 Iniciar sesión"])
        cu02(["CU-02 Registrar entrada"])
        cu03(["CU-03 Registrar salida"])
        cu04(["CU-04 Consultar estado de vehículo"])
        cu05(["CU-05 Corregir celda de la estancia"])
        cu11(["CU-11 Registrar mensualidad"])
        cu12(["CU-12 Consultar vigencia"])
        cu13(["CU-13 Validar mensualidad vigente"])
    end
    op --- cu02
    op --- cu03
    op --- cu04
    op --- cu05
    op --- cu11
    op --- cu12
    cu02 -. "«include»" .-> cu13
    cu02 -. "«include»" .-> cu01
    cu03 -. "«include»" .-> cu01
    cu05 -. "«include»" .-> cu01
    cu11 -. "«include»" .-> cu01
```

CU-15 *Verificar estado de la API* (`GET /health`) lo usa la pantalla de inicio.

## 3. Diagrama de clases

Incluye **Cliente** y **Pago** con sus relaciones, tal como pidió la
retroalimentación de la Actividad 1. Coincide con `backend/app/models.py`.

```mermaid
classDiagram
    direction LR
    class Cliente {
        +Long id
        +String nombre
        +String documento
        +String telefono
    }
    class Vehiculo {
        +Long id
        +String placa
        +String color
        +Integer modelo
        +String marca
        +TipoVehiculo tipo
        +Long cliente_id
    }
    class Celda {
        +Long id
        +String codigo
        +String tipo
    }
    class Operador {
        +Long id
        +String nombre
        +String telefono
        +String usuario
        +String password_hash
        +Turno turno
        +Rol rol
    }
    class Estancia {
        +Long id
        +DateTime entrada
        +DateTime salida
        +esta_abierta() bool
        +cerrar(fecha, operador)
    }
    class Pago {
        +Long id
        +Decimal monto
        +Date periodo_inicio
        +Date periodo_fin
        +DateTime fecha_pago
    }
    class TipoVehiculo {
        <<enumeration>>
        MOTO
        AUTOMOVIL
        CAMIONETA
    }
    class Turno {
        <<enumeration>>
        DIA
        NOCHE
    }
    class Rol {
        <<enumeration>>
        ADMINISTRADOR
        OPERADOR
    }
    Cliente "1" --> "0..*" Vehiculo : posee
    Vehiculo "1" --> "0..*" Estancia : tiene
    Celda "1" --> "0..*" Estancia : aloja
    Operador "1" --> "0..*" Estancia : registra entrada
    Operador "0..1" --> "0..*" Estancia : registra salida
    Vehiculo "1" --> "0..*" Pago : cubre
    Operador "1" --> "0..*" Pago : registra
    Vehiculo ..> TipoVehiculo
    Operador ..> Turno
    Operador ..> Rol
```

Reglas de la base de datos que el diagrama resume: una sola estancia abierta
por vehículo y por celda (índices únicos parciales); todas las claves foráneas
son `RESTRICT`; `modelo` se limita a 1900–2200 con la migración `0004`.

## Diagramas de secuencia

Participantes comunes: **Operador** (persona), **UI** (componente Angular),
**API** (router FastAPI), **Servicio** (capa `services`) y **BD** (PostgreSQL).

### 4. Iniciar sesión (RF-16)

```mermaid
sequenceDiagram
    autonumber
    participant Operador
    participant UI as Login (Angular)
    participant API as POST /auth/login
    participant Srv as auth.login
    participant BD as PostgreSQL
    Operador->>UI: Escribe usuario y contraseña
    UI->>API: POST /auth/login
    API->>Srv: login(usuario, password)
    Srv->>BD: SELECT operador WHERE usuario
    BD-->>Srv: operador con password_hash
    Srv->>Srv: verify_password (PBKDF2) y crear JWT
    alt Credenciales válidas
        Srv-->>API: token y operador
        API-->>UI: 200 access_token y operador
        UI->>UI: Guarda la sesión y habilita el interceptor
    else Credenciales inválidas
        Srv-->>API: AuthError 401
        API-->>UI: 401 Usuario o contraseña incorrectos
    end
```

### 5. Registrar entrada de vehículo (RF-03, RF-14)

```mermaid
sequenceDiagram
    autonumber
    participant Operador
    participant UI as ControlAcceso (Angular)
    participant API as POST /estancias/entrada
    participant Srv as ServicioEstancia
    participant Pag as pago.vigente_para_vehiculo
    participant BD as PostgreSQL
    Operador->>UI: Placa y celda
    UI->>API: POST con Authorization Bearer
    API->>API: operador_actual valida el token
    API->>Srv: entrada(datos, operador)
    Srv->>BD: Busca vehículo y celda
    Srv->>Pag: ¿Mensualidad vigente?
    Pag->>BD: SELECT pago cuyo periodo incluye hoy
    alt Sin mensualidad vigente
        Srv-->>UI: 402 El vehículo no tiene mensualidad vigente
    else Vehículo dentro o celda ocupada
        Srv-->>UI: 409 con el motivo
    else Todo correcto
        Srv->>BD: INSERT estancia con operador de entrada
        BD-->>Srv: estancia creada
        Srv-->>UI: 201 estancia
        UI-->>Operador: Confirma placa, celda y fecha en hora de Bogotá
    end
```

### 6. Registrar salida de vehículo (RF-04)

```mermaid
sequenceDiagram
    autonumber
    participant Operador
    participant UI as ControlAcceso (Angular)
    participant API as API FastAPI
    participant Srv as ServicioEstancia
    participant BD as PostgreSQL
    Operador->>UI: Consulta la placa
    UI->>API: GET /estancias/vehiculo/placa
    API->>Srv: consultar(placa)
    Srv->>BD: Vehículo, estancia abierta y celda
    BD-->>UI: Estado dentro con celda y fecha de entrada
    Operador->>UI: Confirma la salida
    UI->>API: POST /estancias/salida
    API->>Srv: salida(placa, operador del token)
    Srv->>BD: Bloquea y busca la estancia abierta
    alt Sin estancia abierta
        Srv-->>UI: 409 El vehículo no tiene una estancia abierta
    else Estancia abierta
        Srv->>BD: Cierra la estancia con fecha y operador de salida
        Srv-->>UI: 200 estancia cerrada
        UI->>API: GET estado de nuevo
        API-->>UI: Fuera, celda libre
    end
```

### 7. Gestionar operadores — crear (RF-07, iteración 2)

```mermaid
sequenceDiagram
    autonumber
    participant Administrador
    participant UI as Operadores (Angular)
    participant API as POST /operadores
    participant Srv as services.operador
    participant Sec as security.hash_password
    participant BD as PostgreSQL
    Administrador->>UI: Nombre, teléfono, usuario, contraseña y turno
    UI->>UI: Valida campos no vacíos
    UI->>API: POST /operadores
    API->>API: Valida el esquema Pydantic
    API->>Srv: create_operador(datos)
    Srv->>Sec: hash_password(password)
    Sec-->>Srv: pbkdf2_sha256 hash
    Srv->>BD: INSERT operador con password_hash
    alt Usuario repetido
        BD-->>Srv: Violación de unicidad
        Srv-->>UI: 409 Ya existe un operador con ese usuario
    else Correcto
        BD-->>Srv: operador creado
        Srv-->>UI: 201 operador sin contraseña
        UI-->>Administrador: Confirmación y listado actualizado
    end
```

#### 7b. Gestionar operadores — editar y eliminar (RF-07, RF-17)

```mermaid
sequenceDiagram
    autonumber
    participant Administrador
    participant UI as Operadores (Angular)
    participant API as PATCH/DELETE /operadores/{id}
    participant Srv as services.operador
    participant BD as PostgreSQL
    Administrador->>UI: Edita datos (o deja la contraseña vacía)
    UI->>API: PATCH /operadores/{id}
    API->>API: Exige rol ADMINISTRADOR (solo_administrador)
    alt Sin rol ADMINISTRADOR
        API-->>UI: 403 No tienes permisos para esta operación
    else Rol correcto
        API->>Srv: update_operador(id, datos)
        Srv->>BD: UPDATE operador (conserva password_hash si no llega contraseña)
        alt Usuario repetido
            BD-->>Srv: Violación de unicidad
            Srv-->>UI: 409 Ya existe un operador con ese usuario
        else Correcto
            BD-->>Srv: operador actualizado
            Srv-->>UI: 200 operador sin contraseña
        end
    end
    Administrador->>UI: Elimina un operador
    UI->>API: DELETE /operadores/{id}
    API->>API: Exige rol ADMINISTRADOR
    API->>Srv: delete_operador(id)
    alt Tiene estancias o pagos registrados
        BD-->>Srv: Violación de clave foránea (RESTRICT)
        Srv-->>UI: 409 No se puede eliminar: tiene registros relacionados
    else Sin registros relacionados
        Srv->>BD: DELETE operador
        Srv-->>UI: 204 eliminado
    end
```

### 8. Gestionar celdas — crear y consultar disponibles (RF-06, RF-10)

```mermaid
sequenceDiagram
    autonumber
    participant Administrador
    participant UI as Celdas (Angular)
    participant API as API FastAPI
    participant Srv as services.celda
    participant BD as PostgreSQL
    Administrador->>UI: Código y tipo
    UI->>API: POST /celdas
    API->>Srv: create_celda(datos)
    Srv->>Srv: Normaliza el código a mayúsculas
    Srv->>BD: INSERT celda
    alt Código repetido
        Srv-->>UI: 409 Ya existe una celda con ese código
    else Correcto
        Srv-->>UI: 201 celda
    end
    Administrador->>UI: Consulta las disponibles
    UI->>API: GET /celdas/disponibles
    API->>Srv: list_available(offset, limit)
    Srv->>BD: Celdas sin estancia abierta
    BD-->>UI: Página de celdas libres
```

#### 8b. Gestionar celdas — editar y eliminar (RF-06, RF-17)

```mermaid
sequenceDiagram
    autonumber
    participant Administrador
    participant UI as Celdas (Angular)
    participant API as PATCH/DELETE /celdas/{id}
    participant Srv as services.celda
    participant BD as PostgreSQL
    Administrador->>UI: Edita código o tipo
    UI->>API: PATCH /celdas/{id}
    API->>API: Exige rol ADMINISTRADOR (solo_administrador)
    alt Sin rol ADMINISTRADOR
        API-->>UI: 403 No tienes permisos para esta operación
    else Rol correcto
        API->>Srv: update_celda(id, datos)
        Srv->>Srv: Normaliza el código a mayúsculas
        Srv->>BD: UPDATE celda
        alt Código repetido
            BD-->>Srv: Violación de unicidad
            Srv-->>UI: 409 Ya existe una celda con ese código
        else Correcto
            BD-->>Srv: celda actualizada
            Srv-->>UI: 200 celda
        end
    end
    Administrador->>UI: Elimina una celda
    UI->>API: DELETE /celdas/{id}
    API->>API: Exige rol ADMINISTRADOR
    API->>Srv: delete_celda(id)
    alt Tiene estancias relacionadas (libre u ocupada)
        BD-->>Srv: Violación de clave foránea (RESTRICT)
        Srv-->>UI: 409 No se puede eliminar: la celda tiene estancias relacionadas
    else Sin estancias relacionadas
        Srv->>BD: DELETE celda
        Srv-->>UI: 204 eliminada
    end
```

### 9. Registrar mensualidad (RF-14)

```mermaid
sequenceDiagram
    autonumber
    participant Operador
    participant UI as Mensualidades (Angular)
    participant API as POST /pagos
    participant Srv as services.pago
    participant BD as PostgreSQL
    Operador->>UI: Elige el vehículo y, si quiere, la fecha de inicio
    UI->>API: POST /pagos solo con vehiculo_id y periodo_inicio
    API->>API: operador_actual valida el token
    API->>Srv: register_payment(datos, operador)
    Srv->>BD: Busca el vehículo
    alt Vehículo inexistente
        Srv-->>UI: 404 Vehículo no encontrado
    else Vehículo existe
        Srv->>Srv: Calcula monto por tipo y fin de periodo
        Srv->>BD: INSERT pago con operador y fecha
        BD-->>Srv: pago creado
        Srv-->>UI: 201 pago
        UI->>API: GET /vehiculos/id/mensualidad
        API-->>UI: vigente verdadero con el periodo
    end
```

### 10. Gestionar clientes — crear y asignar vehículo (RF-12, RF-13)

```mermaid
sequenceDiagram
    autonumber
    participant Administrador
    participant UI as Clientes y Vehículos (Angular)
    participant API as API FastAPI
    participant Srv as Servicios cliente y vehículo
    participant BD as PostgreSQL
    Administrador->>UI: Nombre, documento y teléfono
    UI->>API: POST /clientes
    API->>Srv: create_cliente(datos)
    Srv->>BD: INSERT cliente
    alt Documento repetido
        Srv-->>UI: 409 Ya existe un cliente con ese documento
    else Correcto
        Srv-->>UI: 201 cliente
    end
    Administrador->>UI: Registra o edita un vehículo y elige el cliente
    UI->>API: POST o PATCH /vehiculos con cliente_id
    API->>Srv: create o update vehículo
    Srv->>BD: INSERT o UPDATE vehiculo
    Srv-->>UI: Vehículo asociado al cliente
```

## 11. Diagrama de componentes

```mermaid
flowchart LR
    subgraph FE["Frontend — Angular 22 (frontend/src/app)"]
        direction TB
        pantallas["Pantallas standalone: home, login, control-acceso, vehiculos, celdas, operadores, clientes, mensualidades, reportes"]
        servicios["Servicios: ApiService, CeldasService, OperadoresService, ClientesService, EstanciasService, PagosService, AuthService"]
        seguridad["authGuard e interceptor de autenticación"]
        pantallas --> servicios
        pantallas --> seguridad
        seguridad --> servicios
    end
    subgraph BE["Backend — FastAPI (backend/app)"]
        direction TB
        routers["routers: auth, vehiculos, celdas, operadores, clientes, estancias, pagos, reportes"]
        auth["auth.py y security.py: JWT y PBKDF2"]
        services["services: reglas de negocio y transacciones"]
        schemas["schemas: validación Pydantic"]
        models["models.py: SQLAlchemy"]
        routers --> auth
        routers --> schemas
        routers --> services
        services --> models
    end
    DB[("PostgreSQL — autos_colombia, migraciones Alembic 0001 a 0004")]
    FE -- "HTTP JSON, proxy de desarrollo" --> BE
    models -- "psycopg" --> DB
```

Interfaces entre componentes: el frontend solo conoce la API HTTP (rutas
relativas, base centralizada en `ApiService`); el backend no expone la
estructura de la base de datos ni errores del controlador.
