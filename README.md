# Alarm Gateway Pipeline - Industrial Data Analytics

Este proyecto es una solución integral para el procesamiento, limpieza y análisis de alarmas industriales (SCADA/Gateway). La arquitectura está diseñada bajo principios de ingeniería de software moderna, permitiendo la transición de scripts aislados a una API robusta y contenedorizada.

## 1. Descripción de la Solución

El sistema implementa un pipeline ETL (Extract, Transform, Load) que:
1.  **Ingesta:** Recibe archivos de datos brutos (CSV).
2.  **Limpia:** Utiliza un módulo especializado (`AlarmCleaner`) para validar marcas de tiempo, eliminar duplicados y corregir inconsistencias lógicas.
3.  **Persiste:** Almacena los datos limpios en una base de datos MySQL gestionada por SQLAlchemy.
4.  **Analiza:** Expone una API REST con FastAPI para consultar métricas clave, como el "Top de Tags" con más alarmas.

## 2. Decisiones Arquitectónicas

Se optó por una **Arquitectura en Capas** para garantizar el mantenimiento y la escalabilidad:

* **Capa de Aplicación (FastAPI):** Gestiona las rutas y la lógica de los endpoints.
* **Capa de Dominio:** Contiene la lógica de limpieza y procesamiento (Clase `AlarmCleaner`). Se separó de la API para permitir su uso en scripts de consola o procesos batch.
* **Capa de Persistencia (SQLAlchemy):** Implementa el patrón *Data Mapper* para desacoplar el modelo de datos de la infraestructura de la base de datos.
* **Contenedorización (Docker):** Se utiliza `docker-compose` para orquestar la API y la base de datos, garantizando que el entorno de ejecución sea idéntico en cualquier máquina.



## 3. Justificación de Decisiones Técnicas

* **Python + Pandas:** Se eligió para la fase de limpieza por su eficiencia en el manejo de estructuras vectorizadas, ideal para datos industriales masivos.
* **MySQL 8.0:** Proporciona un motor de persistencia robusto y estándar en la industria.
* **Validación de Datos (Supuestos):**
    * Se asume que los timestamps deben ser cronológicos o nulos.
* **Type Hinting:** Todo el código utiliza tipado estático de Python para reducir errores en tiempo de ejecución y mejorar la documentación interna.

## 4. Instrucciones de Ejecución

### Requisitos Previos
* Docker y Docker Desktop instalados.
* Git.

### Instalación y Despliegue

1. **Clonar el repositorio:**
   ```bash
   git clone [https://github.com/tu-usuario/alarm-gateway.git](https://github.com/tu-usuario/alarm-gateway.git)
   cd alarm-gateway

2. **Configurar variables de entorno:**
Crea un archivo .env en la raíz con los siguientes valores:

DB_PASSWORD=tu_password_seguro
DB_NAME=alarm_db
DB_USER=root
DB_HOST=db

3. **Levantar el entorno con Docker:**

docker-compose up --build

Este comando descargará las imágenes, instalará las dependencias y levantará la API en el puerto 8000.

4. **Acceso a la documentación:**
Una vez encendido, abre tu navegador en:

API: http://localhost:8000/docs (Swagger UI interactivo)

5. **Estructura del Proyecto**

├── src/
│   ├── api/            # Endpoints y rutas de FastAPI
│   ├── database/       # Configuración de SQLAlchemy y modelos
│   ├── modules/        # Scripts de carga inicial de datos
│   ├── config.py       # Script de configuración
│   └── main.py         # Entry Point
├── data/               # Almacenamiento de datos
├── Dockerfile          # Configuración de imagen de la API
├── docker-compose.yml  # Orquestación de servicios
└── requirements.txt    # Dependencias de Python