# Generador Automático de Informes de Análisis de Tweets

Este proyecto implementa un sistema para analizar automáticamente un conjunto de tweets. Utiliza un Modelo de Lenguaje Grande (LLM) configurado a través de Ollama para:
1.  **Extraer categorías temáticas** de una muestra de tweets.
2.  **Clasificar** cada tweet dentro de las categorías extraídas.
3.  **Calcular estadísticas** (distribución de sentimiento, engagement) para cada categoría.
4.  **Generar un informe detallado** en formato Markdown que resume los hallazgos.

El sistema está diseñado para ser flexible, permitiendo configurar el modelo LLM, los parámetros de categorización y los directorios de salida a través de un archivo `.env`.

## Características Principales

-   **Carga de Tweets**: Lee datos de tweets desde un archivo JSON.
-   **Categorización Dinámica**: Extrae categorías temáticas relevantes directamente de los datos usando el LLM, en lugar de usar categorías predefinidas.
-   **Clasificación Basada en LLM**: Asigna cada tweet a la categoría más apropiada utilizando el LLM.
-   **Análisis Estadístico**: Calcula métricas clave por categoría, como distribución de sentimientos y engagement promedio.
-   **Generación de Informes**: Crea informes completos en Markdown, incluyendo resúmenes, estadísticas y ejemplos por categoría.
-   **Estructura Organizada**: Mantiene los logs, tweets categorizados (caché) y reportes finales en directorios separados.
-   **Configuración Centralizada**: Utiliza un archivo `.env` para gestionar todas las configuraciones importantes.
-   **Manejo de Modelos**: Permite especificar fácilmente qué modelo LLM (disponible en Ollama) se debe usar.

## Requisitos

