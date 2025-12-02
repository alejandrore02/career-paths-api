# flows.md

## Talent Management / Career Paths API – Flujos de Procesamiento

Este documento describe **paso a paso** los flujos principales del sistema, especificando:

- Componentes que participan
- Orden de ejecución
- Datos que se transforman
- Manejo de asincronía
- Manejo de errores y consistencia

---

## 1. Componentes principales (referencia)

- **Routers (FastAPI)**  
  - `health.py` — Health checks
  - `evaluation_cycles.py` — Gestión de ciclos
  - `evaluations.py` — Evaluaciones 360°
  - `skills_assessments.py` — Skills assessments con IA
  - `career_paths.py` — Senderos de carrera
  - `users.py` — Gestión de usuarios
  - `skills.py` — Catálogo de competencias
  - `roles.py` — Roles organizacionales

- **Servicios de aplicación**
  - `EvaluationService` — Evaluaciones 360° y agregación
  - `EvaluationCycleService` — Gestión de ciclos
  - `SkillsAssessmentService` — Skills assessment con IA
  - `CareerPathService` — Career paths con IA
  - `UserService` — CRUD de usuarios
  - `SkillService` — CRUD de competencias
  - `RoleService` — CRUD de roles

- **Repositorios / UoW**
  - `EvaluationRepository`
  - `EvaluationCycleRepository`
  - `SkillsAssessmentRepository`
  - `CareerPathRepository`
  - `UserRepository`
  - `SkillRepository`
  - `RoleRepository`
  - `UnitOfWork` (control transaccional)

- **Integraciones IA**
  - `AISkillsClient`  
    - Simula servicio de skills assessment
    - Usa circuit breaker + retry decorators
  - `AICareerClient`  
    - Simula servicio de career paths
    - Usa circuit breaker + retry decorators

- **Dominio / lógica**
  - `evaluation_logic.py` (cálculo de porcentaje completado por ciclo, agregación de evaluaciones, etc.)
  - Lógica de gap analysis (comparar `user_skill_scores` vs `role_skill_requirements`)

---

## 2. Flujo 1 – Procesamiento de Evaluación 360° → Skills Assessment → Career Path

### 2.1 Descripción general

Objetivo:  
Cuando un colaborador complete todas las evaluaciones 360° (self, peers, manager, direct reports), el sistema debe:

1. Detectar que el **ciclo de evaluación** está completo para ese usuario.
2. Agregar y consolidar resultados de las evaluaciones (`user_skill_scores`).
3. Llamar al servicio de IA de **Skills Assessment**.
4. Persistir el **Skills Assessment** y sus ítems detallados.
5. Llamar al servicio de IA de **Career Paths**.
6. Persistir los **senderos de carrera**, pasos y acciones de desarrollo.
7. Notificar al usuario o al sistema cliente (según integración futura).

Este flujo se orquesta desde el endpoint:

- `POST /api/v1/evaluations/{evaluation_id}/process`

y puede extenderse en el futuro a un procesamiento automático por ciclo.

---

### 2.2 Paso a paso detallado

#### Paso 1 – Creación y actualización de evaluaciones

**Endpoint principal:** `POST /api/v1/evaluations` (router `evaluations.py`)  

**Componentes:**

- `evaluations.py` (router FastAPI)
- `EvaluationService.create_evaluation`
- `EvaluationRepository`
- Tablas:
  - `evaluations`
  - `evaluation_competency_scores`

**Flujo detallado:**

1. El frontend envía una petición HTTP `POST` con:
   - `user_id` (colaborador evaluado).
   - `evaluation_cycle_id`.
   - `evaluator_id`.
   - `evaluator_relationship` (manager, peer, direct_report, self).
   - Lista de competencias con:
     - nombre de la competencia (o `competency_name`).
     - score numérico dentro del rango permitido (por ejemplo 1–10).
     - comentarios opcionales.

