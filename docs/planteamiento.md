# Plataforma de Gestión de talento

- Generar evaluaciones 360.
- Generar un sendero de carrera personalizado.
- desarrollo de colaboradores mediante análisis inteligente de competencias.

## Task

Desarrollar e implementar API's

- Conectar distintos componentes.
- Integración de servicios de IA.

## Preguntas

### ¿Qué es una evaluación 360°?

Una evaluación donde un usuario es evaluado desde múltiples perspectivas:

- self (autoevaluación)
- peers (compañeros de la misma área o nivel)
- manager (jefe directo)
- direct reports (trabajadores a cargo)

Reglas de negocio asociadas:
**Ciclo de evaluación**: Periodos, competencias a evaluar; ¿Quién evalúa a quien?.
**Evaluación 360 Completada**:
    - Usuario realizó Autoevaluación exitosamente.
    - manager realizó evaluación de usuario exitosamente.
    - Peers realizaron evaluación de usuario exitosamente.
En este caso es importante mencionar que para un mejor desempeño, idealmente debería realizarse evaluación de todos los Peers, managers, direct report, etc. pero se debería ajustar a un minimo de evaluaciones para facilitar el uso del sistema.

**¿El backend debería definir los pesos para el scoring de usuario?**
Es importante el manejo de sesgos en una capa entre el backend planteado en este documento y el servicio de IA principal para reducir costos.

Propuestas en este caso:

- Detectar outliers en las evaluaciónes.
- Internamente llevar un registro de quien evalúa a quien. Es decir: Suponiendo que un evaluador A con skills en cierto nivel en la ultima revisión evalúa al Usuario, cúanto peso tiene esta evaluación en comparación a las de un evaluador B con diferentes skills.
- Por trazabilidad la evaluación tal cual y la ponderada se tienen que guardar.


### ¿Qué es un sendero de carrera?

Una secuencia de pasos (roles + acciones de desarrollo) que lleva al Usuario desde su rol actual hacia uno o varios roles objetivo, en un horizonte de tiempo dado.

Reglas de negocio asociadas:

**Sendero**:
    - usuario.
    - posición actual.
    - roles de interés.
    - viabilidad del path.
    - steps entre la posición actual y el objetivo.
    - Requisitos de competencias y acciones de desarrollo asociadas.

### ¿Como definimos algo abstracto como "competencia o skill".

Una competencia debería tener definición, niveles y contexto. Sobre este asunto me parece que hay una gran cantidad de literatura encontrada como *Competency Model for talent management*. Por lo que no se pretende dar una solución robusta al problema. Solamente una versión dummy.


### ¿Las calificaciones quien las emite? hays sesgos involucrados por pairs o jefes?

Cada evaluación individual registra explícitamente:

- quién evalúa a quién (hidden),
- su rol en la relación con el evaluado (peer, manager, etc.),
- SI hay posibilidad de sesgos como se mencionó anteriormente pero tampoco corresponde ahondar en un modelo del sesgo.

### ¿La preparación de datos Para que los consuma la IA dependen de que? ¿Cuál es una manera eficaz para optimizar las request?

- Se sugiere que el envío de la data al LLM sea ya normalizada con los cálculos realizados para reducir tokens y el ruido.
- Puede ser que para la ventana de contexto del LLM se manden los dos ultimos ciclos de evaluación del usuario.

### ¿Las respuestas del modelo se guardan de manera estructurada en el serivcio principal conectado a posgres?.

- Si se guardan en dos puntos: Responses del LLM en crudo y y procesamiento de la response.

### NO es mi ambito pero el embeddings de acuerdo a la skill es eficiente?

### Relación entre puesto y skills: ¿qué pesa más?

Un puesto debe tener asociado:

- lista de skills requeridas,
- nivel requerido por competencia,
- peso relativo de cada competencia,
- (Opcional) banda salarial
- (Opcional) Posible un esquema de nivel de seniority dado el rol o años requeridos como referencia.
