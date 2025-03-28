#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Módulo para categorizar tweets utilizando el modelo Gemma3 (12b).
"""

import logging
import json
import requests
from typing import List, Dict, Any, Set, Tuple
from collections import defaultdict
import re
import os
from dotenv import load_dotenv
import random

# Cargar variables de entorno
load_dotenv()

# URL de la API de Ollama y Nombre del Modelo (cargados desde .env)
OLLAMA_API_URL = os.getenv("OLLAMA_API_URL")
MODEL_NAME = os.getenv("MODEL_NAME")

# Configuraciones de extracción de categorías desde .env
CATEGORY_SAMPLE_SIZE = int(os.getenv("CATEGORY_SAMPLE_SIZE", 200)) # Tamaño de muestra para extracción
MIN_CATEGORIES = int(os.getenv("MIN_CATEGORIES", 5))           # Mínimo de categorías a extraer
MAX_CATEGORIES = int(os.getenv("MAX_CATEGORIES", 8))           # Máximo de categorías a extraer

# Comprobar variables críticas
if not OLLAMA_API_URL or not MODEL_NAME:
    logger = logging.getLogger(__name__) 
    logger.error("Las variables OLLAMA_API_URL y MODEL_NAME deben estar definidas en el archivo .env")
    raise ValueError("Faltan variables críticas OLLAMA_API_URL o MODEL_NAME en .env")

# Configuración de logging para manejar caracteres Unicode
logger = logging.getLogger(__name__)

# Configurar el handler para evitar problemas con Unicode en Windows
for handler in logger.handlers + logging.getLogger().handlers:
    if isinstance(handler, logging.StreamHandler):
        try:
            handler.setStream(open(handler.stream.fileno(), mode='w', encoding='utf-8', buffering=1))
        except:
            pass  # Ignorar errores si el stream ya está en uso

def query_llm(prompt: str) -> str:
    """
    Consulta al modelo LLM configurado mediante la API de Ollama.
    
    Args:
        prompt (str): Prompt para el modelo.
        
    Returns:
        str: Respuesta del modelo.
    """
    try:
        payload = {
            "model": MODEL_NAME,
            "prompt": prompt,
            "stream": False,
            "temperature": 0.2
        }
        
        response = requests.post(OLLAMA_API_URL, json=payload)
        response.raise_for_status()
        
        return response.json().get("response", "").strip()
        
    except requests.RequestException as e:
        logger.error(f"Error al consultar {MODEL_NAME}: {str(e)}")
        return ""

def extract_categories_from_tweets(tweets: List[Dict[str, Any]], sample_size: int = CATEGORY_SAMPLE_SIZE) -> List[str]:
    """
    Extrae categorías temáticas de los tweets utilizando {MODEL_NAME}.
    
    Args:
        tweets (List[Dict[str, Any]]): Lista de tweets para extraer categorías.
        sample_size (int): Número de tweets a utilizar para la extracción (por defecto CATEGORY_SAMPLE_SIZE).
        
    Returns:
        List[str]: Lista de categorías extraídas.
    """
    # Asegurarse de que sample_size no sea mayor que el número total de tweets
    actual_sample_size = min(sample_size, len(tweets))
    
    # Tomar una muestra aleatoria representativa de tweets para el análisis
    if actual_sample_size < len(tweets):
        tweet_sample = random.sample(tweets, actual_sample_size)
    else:
        tweet_sample = tweets # Usar todos si sample_size >= len(tweets)
    
    # Crear un texto con los ejemplos de tweets
    tweet_texts = [t['text'] for t in tweet_sample]
    tweet_examples = "\n".join([f"Tweet {i+1}: {text}" for i, text in enumerate(tweet_texts)])
    
    # Prompt para extraer categorías
    prompt = f"""Analiza los siguientes tweets y extrae las principales categorías temáticas.

{tweet_examples}

Basándote en estos tweets, identifica entre {MIN_CATEGORIES} y {MAX_CATEGORIES} categorías temáticas principales que agrupen estos contenidos.
Para cada categoría, proporciona:
1. Un nombre claro y descriptivo
2. Una breve explicación de qué temas incluye esta categoría

Formato de respuesta:
Categoría 1: [Nombre de la categoría]
Descripción: [Breve descripción]