**Nota** En la BD la tabla de catálogo es skills, pero conceptualmente corresponde a las “competencias” (competenciess)

   **Ejemplo de request:**

   ```json
   {
     "user_id": "f8c0c3c4-8a0f-4e2e-bf84-2a6b9a4f1b10",
     "evaluation_cycle_id": "a1b2c3d4-0000-1111-2222-333344445555",
     "evaluator_id": "9e7c6a51-3d42-4d3f-a9c2-1a2b3c4d5e6f",
     "evaluator_relationship": "manager",
     "competencies": [
       {
         "competency_name": "Liderazgo",
         "score": 8,
         "comments": "Demuestra gran capacidad para coordinar al equipo."
       },
       {
         "competency_name": "Comunicación",
         "score": 9,
         "comments": "Explica objetivos con claridad."
       }
     ]
   }

  ```

2. El router:
   - Valida el body contra el esquema Pydantic v2.
   - Si hay errores de validación (por ejemplo score fuera de rango):
     - Responde con código HTTP 400.
     - Body con un objeto de error estándar, incluyendo un código (`validation_error`) y detalle.

3. `EvaluationService.create_evaluation`:
   - Verifica que:
     - `user_id` existe en `users`.
     - `evaluator_id` existe en `users`.
     - `evaluation_cycle_id` existe y el ciclo está en estado activo.
   - Crea un registro en `evaluations` con:
     - `status = "submitted"`.
     - `evaluator_relationship` según la entrada.
   - Normaliza las competencias:
     - Para cada elemento de la lista:
       - Resuelve el `skill_id` a partir del `competency_name` en el catálogo `skills`.
       - Crea una fila en `evaluation_competency_scores` con `score` y `comments`.

4. El `UnitOfWork`:
   - Ejecuta `commit()` si todo fue correcto.
   - En caso de error de BD:
     - Realiza `rollback()`.
     - El servicio lanza una excepción que se mapea a un `HTTP 500` o `409` según el tipo de error.

5. El router responde:
   - Código 201 Created.
   - Cuerpo con:
     - `evaluation_id`.
     - `user_id`.
     - `status` (submitted).
     - `created_at`.

    ```json
    {
        "evaluation_id": "11111111-2222-3333-4444-555555555555",
        "user_id": "f8c0c3c4-8a0f-4e2e-bf84-2a6b9a4f1b10",
        "evaluation_cycle_id": "a1b2c3d4-0000-1111-2222-333344445555",
        "evaluator_id": "9e7c6a51-3d42-4d3f-a9c2-1a2b3c4d5e6f",
        "evaluator_relationship": "manager",
        "status": "submitted",
        "created_at": "2025-01-15T10:30:00Z"
    }
    ```

    el manejo de errores sigue el wrapper:

    ```json
    {
    "error": "",
    "message": "",
    "details": []
    }
    ```

  El uso de errores no está harcodeado si no definido en un archivo constants para manejar los distintos status, errors y messages
---

#### Paso 2 – Detección de ciclo completo para un usuario

Este paso se dispara cuando se llama a:

- `POST /api/v1/evaluations/{evaluation_id}/process`

**Componentes:**

- `EvaluationService.process_evaluation`
- `EvaluationRepository`
- `evaluation_logic.py` (para reglas de “ciclo completo”)

**Flujo detallado:**

1. El router recibe el `evaluation_id` en la ruta y lo valida como UUID.
2. Llama a `EvaluationService.process_evaluation(evaluation_id)`.

    Dentro del servicio:

3. Se recupera la `Evaluation`:
   - Si no existe → error 404 (evaluation not found).
4. A partir de esa evaluación se obtiene:
   - `user_id` (evaluado).
   - `evaluation_cycle_id`.
5. Se consultan todas las evaluaciones de ese usuario en ese ciclo:
   - Filtra en `evaluations` por `user_id` y `evaluation_cycle_id`.
