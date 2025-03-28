#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Asistente automático generador de informes sobre tweets mediante Ollama.
Este script orquesta el proceso completo de análisis de tweets y generación de informes.
"""

import json
import logging
import os
from datetime import datetime
import sys
from dotenv import load_dotenv

# Ajustar sys.path para importar desde src
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from data_loader import load_tweets
from tweet_categorizer import categorize_tweets, load_categorization, save_categorization
from stats_calculator import calculate_statistics
from report_generator import generate_report

# Directorios de salida (asegúrate de que existan)
LOGS_DIR = os.getenv("LOGS_DIR")
CACHE_DIR = os.getenv("CACHE_DIR")
REPORTS_DIR = os.getenv("REPORTS_DIR")

# Crear directorios si no existen
os.makedirs(LOGS_DIR, exist_ok=True)
os.makedirs(CACHE_DIR, exist_ok=True)
os.makedirs(REPORTS_DIR, exist_ok=True)

# Cargar variables de entorno
load_dotenv()

# Obtener variables desde .env
DATA_FILE = os.getenv("DATA_FILE")
CACHE_FILE_BASE = os.getenv("CACHE_FILE") # Base name without extension
LOG_FILE_BASE = os.getenv("LOG_FILE") # Base name without extension
LOG_LEVEL = os.getenv("LOG_LEVEL").upper()
MODEL_NAME = os.getenv("MODEL_NAME")

# Sanitizar MODEL_NAME para usar en nombres de archivo (reemplazar ':' y '/')
model_name_sanitized = MODEL_NAME.replace(":", "-").replace("/", "-")

# Construir nombres de archivo finales con directorios
CACHE_FILE = os.path.join(CACHE_DIR, f"{CACHE_FILE_BASE}_{model_name_sanitized}.json")
LOG_FILE = os.path.join(LOGS_DIR, f"{LOG_FILE_BASE}_{model_name_sanitized}.log")

# Configuración de logging
log_level_numeric = getattr(logging, LOG_LEVEL, logging.INFO)
logging.basicConfig(
    level=log_level_numeric,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE, encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def main():
    """
    Función principal que ejecuta el flujo completo del análisis de tweets
    y generación de informes.
    """
    start_time = datetime.now()
    logger.info("Iniciando análisis de tweets")
    logger.info(f"Usando archivo de datos: {DATA_FILE}")
    logger.info(f"Usando archivo de caché: {CACHE_FILE}")

    # 1. Cargar los tweets desde el archivo JSON especificado en .env
    logger.info(f"Cargando tweets desde {DATA_FILE}")
    tweets = load_tweets(DATA_FILE)
    if not tweets:
        logger.error(f"No se pudieron cargar tweets desde {DATA_FILE}. Abortando.")
        return None
    logger.info(f"Se han cargado {len(tweets)} tweets correctamente")

    # 2. Intentar cargar la categorización previa desde el archivo especificado en .env
    categorized_tweets = None
    categories = None
    cache_file_path = CACHE_FILE

    if os.path.exists(cache_file_path):
        logger.info(f"Intentando cargar categorización previa desde {cache_file_path}")
        categorized_tweets, categories = load_categorization(cache_file_path)

    # 3. Si no hay categorización previa, categorizar los tweets
    if categorized_tweets is None:
        logger.info("Categorizando tweets")
        categorized_tweets = categorize_tweets(tweets)

        # Extraer las categorías del diccionario de tweets categorizados
        categories = list(categorized_tweets.keys())

        # Guardar la categorización para uso futuro en el archivo especificado en .env
        logger.info(f"Guardando categorización para uso futuro en {cache_file_path}")
        save_categorization(categorized_tweets, categories, cache_file_path)
    else:
        logger.info(f"Usando categorización previa de {cache_file_path} con {len(categories)} categorías")

    # Verificar si la categorización produjo resultados
    if not categorized_tweets or not categories:
        logger.error("La categorización no produjo resultados válidos. Abortando.")
        return None

    # 4. Calcular estadísticas para cada categoría
    logger.info("Calculando estadísticas por categoría")
    category_stats = calculate_statistics(categorized_tweets)

    # 5. Generar informe final
    logger.info("Generando informe")
    report = generate_report(categorized_tweets, category_stats)

    # 6. Guardar el informe
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_filename_base = f"informe_{timestamp}_{model_name_sanitized}.md"
    report_filename = os.path.join(REPORTS_DIR, report_filename_base)
    try:
        with open(report_filename, "w", encoding="utf-8") as f:
            f.write(report)
        logger.info(f"Informe generado y guardado como {report_filename}")
    except IOError as e:
        logger.error(f"No se pudo guardar el informe en {report_filename}. Error: {e}")
        return None

    logger.info(f"Tiempo total de ejecución: {datetime.now() - start_time}")

    return report_filename

if __name__ == "__main__":
    try:
        output_file = main()
        if output_file:
            print(f"\nAnálisis completado con éxito. El informe se ha guardado en: {output_file}")
        else:
            print("\nEl análisis no se completó correctamente. Revisa el archivo de log para más detalles.")
    except Exception as e:
        logger.error(f"Error fatal durante la ejecución: {str(e)}", exc_info=True)
        print(f"\nError fatal durante la ejecución: {str(e)}")
