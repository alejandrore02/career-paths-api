# Discusión de Arquitectura

El sistema presenta una arquitectura basada en capas como se puede observar en el diagrama de `ARCHITECTURE.md`. La razón de dividirlo de esta manera es:

- **separar las responsabilidades de cada capa**, es decir, los endpoints o routers unicamente manejan la solicitud http, los servicios orquestan, las reglas de negocio están presentes en el domain unicamente y las integraciones de servicios están aislados.

- Nos proporciona cierto equilibrio entre velocidad de deasrrollo - flexibilidad que otros tipo de arquitecturas se pueden llevar en tiempo corto pero con mayor acoplamiento u otros tipos de arquitectura como de microservicios que requiere más tiempo de desarrollo.

## Patterns

la **inyección de dependencias** es un *must* en cualquier proyecto de desarrollo. Especialmente para tener menos acoplamiento entre componenter y un testeo más sencillo.

**Unit of Work** Se planteó para poder llevar transacciones atómicas en la BD. Especialmente al estar integrando y procesando con servicios externos me parece importante tener un servicio así para que en caso de fallo, los potenciales errores no corrompan la BD.

El **Repository Pattern** se usa para encapsular el acceso a datos por agregado de dominio (users, evaluations, skills, roles, career_paths, etc.).  
La idea es que los servicios de aplicación no conozcan detalles de SQLAlchemy ni de la base de datos, sino que trabajen con métodos de más alto nivel (`get_by_email`, `list_by_cycle`, `create`, etc.).

El **Service Layer Pattern** organiza la lógica de negocio en servicios de aplicación (por ejemplo, `EvaluationService`, `SkillsAssessmentService`, `CareerPathService`).  
Los routers no contienen reglas de negocio, solo delegan en estos servicios. De esta forma:

- se evita duplicar lógica entre endpoints,
- se pueden probar los casos de uso directamente (sin pasar por HTTP),
- y se mantiene una separación clara entre “hablar HTTP” y “resolver el problema de negocio”.

La **separación de Domain Logic** (Domain Layer) permite aislar reglas puras de negocio de cualquier detalle técnico.  
Cosas como:

- reglas para considerar un ciclo de evaluación como “completo” o “incompleto”,
- cómo se agregan scores,
- cómo se hace un gap analysis,
se implementan en funciones y tipos de dominio que no dependen de FastAPI, SQLAlchemy ni de servicios externos. Esto hace más fácil razonar, probar y reutilizar esa lógica.

El uso de **DTOs / Schemas con Pydantic v2** sigue el patrón clásico de separación entre:

- modelos de dominio / BD,
- y modelos de transporte (entrada/salida de la API).
Los `*Create`, `*Update` y `*Response` permiten definir contratos claros hacia el frontend, con validación automática y sin exponer directamente los modelos internos de la base de datos.

El patrón de **Error Handling centralizado** agrupa los errores del dominio en excepciones propias (`NotFoundError`, `ValidationError`, `ConflictError`, etc.) y un handler global que las transforma en respuestas JSON consistentes.  
El objetivo es:

- tener un formato homogéneo de errores,
- evitar `try/except` repetidos por toda la app,
- y poder mapear de forma clara errores de negocio → códigos HTTP.

El patrón de **Retry con backoff exponencial** se aplica únicamente en las integraciones con servicios externos (IA).  
En lugar de mezclar lógica de reintentos en cada método, se usa un decorador configurable (`with_retry`) que:

- reintenta un número limitado de veces,
- espera cada vez un poco más,
- y solo se aplica donde tiene sentido (clients HTTP).  
Esto mejora la resiliencia sin ensuciar la lógica de negocio.

El **Circuit Breaker** complementa al retry y también se aplica solo en las integraciones.  
Cuando un servicio externo empieza a fallar de manera repetida, el circuito se “abre” y el sistema deja de llamar temporalmente a ese servicio, fallando rápido. Esto protege tanto a la API como al proveedor de IA, y evita quedarse atascado en timeouts constantes.

## ¿Qué debería seguir?

Este planteamiento podría extenderse aún más sin comprometer el escalamiento de la app.

Se creo una carpeta de `middleware` que no se implementó puesto que en esta lo más posible es que se implemente la autenticación de usuario, por ejemplo con JWT, roles de usuario, etc.

Después de eso lo más seguro es implementar REDIS para caché de lectura para el usuario y reducir la carga en la BD.

También es importante implementar un rate limiting en los endpoints, con la api key por ejemplo. Los servicios de IA no están accesibles directamente desde la api pero es importante tomarlo en cuenta para futuros escenarios.

Para escalar la app, en especifico de los servicios de IA sería bueno incorporar una queue para procesar peticiones a los servicios externos. 