6. `evaluation_logic` aplica las reglas de completitud:
   - Por ejemplo:
     - Debe existir al menos 1 evaluación `self`.
     - Al menos 1 `manager`.
     - Al menos un número configurable de `peers` y `direct_reports`.
   - Si las condiciones no se cumplen:
     - Puede devolver un 409 (conflict) indicando que el ciclo no está listo para procesamiento.
   - Si se cumplen:
     - Continúa con el siguiente paso.

---

#### Paso 3 – Agregación de resultados en `user_skill_scores`

**Objetivo:**  
Transformar evaluaciones individuales en un perfil consolidado por competencia para el usuario en ese ciclo.

**Componentes:**

- `EvaluationRepository` (para leer evaluaciones y scores).
- `UserSkillScoresRepository` o repositorio equivalente.
- Tabla `user_skill_scores`.
- `evaluation_logic.py` (agregación por competencia y relación).

**Flujo detallado:**

1. A partir de las evaluaciones obtenidas, se construye una vista interna por competencia:
   - Para cada `skill`:
     - Recopilar scores donde:
       - `evaluator_relationship = "self"`.
       - `evaluator_relationship = "peer"`.
       - `evaluator_relationship = "manager"`.
       - `evaluator_relationship = "direct_report"`.
   - Calcular métricas como:
     - Promedio global.
     - Promedios por relación (self, peers, manager, direct_reports).
     - Número de evaluaciones por relación.
     - Desviación estándar (opcional).

2. Se limpian datos previos:
   - Borrar o marcar como obsoletos los `user_skill_scores` para ese `user_id` y `evaluation_cycle_id` si ya existían.

3. Se insertan nuevas filas en `user_skill_scores`:
   - Por cada combinación `(user_id, evaluation_cycle_id, skill_id)`:
     - `source = "360_aggregated"` (o similar).
     - `score` = promedio global.
     - `confidence` = función de n y dispersión.
     - `raw_stats` = JSON resumido (contando cuántos self, peers, etc.).

4. Transacción:
   - Marcado de obsoletos los datos antiguos + inserción de los nuevos se hace dentro de una misma transacción.
   - En caso de error se hace rollback y no se deja el perfil en un estado inconsistente.

---

#### Paso 4 – Construcción del payload para el Servicio IA de Skills Assessment

**Objetivo:**  
Tomar la información consolidada y construir el objeto `evaluation_data` que requiere el equipo de ML.

**Componentes:**

- `SkillsAssessmentService` (o parte de `EvaluationService` que prepara el payload).
- `AISkillsAssessmentClient`.

**Datos de entrada necesarios:**

- `user_id`.
- Perfil de competencias del usuario en el ciclo:
  - Para cada competencia:
    - Nombre de la competencia (string legible).
    - Score self (promedio).
    - Lista de scores de peers.
    - Score de manager.
    - Lista de scores de direct reports.
- `current_position`:
  - Derivado del rol actual del usuario (`roles.name`).
- `years_experience`:
  - Derivable de `hire_date` y fecha actual o configurado manualmente.

**Flujo detallado:**

1. A partir de `user_skill_scores` y las evaluaciones crudas:
   - Se reconstruyen las listas de scores por relación para cada competencia.
2. Se arma un objeto en memoria con:
   - ID de usuario.
   - Estructura `evaluation_data` con una lista de competencias.
   - Posición actual.
   - Años de experiencia.
3. No se guarda aún en BD; este objeto se pasa directamente al `AISkillsAssessmentClient`.

---

#### Paso 5 – Llamada al Servicio IA de Skills Assessment

**Componentes:**

- `AISkillsAssessmentClient.assess_skills(...)`
- Tabla `skills_assessments`
- Tabla `skills_assessment_items`
- Tabla `ai_calls_log`

**Flujo detallado:**

1. Antes de la llamada:
   - Crear una entrada en `ai_calls_log`:
     - `service_name = "skills_assessment"`.
     - `user_id`.
     - `evaluation_cycle_id`.
     - `request_payload` (payload construido).
     - `status = "pending"`.