Categoría 2: [Nombre de la categoría]
Descripción: [Breve descripción]

Y así sucesivamente...

Las categorías deben ser mutuamente excluyentes en la medida de lo posible y cubrir todos los temas principales presentes en los tweets.
**IMPORTANTE**: Ten en cuenta que el campo category_id es siempre 71 porque se refiere a la ciudad de Valencia.
"""
    
    # Consultar a LLM
    response = query_llm(prompt)
    
    # Extraer las categorías de la respuesta
    categories = []
    category_pattern = r"Categoría \d+: (.*?)(?:\nDescripción:|$)"
    matches = re.findall(category_pattern, response, re.DOTALL)
    
    for match in matches:
        category = match.strip()
        if category:
            categories.append(category)
    
    # Si no se pudieron extraer categorías, devolver lista vacía
    if not categories:
        logger.warning("No se pudieron extraer categorías automáticamente.")
        return []
    
    # Validación adicional: ¿se generó un número razonable de categorías?
    if not (MIN_CATEGORIES <= len(categories) <= MAX_CATEGORIES + 2): # Permitir un margen por exceso
        logger.warning(f"Se extrajeron {len(categories)} categorías, fuera del rango esperado ({MIN_CATEGORIES}-{MAX_CATEGORIES}).")
        # Podríamos devolver [] aquí si queremos ser estrictos, o confiar en la asignación posterior
    
    logger.info(f"Se extrajeron {len(categories)} categorías: {categories}")
    return categories

def assign_tweet_to_category(tweet: Dict[str, Any], categories: List[str]) -> str:
    """
    Asigna un tweet a una categoría utilizando LLM.
    
    Args:
        tweet (Dict[str, Any]): Tweet a categorizar.
        categories (List[str]): Lista de categorías disponibles.
        
    Returns:
        str: Categoría asignada.
    """
    # Texto del tweet
    tweet_text = tweet['text']
    
    # Usar LLM para la asignación
    try:
        prompt = f"""Eres un experto en análisis de contenido en redes sociales y clasificación de textos.

A continuación te muestro un tweet y una lista de categorías temáticas.
Tu tarea es asignar el tweet a UNA SOLA categoría de la lista proporcionada.
Responde ÚNICAMENTE con el nombre exacto de la categoría que mejor se ajuste al contenido del tweet.

Tweet: "{tweet_text}"

Categorías disponibles:
{chr(10).join([f"- {cat}" for cat in categories])}

IMPORTANTE:
1. Responde SOLO con el nombre EXACTO de UNA categoría de la lista (copia y pega el nombre).
2. No añadas explicaciones ni texto adicional.
3. Si no estás seguro, elige la categoría que parezca más relevante.
4. Ten en cuenta que el campo category_id es siempre 71 porque se refiere a la ciudad de Valencia.
"""
        
        response = query_llm(prompt).strip()
        
        # Verificar si la respuesta es una categoría válida
        for category in categories:
            # Comparación flexible: eliminar espacios extra, asteriscos, etc.
            clean_category = re.sub(r'[*_]', '', category).strip()
            clean_response = re.sub(r'[*_]', '', response).strip()
            
            if clean_response.lower() == clean_category.lower() or clean_category.lower() in clean_response.lower():
                return category
        
        # Si la respuesta no coincide exactamente pero es similar a alguna categoría
        for category in categories:
            clean_category = re.sub(r'[*_]', '', category).strip().lower()
            if any(word.lower() in clean_category for word in response.split() if len(word) > 3):
                return category
        
        # Si aún no hay coincidencia, intentar con un prompt más directo
        prompt = f"""Elige EXACTAMENTE UNA categoría de la siguiente lista para clasificar este tweet:

Tweet: "{tweet_text}"

Categorías disponibles:
{chr(10).join([f"- {cat}" for cat in categories])}

