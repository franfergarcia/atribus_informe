#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Módulo para generar informes utilizando ollama.
"""

import os
from datetime import datetime
from dotenv import load_dotenv
import logging
from typing import Dict, List, Any
import requests
import time
import json

# Cargar variables de entorno
load_dotenv()

# Obtener variables desde .env (si existen)
OLLAMA_API_URL = os.getenv("OLLAMA_API_URL")
MODEL_NAME = os.getenv("MODEL_NAME")

logger = logging.getLogger(__name__)

def query_llm(prompt: str) -> str:
    """
    Consulta al modelo {MODEL_NAME} mediante la API de Ollama.
    
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
            "temperature": 0.7
        }
        
        response = requests.post(OLLAMA_API_URL, json=payload)
        response.raise_for_status()
        
        return response.json().get("response", "").strip()
        
    except requests.RequestException as e:
        logger.error(f"Error al consultar {MODEL_NAME}: {str(e)}")
        return "No se pudo generar el contenido debido a un error de conexión con el modelo."

def generate_category_introduction(category: str, stats: Dict[str, Any]) -> str:
    """
    Genera una introducción detallada para una categoría utilizando {MODEL_NAME}.
    
    Args:
        category (str): Nombre de la categoría.
        stats (Dict[str, Any]): Estadísticas de la categoría.
        
    Returns:
        str: Introducción generada.
    """
    # Obtener ejemplos representativos
    examples = []
    for i, tweet in enumerate(stats['most_engaging_tweets'][:3]):
        examples.append(f"Tweet {i+1}: {tweet['text']}")
    
    examples_text = "\n\n".join(examples)
    
    # Calcular porcentajes de sentimiento
    sentiment_text = []
    for sentiment, percentage in stats['sentiment_percentages'].items():
        sentiment_text.append(f"- {sentiment}: {percentage:.1f}%")
    
    sentiment_summary = "\n".join(sentiment_text)
    
    prompt = f"""Eres un experto analista de contenido en redes sociales y comunicación digital.

Escribe una introducción detallada y exhaustiva (sin límite de extensión) para la categoría temática "{category}".

DATOS SOBRE LA CATEGORÍA:
- Total de tweets: {stats['total_tweets']}
- Distribución de sentimiento:
{sentiment_summary}
- Engagement promedio: {stats['avg_engagement']}

EJEMPLOS REPRESENTATIVOS DE TWEETS EN ESTA CATEGORÍA:
{examples_text}

Tu introducción debe incluir:

1. CONTEXTO GENERAL:
   - Explicación detallada de qué trata esta categoría temática
   - Relevancia e importancia de este tema en el contexto actual
   - Principales actores o entidades involucradas

2. ANÁLISIS DE SENTIMIENTO:
   - Interpretación detallada de la distribución de sentimiento
   - Posibles razones para este patrón de sentimiento
   - Comparación con lo que cabría esperar en este tipo de temática

3. ANÁLISIS DE ENGAGEMENT:
   - Interpretación del nivel de engagement
   - Factores que podrían estar influyendo en el engagement
   - Tipos de contenido que generan mayor interacción

4. TENDENCIAS Y PATRONES:
   - Subtemas o narrativas principales dentro de esta categoría
   - Evolución temporal si es detectable
   - Conexiones con otros temas o categorías

Proporciona un análisis profundo y matizado. No escatimes en detalles y asegúrate de cubrir todos los aspectos relevantes.
El análisis debe ser objetivo y basado en los datos proporcionados.
"""
    
    introduction = query_llm(prompt)
    return introduction