2. Llamada al servicio IA (simulado):
   - `AISkillsAssessmentClient` recibe:
     - `user_id`
     - `evaluation_data`
     - `current_position`
     - `years_experience`
     
     Ejemplo Request: 

     ```json
     {
        "user_id": "uuid",
        "evaluation_data": {
        "competencies": [
        {
        "name": "Liderazgo",
        "self_score": 8,
        "peer_scores": [7, 8, 9],
        "manager_score": 7,
        "direct_report_scores": [8, 8]
        },
        {
        "name": "Comunicación",
        "self_score": 7,
        "peer_scores": [8, 7, 8],
        "manager_score": 8,
        "direct_report_scores": [7, 8]
        }
        ]
        },
        "current_position": "Gerente de Sucursal",
        "years_experience": 5
     }
     ```

   - El cliente:
     - Simula latencia.
     - Devuelve una estructura con:
       - Un identificador de assessment.
       - Perfil de habilidades (fortalezas, áreas de crecimiento, talentos ocultos).
       - Información de readiness por rol.
       - Timestamp.

    Ejemplo response 200:

    ```json
    {
        "assessment_id": "uuid",
        "user_id": "uuid",
        "skills_profile": {
        "strengths": [
        {
        "skill": "Comunicación",
        "proficiency_level": "Avanzado",
        "score": 7.8,
        "evidence": "Consistentemente evaluado positivamente por pares y equipo"
        }
        ],
        "growth_areas": [
        {
        "skill": "Liderazgo",
        "current_level": "Intermedio",
        "target_level": "Avanzado",
        "gap_score": 1.2,
        "priority": "Alta"
        }
        ],
        "hidden_talents": [
        {
        "skill": "Gestión de Conflictos",
        "evidence": "Identificado a través de análisis de feedback cualitativo",
        "potential_score": 8.5
        }
        ]
        },
        "readiness_for_roles": [
        {
        "role": "Gerente Regional",
        "readiness_percentage": 65,
        "missing_competencies": ["Pensamiento Estratégico", "Gestión de P&L"]
        }
    }
    ```

3. Manejo de errores:
   - Si el cliente lanza excepciones por timeout o error HTTP:
     - Actualizar `ai_calls_log` con `status = "timeout"` o `"error"`.
     - Registrar `error_message`.
     - Actualizar `skills_assessments` (si ya se creó) con `status = "failed"`.
     - Devolver al caller un 502 o 500, según convenga para la API pública.

4. Si la llamada es exitosa:
   - Actualizar `ai_calls_log` con:
     - `status = "success"`.
     - `response_payload`.
     - `latency_ms`.
   - Crear una fila en `skills_assessments`:
     - Relacionada a `user_id` y `evaluation_cycle_id`.
     - `status = "completed"`.
     - Guardar la respuesta completa en `raw_response`.
   - Crear una serie de `skills_assessment_items`:
     - Para fortalezas (`item_type = "strength"`).
     - Para áreas de crecimiento (`item_type = "growth_area"`).
     - Para talentos ocultos (`item_type = "hidden_talent"`).
     - Para readiness por rol (`item_type = "role_readiness"`).

5. Transacción:
   - Inserción en `skills_assessments` + `skills_assessment_items` se hace en una transacción.
   - El log de IA se puede escribir en la misma u otra transacción, pero debe garantizar trazabilidad.

---

#### Paso 6 – Construcción del payload para el Servicio IA de Career Paths

**Objetivo:**  
A partir del `skills_assessment` generado, preparar la entrada para `/api/ai/career-paths`.

**Componentes:**

- `CareerPathService` o parte dedicada a IA en `SkillsAssessmentService`.
- `AICareerPathClient`.

**Datos de entrada necesarios:**

- `user_id`.
- `skills_assessment_id`.
- `current_position` (de nuevo, rol actual).
- `career_interests` (lista de strings; se puede simular).
- `time_horizon_years` (por ejemplo 3).
- `organization_structure`:
  - Lista de roles disponibles en la organización, derivada de `roles`.