IMPORTANTE: Responde ÚNICAMENTE con el nombre EXACTO de una categoría de la lista. Copia y pega el nombre tal cual aparece.
"""
        
        response = query_llm(prompt).strip()
        
        # Verificar nuevamente
        for category in categories:
            clean_category = re.sub(r'[*_]', '', category).strip()
            clean_response = re.sub(r'[*_]', '', response).strip()
            
            if clean_response.lower() == clean_category.lower() or clean_category.lower() in clean_response.lower():
                return category
        
        # Si aún no hay coincidencia, asignar a la categoría "Otros"
        if "Otros" not in categories:
            categories.append("Otros")
        return "Otros"
        
    except Exception as e:
        logger.error(f"Error al asignar categoría: {str(e)}")
        
        # En caso de error, asignar a una categoría por defecto
        default_category = categories[0] if categories else "Sin categoría"
        logger.warning(f"No se pudo asignar categoría al tweet: {tweet_text[:50]}...")
        return default_category

def categorize_tweets(tweets: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    """
    Categoriza todos los tweets extrayendo primero las categorías y luego asignando cada tweet.
    
    Args:
        tweets (List[Dict[str, Any]]): Lista de tweets a categorizar.
        
    Returns:
        Dict[str, List[Dict[str, Any]]]: Diccionario con tweets categorizados.
    """
    # Extraer categorías de los tweets
    logger.info(f"Extrayendo categorías de los tweets usando {MODEL_NAME}")
    categories = extract_categories_from_tweets(tweets)
    
    # Si no se pudieron extraer suficientes categorías (según MIN_CATEGORIES), no se puede continuar
    if len(categories) < MIN_CATEGORIES:
        logger.error(f"No se extrajeron suficientes categorías (mínimo {MIN_CATEGORIES}). No se puede continuar.")
        return {}
    
    logger.info(f"Categorías finales: {categories}")
    
    # Inicializar diccionario para almacenar tweets por categoría
    categorized = defaultdict(list)
    total = len(tweets)
    
    # Asignar cada tweet a una categoría
    for i, tweet in enumerate(tweets):
        try:
            logger.info(f"Categorizando tweet {i+1}/{total}")
            category = assign_tweet_to_category(tweet, categories)
            
            # Añadir el tweet a la categoría correspondiente
            tweet_with_category = tweet.copy()
            tweet_with_category['category'] = category
            categorized[category].append(tweet_with_category)
            
        except Exception as e:
            logger.error(f"Error al categorizar tweet {i+1}: {str(e)}")
            # Añadir a la primera categoría en caso de error
            tweet_with_category = tweet.copy()
            tweet_with_category['category'] = categories[0]
            categorized[categories[0]].append(tweet_with_category)
    
    # Verificar que todas las categorías tengan al menos un tweet
    for category in categories:
        if category not in categorized:
            logger.warning(f"La categoría '{category}' no tiene tweets asignados")
    
    return dict(categorized)

def save_categorization(categorized_tweets: Dict[str, List[Dict[str, Any]]], categories: List[str], filename: str = "categorized_tweets.json") -> None:
    """
    Guarda los tweets categorizados y las categorías en un archivo JSON.
    
    Args:
        categorized_tweets (Dict[str, List[Dict[str, Any]]]): Diccionario con tweets categorizados.
        categories (List[str]): Lista de categorías.
        filename (str): Nombre del archivo donde guardar los datos.
    """
    data = {
        "categories": categories,
        "categorized_tweets": categorized_tweets
    }
    
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        logger.info(f"Categorización guardada en {filename}")
        return True
    except Exception as e:
        logger.error(f"Error al guardar la categorización: {str(e)}")
        return False

def load_categorization(filename: str = "categorized_tweets.json") -> Tuple[Dict[str, List[Dict[str, Any]]], List[str]]:
    """
    Carga los tweets categorizados y las categorías desde un archivo JSON.
    
    Args:
        filename (str): Nombre del archivo desde donde cargar los datos.
        
    Returns:
        Tuple[Dict[str, List[Dict[str, Any]]], List[str]]: Tupla con tweets categorizados y categorías.
    """
    try:
        if not os.path.exists(filename):
            logger.warning(f"El archivo {filename} no existe")
            return None, None
            
        with open(filename, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        categorized_tweets = data.get("categorized_tweets", {})
        categories = data.get("categories", [])
        
        logger.info(f"Categorización cargada desde {filename}: {len(categories)} categorías, {sum(len(tweets) for tweets in categorized_tweets.values())} tweets")
        return categorized_tweets, categories
    except Exception as e:
        logger.error(f"Error al cargar la categorización: {str(e)}")
        return None, None