def generate_category_conclusion(category: str, stats: Dict[str, Any]) -> str:
    """
    Genera una conclusión detallada para una categoría utilizando Gemma3.
    
    Args:
        category (str): Nombre de la categoría.
        stats (Dict[str, Any]): Estadísticas de la categoría.
        
    Returns:
        str: Conclusión generada.
    """
    # Obtener ejemplos representativos
    examples = []
    for i, tweet in enumerate(stats['most_engaging_tweets'][:3]):
        examples.append(f"Tweet {i+1}: {tweet['text']}")
    
    examples_text = "\n\n".join(examples)
    
    # Calcular porcentajes de sentimiento
    sentiment_text = []
    for sentiment, percentage in stats['sentiment_percentages'].items():
        sentiment_text.append(f"- {sentiment}: {percentage:.1f}%")
    
    sentiment_summary = "\n".join(sentiment_text)
    
    prompt = f"""Eres un experto analista de contenido en redes sociales y comunicación digital.

Escribe una conclusión detallada y exhaustiva (sin límite de extensión) para la categoría temática "{category}".

DATOS SOBRE LA CATEGORÍA:
- Total de tweets: {stats['total_tweets']}
- Distribución de sentimiento:
{sentiment_summary}
- Engagement promedio: {stats['avg_engagement']}

EJEMPLOS REPRESENTATIVOS DE TWEETS EN ESTA CATEGORÍA:
{examples_text}

Tu conclusión debe incluir:

1. HALLAZGOS PRINCIPALES:
   - Resumen de los patrones más significativos encontrados
   - Interpretación de la distribución de sentimiento
   - Análisis de los niveles de engagement

2. IMPLICACIONES:
   - Posibles consecuencias de estos patrones para los actores involucrados
   - Impacto potencial en la percepción pública
   - Oportunidades o desafíos que se presentan

3. RECOMENDACIONES:
   - Estrategias sugeridas para abordar los temas identificados
   - Acciones específicas que podrían mejorar la comunicación
   - Áreas que requieren mayor atención o seguimiento

4. TENDENCIAS FUTURAS:
   - Posible evolución de este tema en el corto y medio plazo
   - Factores que podrían influir en su desarrollo
   - Escenarios potenciales a considerar

Proporciona un análisis profundo y matizado. No escatimes en detalles y asegúrate de cubrir todos los aspectos relevantes.
El análisis debe ser objetivo y basado en los datos proporcionados.
"""
    
    conclusion = query_llm(prompt)
    return conclusion

def generate_final_summary(all_stats: Dict[str, Dict[str, Any]]) -> str:
    """
    Genera un resumen general detallado del informe utilizando Gemma3.
    
    Args:
        all_stats (Dict[str, Dict[str, Any]]): Estadísticas de todas las categorías.
        
    Returns:
        str: Resumen general generado.
    """
    # Preparar un resumen de datos para el prompt
    categories_summary = []
    
    for category, stats in all_stats.items():
        # Calcular porcentajes de sentimiento positivo, negativo y neutro
        pos_sentiment = stats['sentiment_percentages'].get('Positivo', 0) + stats['sentiment_percentages'].get('Muy positivo', 0)
        neg_sentiment = stats['sentiment_percentages'].get('Negativo', 0) + stats['sentiment_percentages'].get('Muy negativo', 0)
        neutral_sentiment = stats['sentiment_percentages'].get('Neutro', 0)
        
        # Obtener tweets representativos
        top_tweets = [t['text'][:100] + "..." for t in stats['most_engaging_tweets'][:2]]
        tweet_examples = "; ".join(top_tweets) if top_tweets else "No hay ejemplos disponibles"
        
        categories_summary.append(
            f"- {category}:\n"
            f"  * Total tweets: {stats['total_tweets']}\n"
            f"  * Sentimiento: {pos_sentiment:.1f}% positivo, {neg_sentiment:.1f}% negativo, {neutral_sentiment:.1f}% neutro\n"
            f"  * Engagement promedio: {stats['avg_engagement']}\n"
            f"  * Ejemplos destacados: {tweet_examples}"
        )
    
    categories_text = "\n\n".join(categories_summary)
    
    prompt = f"""Eres un experto analista de contenido en redes sociales y comunicación digital.
Elabora un análisis exhaustivo y detallado (sin límite de extensión) sobre los tweets analizados,
basándote en los datos proporcionados a continuación.

DATOS COMPLETOS POR CATEGORÍA:
{categories_text}

Tu análisis debe incluir:

1. CONTEXTO GENERAL:
   - Panorama general de los temas analizados
   - Principales tendencias identificadas
   - Clima de opinión pública en redes sociales

2. ANÁLISIS COMPARATIVO ENTRE CATEGORÍAS:
   - Diferencias significativas en el sentimiento entre categorías
   - Patrones de engagement y su significado
   - Categorías que generan mayor polarización
   - Categorías con mayor impacto en la percepción pública

3. TEMAS POLÉMICOS Y CONTROVERSIAS:
   - Identificación detallada de los temas más controvertidos
   - Análisis de las narrativas dominantes en estos temas
   - Actores principales involucrados y sus posiciones
   - Impacto potencial en la imagen pública

4. PERCEPCIÓN GENERAL:
   - Evaluación detallada de cómo se perciben los diferentes temas
   - Principales preocupaciones expresadas en los tweets
   - Diferencias de percepción entre distintos grupos (si es posible identificarlas)

5. TENDENCIAS EMERGENTES:
   - Temas emergentes que podrían ganar relevancia
   - Cambios en la percepción a lo largo del tiempo (si es detectable)
   - Posibles evoluciones futuras del discurso público

6. RECOMENDACIONES ESTRATÉGICAS:
   - Áreas donde la comunicación podría mejorarse
   - Temas que requieren atención especial
   - Oportunidades para mejorar la percepción pública

Proporciona un análisis profundo, basado en datos y matizado. No escatimes en detalles y asegúrate de cubrir todos los aspectos relevantes.
El análisis debe ser objetivo y equilibrado.
"""
    
    summary = query_llm(prompt)
    return summary