-   **Python 3.11**: Se recomienda usar `conda` para gestionar el entorno.
-   **Ollama**: Debe estar instalado y ejecutándose. [Instrucciones de Ollama](https://ollama.com/)
-   **Un Modelo LLM en Ollama**: El modelo especificado en `.env` (por ejemplo, `gemma3:latest`, `phi4`, `granite3.2:latest`, etc.) debe estar descargado (`ollama pull <nombre_modelo>`).
-   **Dependencias de Python**: Listadas en `requirements.txt`.

## Instalación y Configuración

Sigue estos pasos para poner en marcha el proyecto:

1.  **Clonar el Repositorio**:
    ```bash
    git clone <url-del-repositorio>
    cd <directorio-del-proyecto>
    ```

2.  **Crear Entorno Conda (Recomendado)**:
    Abre una terminal y ejecuta:
    ```bash
    # Crear un nuevo entorno llamado 'atribus_informe' con Python 3.11
    conda create --name atribus_informe python=3.11 -y

    # Activar el entorno
    conda activate atribus_informe
    ```

3.  **Instalar Dependencias**:
    Con el entorno `atribus_informe` activado:
    ```bash
    pip install -r requirements.txt
    ```

4.  **Configurar Ollama**:
    -   Asegúrate de que Ollama esté instalado y ejecutándose. Por defecto, debería estar accesible en `http://127.0.0.1:11434`.
    -   Descarga el modelo LLM que deseas utilizar. Por ejemplo, para usar `granite3.2:latest`:
        ```bash
        ollama pull granite3.2:latest
        ```
        *Nota: Puedes usar cualquier otro modelo compatible con Ollama.*

5.  **Preparar Datos de Entrada**:
    -   Coloca tu archivo de tweets en formato JSON dentro del directorio `data/`. El script espera por defecto un archivo llamado `DATA_FILE`, pero puedes cambiarlo en `.env` si es necesario. Asegúrate de que cada tweet en el JSON tenga al menos las claves `text`, `sentiment`, `likes`, `retweets`, `replies`.

6.  **Configurar el Archivo `.env`**:
    -   Crea un archivo llamado `.env` en la raíz del proyecto.
    -   Copia y pega el siguiente contenido, ajustando los valores según sea necesario:

    ```dotenv
    # --- Configuración Obligatoria ---

    # URL de la API de Ollama (normalmente no necesita cambio)
    OLLAMA_API_URL=http://127.0.0.1:11434/api/generate

    # Nombre EXACTO del modelo LLM instalado en Ollama
    # Ejemplo: MODEL_NAME=gemma3:latest
    # Ejemplo: MODEL_NAME=mistral:7b
    MODEL_NAME=granite3.2:latest

    # --- Configuración de Archivos y Directorios ---

    # Ruta al archivo JSON de tweets (relativa a la raíz del proyecto)
    DATA_FILE=data/tweets.json

    # Nombre base para los archivos de salida (log, caché, informe)
    # El script añadirá el nombre del modelo y la extensión .log/.json/.md
    LOG_FILE_BASE=tweet_analysis

    # Directorios de salida (se crearán si no existen)
    LOGS_DIR=logs
    CACHE_DIR=categorized_tweets
    REPORTS_DIR=final_reports

    # --- Configuración de Extracción de Categorías ---

    # Número de tweets aleatorios a usar para extraer las categorías iniciales
    CATEGORY_SAMPLE_SIZE=200

    # Rango deseado para el número de categorías a generar por el LLM
    MIN_CATEGORIES=5
    MAX_CATEGORIES=8

    # --- Configuración de Procesamiento ---

    # Nivel de detalle para los logs (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    LOG_LEVEL=INFO

    # Tamaño del lote para procesar tweets (clasificación y estadísticas)
    # Ajusta según la memoria disponible y la velocidad deseada
    # - Valores más bajos (5-10): Menor uso de memoria, proceso más lento
    # - Valores más altos (20-50): Mayor uso de memoria, proceso más rápido
    BATCH_SIZE=10
    ```

## Uso

Una vez configurado todo, ejecuta el script principal desde la raíz del proyecto con tu entorno Conda activado:

```bash
conda activate atribus_informe
python main.py
```

**Traza de Ejecución (Ejemplo):**

Al ejecutar `python main.py`, el sistema realizará los siguientes pasos:

1.  **Inicialización**:
    -   Lee la configuración del archivo `.env`.
    -   Configura el logging para guardar mensajes en `logs/tweet_analysis_<nombre_modelo>.log`.
    -   Crea los directorios de salida (`logs`, `categorized_tweets`, `final_reports`) si no existen.
    -   Muestra un mensaje inicial indicando el modelo LLM y los archivos de entrada/salida que se usarán.

2.  **Carga de Datos**:
    -   Lee los tweets del archivo especificado en `DATA_FILE`.
    -   Muestra el número total de tweets cargados.

3.  **Extracción de Categorías**:
    -   Verifica si existe un archivo de caché de categorías/tweets (`CACHE_FILE`).
    -   **Si no hay caché**:
        -   Selecciona una muestra aleatoria de `CATEGORY_SAMPLE_SIZE` tweets.
        -   Envía un prompt al LLM (`MODEL_NAME`) pidiendo que identifique entre `MIN_CATEGORIES` y `MAX_CATEGORIES` categorías temáticas basadas en la muestra.
        -   Procesa la respuesta del LLM para extraer la lista de nombres de categorías.
        -   Si no se extraen suficientes categorías (menos de `MIN_CATEGORIES`), el proceso se detiene con un error.
    -   **Si hay caché**:
        -   Carga las categorías y los tweets ya clasificados directamente del archivo JSON de caché.
        -   Omite los pasos de extracción y clasificación.

4.  **Clasificación de Tweets (si no se usó caché)**:
    -   Itera sobre **todos** los tweets cargados.
    -   Para cada tweet, envía un prompt al LLM pidiéndole que asigne el tweet a una de las categorías extraídas previamente.
    -   Almacena el tweet junto con su categoría asignada.
    -   Muestra el progreso (si `tqdm` está instalado).

5.  **Guardado en Caché (si no se usó caché)**:
    -   Guarda la lista de categorías y todos los tweets con sus categorías asignadas en el archivo JSON de caché (`CACHE_FILE`). Esto acelera futuras ejecuciones con los mismos datos y modelo.

6.  **Cálculo de Estadísticas**:
    -   Agrupa los tweets por su categoría asignada.
    -   Para cada categoría, calcula:
        -   Número total de tweets.
        -   Distribución porcentual de sentimientos (Positivo, Negativo, Neutro, etc.).
        -   Engagement promedio (basado en likes, retweets, replies).

7.  **Generación del Informe**:
    -   Crea un archivo Markdown en `final_reports/tweet_analysis_<nombre_modelo>.md`.
    -   Escribe una introducción general.
    -   Para cada categoría:
        -   Escribe el nombre de la categoría.
        -   Muestra las estadísticas calculadas (total, sentimiento, engagement).
        -   (Opcional: Podría incluir ejemplos de tweets o resúmenes generados por IA si se implementara).
    -   Escribe una conclusión general.
    -   Muestra un mensaje indicando que el informe se ha generado correctamente y dónde encontrarlo.

8.  **Finalización**:
    -   El script termina.

## Estructura del Proyecto

```
atribus_informe/
├── .env                # Archivo de configuración (¡Crear manualmente!)
├── .gitignore          # Archivos ignorados por Git
├── README.md           # Este archivo
├── main.py             # Script principal que orquesta el flujo
├── requirements.txt    # Dependencias de Python
├── data/
│   └── tweets.json     # Archivo de entrada con los tweets (Ejemplo)
├── logs/               # Directorio para archivos de log (Creado por el script)
│   └── ...log
├── categorized_tweets/ # Directorio para caché de tweets categorizados (Creado por el script)
│   └── ...json
├── final_reports/      # Directorio para los informes finales en Markdown (Creado por el script)
│   └── ...md
└── src/                # Código fuente de los módulos
    ├── __init__.py
    ├── data_loader.py       # Carga datos de tweets
    ├── tweet_categorizer.py # Extracción de categorías y clasificación
    ├── stats_calculator.py  # Cálculo de estadísticas
    └── report_generator.py  # Generación del informe Markdown
```

## Solución de Problemas Comunes

-   **`FileNotFoundError`**: Verifica que la ruta en `TWEET_DATA_PATH` en `.env` sea correcta y que el archivo exista. Asegúrate de ejecutar `python main.py` desde la raíz del proyecto.
-   **Errores de Conexión con Ollama**: Asegúrate de que Ollama esté ejecutándose y sea accesible en la URL especificada en `OLLAMA_API_URL`. Verifica que el `MODEL_NAME` en `.env` esté correctamente escrito y que el modelo esté descargado (`ollama list`).
-   **Errores de `KeyError`**: Revisa que tu archivo JSON de tweets contenga las claves esperadas (`text`, `sentiment`, `likes`, `retweets`, `replies`).
-   **Proceso Lento**: La extracción de categorías y la clasificación pueden tardar, especialmente con muchos tweets o modelos LLM grandes. La caché ayuda en ejecuciones posteriores. Considera usar un `BATCH_SIZE` más pequeño si tienes problemas de memoria.
-   **Pocas Categorías Extraídas**: Si el LLM no genera suficientes categorías (menos de `MIN_CATEGORIES`), el script se detendrá. Puedes:
    -   Ajustar el prompt en `src/tweet_categorizer.py` (función `extract_categories_from_tweets`).
    -   Probar con un `CATEGORY_SAMPLE_SIZE` diferente en `.env`.
    -   Intentar con otro modelo LLM (`MODEL_NAME` en `.env`).
    -   Ajustar `MIN_CATEGORIES` en `.env` si el mínimo actual es demasiado alto para tu caso de uso.