**Flujo detallado:**

1. Se toma el `skills_assessment` recién creado.
2. Se arma un objeto en memoria con:
   - `user_id`.
   - `skills_assessment_id`.
   - Posición actual.
   - Intereses de carrera (simulados o provenientes de otra fuente).
   - Horizonte de tiempo.
   - Roles disponibles (por ejemplo, todos los `roles` activos o un subconjunto filtrado).

3. Este objeto se envía al `AICareerPathClient`.

---

#### Paso 7 – Llamada al Servicio IA de Career Paths

**Componentes:**

- `AICareerPathClient.generate_career_paths(...)`
- Tablas:
  - `career_paths`
  - `career_path_steps`
  - `development_actions`
  - `ai_calls_log`

**Flujo detallado:**

1. Registrar en `ai_calls_log`:
   - `service_name = "career_paths"`.
   - `user_id`.
   - `skills_assessment_id`.
   - `request_payload`.
   - `status = "pending"`.

2. `AICareerPathClient` llama al servicio IA (simulado):
   - Devuelve:
     - Un identificador de career path global.
     - Lista de rutas generadas.
     - Para cada ruta:
       - Nombre.
       - Flag `recommended`.
       - Duración total en meses.
       - Feasibility score.
       - Pasos, cada uno con:
         - Número de paso.
         - Rol objetivo (como texto).
         - Duración del paso.
         - Competencias requeridas y acciones sugeridas.

3. Manejo de errores:
   - Igual que con el servicio de skills:
     - Actualizar log con `status` de error o timeout.
     - No crear rutas de carrera si la IA falla.
     - Devolver un error HTTP apropiado hacia la API pública.

4. Si la respuesta es exitosa:
   - Actualizar `ai_calls_log` a `status = "success"` con `response_payload`.
   - Por cada ruta generada:
     - Crear una fila en `career_paths`:
       - `user_id`.
       - `skills_assessment_id`.
       - `path_name`, `recommended`, `feasibility_score`, `total_duration_months`.
       - Estado inicial, por ejemplo `"proposed"`.
     - Por cada paso:
       - Insertar `career_path_steps`:
         - `career_path_id`.
         - `step_number`.
         - Buscar `target_role_id` en `roles` a partir del nombre del rol.
         - Duración del paso y descripción opcional.
       - Por cada acción de desarrollo sugerida:
         - Insertar `development_actions`:
           - `career_path_step_id`.
           - Asociar `skill_id` si se reconoce el nombre de la competencia.
           - `action_type` (course, project, mentoring, etc.).
           - `title` con el nombre de la acción.
           - Otras propiedades (proveedor, url, esfuerzo estimado) si se mapean.
    
    ejemplo de respuesta exitosa:

    ```json
            {
        "career_path_id": "uuid",
        "user_id": "uuid",
        "generated_paths": [
        {
        "path_id": "uuid",
        "path_name": "Ruta de Liderazgo Regional",
        "recommended": true,
        "total_duration_months": 24,
        "feasibility_score": 0.85,
        "steps": [
        {
        "step_number": 1,

        "target_role": "Gerente de Sucursal Senior",
        "duration_months": 12,
        "required_competencies": [
            {
            "name": "Pensamiento Estratégico",
            "current_level": 5,
            "required_level": 7,
            "development_actions": [
            "Curso: Estrategia de Negocios Avanzada",
            "Proyecto: Plan estratégico para sucursal",
            "Mentoría con Gerente Regional"
                ]
            }
            ]
        },
        {
            "step_number": 2,
            "target_role": "Gerente Regional",
            "duration_months": 12,
            "required_competencies": [
                {
                    "name": "Gestión de P&L",
                    "current_level": 4,
                    "required_level": 8,
                    "development_actions": [
                    "Certificación: Finanzas para Managers",
                    "Shadowing: Director Financiero",
                    "Proyecto: Análisis de rentabilidad regional"
                    ]
                }
            ]
        }
        ]
        },
        {
        "path_id": "uuid",
        "path_name": "Ruta de Especialización en Operaciones",
        "recommended": false,
        "total_duration_months": 18,
        "feasibility_score": 0.72,
        "steps": [...]
        }
        ],
        "timestamp": "2025-01-15T10:35:00Z"
            }
        
    ```