def generate_report(categorized_tweets: Dict[str, List[Dict[str, Any]]], category_stats: Dict[str, Dict[str, Any]]) -> str:
    """
    Genera el informe final completo.
    
    Args:
        categorized_tweets (Dict[str, List[Dict[str, Any]]]): Diccionario con tweets categorizados.
        category_stats (Dict[str, Dict[str, Any]]): Estadísticas por categoría.
        
    Returns:
        str: Informe completo en formato Markdown.
    """
    logger.info("Iniciando generación del informe")
    
    # Encabezado del informe
    current_date = datetime.now().strftime("%d/%m/%Y")
    report = f"""# Informe de Análisis de Tweets

"""
    
    # Generar secciones para cada categoría
    for category, tweets in categorized_tweets.items():
        logger.info(f"Generando sección para la categoría: {category}")
        stats = category_stats[category]
        
        # Generar introducción para la categoría
        introduction = generate_category_introduction(category, stats)
        
        # Crear sección de estadísticas
        stats_section = f"""### Estadísticas generales:

- **Total tweets analizados:** {stats['total_tweets']}

- **Distribución del sentimiento:**
"""
        
        # Añadir porcentajes de sentimiento
        for sentiment, percentage in stats['sentiment_percentages'].items():
            stats_section += f"  - {sentiment}: {percentage}%\n"
        
        stats_section += f"\n- **Engagement promedio:** {stats['avg_engagement']}\n\n"
        
        # Ejemplos significativos
        examples_section = "### Ejemplos significativos:\n\n"
        
        # Primero los tweets con mayor engagement
        examples_section += "**Tweets con mayor interacción:**\n\n"
        for tweet in stats['most_engaging_tweets'][:3]:  # Limitar a 3
            examples_section += f"- {format_tweet_for_report(tweet)}\n\n"
        
        # Luego los tweets con sentimiento extremo
        examples_section += "**Tweets con sentimiento destacado:**\n\n"
        for tweet in stats['extreme_sentiment_tweets'][:3]:  # Limitar a 3
            examples_section += f"- {format_tweet_for_report(tweet)}\n\n"
        
        # Generar conclusión para la categoría
        conclusion = generate_category_conclusion(category, stats)
        
        # Combinar todas las partes para esta categoría
        category_section = f"""## {category}

### Introducción/contexto detectado:
{introduction}

{stats_section}
{examples_section}
### Conclusión:
{conclusion}

---

"""
        
        # Añadir la sección de categoría al informe
        report += category_section
    
    # Generar resumen general del informe
    logger.info("Generando resumen general del informe")
    final_summary = generate_final_summary(category_stats)
    
    report += f"""## Resumen general del informe

{final_summary}

"""
    
    return report

def format_tweet_for_report(tweet: Dict[str, Any]) -> str:
    """
    Formatea un tweet para su inclusión en el informe.
    
    Args:
        tweet (Dict[str, Any]): Tweet a formatear.
        
    Returns:
        str: Tweet formateado.
    """
    # Mapear valor numérico de sentimiento a texto
    sentiment_map = {
        2: "Muy positivo",
        1: "Positivo",
        0: "Neutro",
        -1: "Negativo",
        -2: "Muy negativo"
    }
    
    sentiment_text = sentiment_map.get(tweet.get('sentiment', 0), "Desconocido")
    
    return f""""{tweet['text']}" (Usuario: {tweet['screen_name']}, Fecha: {tweet['datetime_created']}, Sentimiento: {sentiment_text})"""
