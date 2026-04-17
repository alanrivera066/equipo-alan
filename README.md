# [Technova Inventory]
**Equipo:** [Alan Mauricio Rivera Garza]  
**Dominio:** [SISTEMA DE GESTION DE INVENTARIO]  
**Fecha:** 16 Abril 2026

---

## ¿Qué problema resuelve?
El sistema de Technova ayuda a tener un registro de los productos que se tienen en almacen,
permite controlar entradas y salidas de productos, ademas de generar alertas en caso de que 
algun producto no tenga el stock minimo requerido.

---

## Estructura de la Base de Datos

| Tabla               | Descripción                                      | Relación                          |
|---------------------|--------------------------------------------------|-----------------------------------|
| categorias          | Guarda los tipos de producto como electronica    | Ninguna                           |
| productos           | Guarda cada producto con su precio y stock       | Se relaciona con categorias       |
| movimientos         | Registra cada entrada o salida de inventario     | Se relaciona con productos        |
| alertas_reposicion  | Guarda las alertas cuando el stock queda bajo    | Se relaciona con productos        |

---

## Rutas de la API

| Método | Ruta                  | Qué hace                                              |
|--------|-----------------------|-------------------------------------------------------|
| GET    | /                     | Interfaz HTML principal                               |
| GET    | /categorias           | Devuelve la lista de categorías para el formulario    |
| GET    | /productos            | Consulta el stock actual de todos los productos       |
| POST   | /productos            | Registra un nuevo producto en el inventario           |
| POST   | /movimientos          | Registra una entrada o salida y activa alerta si baja |
| GET    | /productos/bajo-stock | Lista los productos por debajo de su stock mínimo     |
| GET    | /alertas              | Muestra todas las alertas de reposición generadas     |


---

## ¿Cuál es la tarea pesada y por qué bloquea el sistema?
[Explicar con sus palabras dónde está el time.sleep,
qué simula y qué pasa cuando llegan múltiples usuarios]

El servicio B tiene un time.sleep en la ruta de procesar alerta, esta ruta es 
la que se encarga de detectar cuando el stock del producto queda por debajo del minimo
despues de un movimiento de salida, el time sleep puede simular que se esta mandando un correo para notificar esta alerta
o generar un reporte, en esos 5 segundos el servicio A espera la respuesta antes de responderle al usuario, por lo que si
varios usuarios registran una salida al mismo tiempo, cada uno tiene que esperar.

---

## Cómo levantar el proyecto
```bash
# 1. Clonar el repositorio
git clone https://github.com/alanrivera066/equipo-alan.git

# 2. Entrar a la carpeta
cd equipo-alan

# 3. Crear las tablas en RDS
mysql -h db-actividades.cvpuussmrdm8.us-east-1.rds.amazonaws.com \
      -u admin -p < schema.sql

# 4. Levantar los contenedores con Docker Compose
#    (Las variables DOCKER_BUILDKIT evitan el error de BuildKit en Amazon Linux)
DOCKER_BUILDKIT=0 COMPOSE_DOCKER_CLI_BUILD=0 docker-compose up --build -d

# 5. Verificar que ambos servicios están corriendo
docker-compose ps

# 6. Abrir en el navegador
http://IP_EC2:5000
```

## Decisiones tecnicas
Decisiones técnicas
[Un párrafo explicando decisiones que tomaron: ¿por qué diseñaron las tablas así?, ¿cómo manejaron los errores?, ¿qué fue lo más difícil de implementar?]
Las cuatro tablas se crearon de esa manera para mantener las responsabilidades separadas, en el caso de las tablas "categorias" y "productos" son los que manejan el catalogo, 
la tabla "movimientos" guarda el historial de cambios de stock sin modificar el dato original, y "alertas_reposicion" es exclusivo para el servicio B para que cada microservicio tenga su propia tabla y no compartan escritura. El cómo se manejaron los errores fue usando bloques de "try/except/finally" en todas las rutas para asegurar que la conexion a la base de datos siempre se cierre, incluso si algo llega a fallar. Lo mas dificil fue implementar el time.sleep para simular la tarea pesada, ya que el servicio A respondia de manera inmediata sin esperar a que el servicio B procesara la alerta al momento de registrar una salida. Esto pasaba ya que el servicio B hacía este proceso en un hilo separado, por lo que al final tuve que eliminar ese hilo para posteriormente hacer la llamada directa, y de esta forma el servicio A espera la respuesta del servicio B antes de contestarle al usuario.