5. Transacción:
   - Inserción de un conjunto consistente:
     - `career_paths`
     - `career_path_steps`
     - `development_actions`
   - Se hace dentro de una transacción.
   - Si falla en medio, se revierte todo el conjunto para evitar rutas incompletas.

---

#### Paso 8 – Respuesta del endpoint de procesamiento

**Para el endpoint:** `POST /api/v1/evaluations/{evaluation_id}/process`

- se ejecuta en **background** (recomendado para producción):
  - El endpoint responde 202 Accepted indicando que:
    - La evaluación ha sido marcada para procesamiento.
    - El resultado estará disponible posteriormente en:
      - `GET /api/v1/skills-assessments/{user_id}/latest`
      - `GET /api/v1/career-paths/{user_id}`

---

## 3. Flujo 2 – Consulta de Senderos de Carrera

### 3.1 `GET /api/v1/career-paths/{user_id}` – Listar senderos de carrera del usuario

**Objetivo:**  
Permitir que el usuario consulte las rutas de carrera propuestas/generadas por la IA.

**Componentes:**

- Router `career_paths.py`
- `CareerPathService.get_paths_for_user(user_id)`
- `CareerPathRepository`
- Tablas:
  - `career_paths`

**Flujo detallado:**

1. El router recibe `user_id` como parámetro de ruta.
2. `CareerPathService`:
   - Verifica que el usuario existe y está activo (opcional).
   - Consulta `career_paths` filtrando por:
     - `user_id`.
     - Estados relevantes (por ejemplo `proposed`, `accepted`, `in_progress`).
   - Ordena:
     - Primero rutas recomendadas (`recommended = true`).
     - Después por fecha de creación o factibilidad.

3. El servicio construye una lista resumida por cada `career_path`:
   - Identificador.
   - Nombre de la ruta.
   - Estado actual.
   - Indicador de recomendación.
   - Score de factibilidad.
   - Duración total estimada.

4. El router responde con una lista de rutas resumidas para el usuario.

---

### 3.2 `GET /api/v1/career-paths/{path_id}/steps` – Detalle de un sendero específico

**Objetivo:**  
Mostrar los pasos de un sendero concreto y las acciones de desarrollo asociadas.

**Componentes:**

- Router `career_paths.py`
- `CareerPathService.get_path_detail(path_id)`
- Tablas:
  - `career_paths`
  - `career_path_steps`
  - `development_actions`
  - `roles` (para enriquecer el nombre del rol objetivo)

**Flujo detallado:**

1. El router recibe `path_id` y lo valida como UUID.
2. `CareerPathService`:
   - Busca en `career_paths`:
     - Si no existe → 404.
   - Recupera todos los `career_path_steps` asociados, ordenados por `step_number`.
   - Para cada step:
     - Enriquecer con el `target_role` si `target_role_id` está presente (consultando `roles`).
     - Recuperar `development_actions` asociadas.

3. Se arma una respuesta con:
   - Datos del sendero (id, nombre, estado, etc.).
   - Lista de pasos:
     - Número de paso.
     - Rol objetivo en texto.
     - Duración estimada.
     - Lista de acciones:
       - Tipo de acción (curso, proyecto, mentoría).
       - Título.
       - Información adicional si existe (proveedor, url, horas estimadas).

4. El router devuelve la estructura al cliente.

---

### 3.3 `POST /api/v1/career-paths/{path_id}/accept` – Marcar un sendero como aceptado

**Objetivo:**  
Permitir que el colaborador seleccione una de las rutas propuestas como su ruta de desarrollo activa.

**Componentes:**

- Router `career_paths.py`
- `CareerPathService.accept_path(path_id, user_id_actual)`
- `CareerPathRepository`
- Tabla:
  - `career_paths`

**Flujo detallado:**

1. El router recibe `path_id` y utiliza el `user_id` autenticado (cuando exista autenticación).
2. `CareerPathService`:
   - Valida que:
     - El `career_path` existe.
     - Pertenece al `user_id_actual`.
     - Su estado es `"proposed"`.
   - Actualiza el sendero:
     - `status = "accepted"`.
   - Opcionalmente:
     - Actualiza otros senderos del mismo usuario a `discarded` o `alternative`.

3. Transacción:
   - La actualización de estados se hace en una transacción.
   - Evitar estados inconsistentes (por ejemplo, dos rutas marcadas como `accepted` si no se desea).

4. El router:
   - Responde con 200 OK y un resumen del sendero aceptado.
   - En caso de errores:
     - 404 si el sendero no existe.
     - 403 si no pertenece al usuario.
     - 409 si el estado no permite aceptación (por ejemplo ya `accepted` o `completed`).

---

## 4. Flujo 3 – Consulta del último Skills Assessment

### 4.1 `GET /api/v1/skills-assessments/{user_id}/latest`

**Objetivo:**  
Obtener el último assessment de habilidades generado para un usuario.

**Componentes:**

- Router `skills_assessments.py`
- `SkillsAssessmentService.get_latest_for_user(user_id)`
- `SkillsAssessmentRepository`
- Tablas:
  - `skills_assessments`
  - `skills_assessment_items`

**Flujo detallado:**

1. El router recibe `user_id` como parámetro de ruta.
2. `SkillsAssessmentService`:
   - Busca el último `skills_assessments` del usuario:
     - Ordenado por `processed_at` (descendente) o `created_at`.
   - Si no encuentra ninguno:
     - Devolver 404 con un mensaje indicando que no hay assessment disponible.
   - Si encuentra:
     - Puede recuperar un subconjunto de `skills_assessment_items`:
       - Por ejemplo:
         - top 3 fortalezas.
         - top 3 áreas de crecimiento.
         - resumen de readiness por rol.

3. El servicio construye una respuesta:
   - Con identificador del assessment.
   - Estado (`completed`, `failed`).
   - Resumen textual (opcional).
   - Listas resumidas de fortalezas, áreas de crecimiento y readiness.

4. El router devuelve la estructura resultante.

---

## 5. Consideraciones transversales

### 5.1 Manejo de asincronía

- Todos los clientes IA (`AISkillsAssessmentClient`, `AICareerPathClient`) deben ser `async`.
- `EvaluationService.process_evaluation` puede:
  - Ejecutar el pipeline completo de forma síncrona para la prueba.
  - O en producción:
    - Disparar tareas en background para no bloquear el request.
- Es importante no bloquear el event loop con lógica pesada o I/O sincrónico.

### 5.2 Manejo de errores

- Errores de validación:
  - Responder con 400.
  - Incluir códigos de error (`validation_error`, etc.).
- Recursos no encontrados:
  - 404 (`evaluation_not_found`, `career_path_not_found`, etc.).
- Conflictos de estado:
  - 409 (`cycle_not_complete`, `path_not_proposed`, etc.).
- Errores de servicios IA:
  - Idealmente 502 (`ai_service_unavailable`).
  - Mantener registro en `ai_calls_log`.

### 5.3 Consistencia de datos

- Todas las operaciones que escriban múltiples tablas deben usar transacciones:
  - Creación de evaluaciones y scores.
  - Agregación de `user_skill_scores`.
  - Persistencia de resultados IA (assessments, rutas, pasos, acciones).
- En caso de fallo:
  - Hacer rollback.
  - No dejar datos intermedios que rompan integridad.

---
