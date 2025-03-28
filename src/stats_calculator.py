#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Módulo para calcular estadísticas generales de los tweets por categoría.
"""

import logging
from typing import Dict, List, Any
from collections import Counter

logger = logging.getLogger(__name__)

def calculate_statistics(categorized_tweets: Dict[str, List[Dict[str, Any]]]) -> Dict[str, Dict[str, Any]]:
    """
    Calcula estadísticas generales para cada categoría de tweets.
    
    Args:
        categorized_tweets (Dict[str, List[Dict[str, Any]]]): Diccionario con tweets categorizados.
        
    Returns:
        Dict[str, Dict[str, Any]]: Estadísticas por categoría.
    """
    statistics = {}
    
    for category, tweets in categorized_tweets.items():
        logger.info(f"Calculando estadísticas para la categoría: {category}")
        
        # Total de tweets
        total_tweets = len(tweets)
        
        # Distribución de sentimiento
        sentiment_counts = Counter()
        for tweet in tweets:
            sentiment_value = tweet.get('sentiment', 0)
            if sentiment_value == 2:
                sentiment_counts['Muy positivo'] += 1
            elif sentiment_value == 1:
                sentiment_counts['Positivo'] += 1
            elif sentiment_value == 0:
                sentiment_counts['Neutro'] += 1
            elif sentiment_value == -1:
                sentiment_counts['Negativo'] += 1
            elif sentiment_value == -2:
                sentiment_counts['Muy negativo'] += 1
            else:
                sentiment_counts['Desconocido'] += 1
        
        # Calcular porcentajes de sentimiento
        sentiment_percentages = {}
        for sentiment, count in sentiment_counts.items():
            percentage = (count / total_tweets) * 100 if total_tweets > 0 else 0
            sentiment_percentages[sentiment] = round(percentage, 2)
        
        # Calcular engagement promedio (retweets + favoritos)
        total_engagement = 0
        for tweet in tweets:
            retweets = tweet.get('count_retweet', 0)
            favorites = tweet.get('count_favorite', 0)
            total_engagement += retweets + favorites
        
        avg_engagement = total_engagement / total_tweets if total_tweets > 0 else 0
        
        # Seleccionar tweets con mayor interacción
        tweets_by_engagement = sorted(
            tweets, 
            key=lambda t: (t.get('count_retweet', 0) + t.get('count_favorite', 0)), 
            reverse=True
        )
        most_engaging_tweets = tweets_by_engagement[:5]  # Top 5
        
        # Seleccionar tweets con sentimiento extremo
        extreme_sentiment_tweets = [
            t for t in tweets 
            if t.get('sentiment', 0) in [-2, 2]
        ]
        
        # Si no hay suficientes tweets con sentimiento extremo, agregar negativos y positivos
        if len(extreme_sentiment_tweets) < 3:
            for t in tweets:
                if t.get('sentiment', 0) in [-1, 1] and t not in extreme_sentiment_tweets:
                    extreme_sentiment_tweets.append(t)
                if len(extreme_sentiment_tweets) >= 3:
                    break
        
        extreme_sentiment_tweets = extreme_sentiment_tweets[:3]  # Top 3
        
        # Guardar estadísticas de la categoría
        statistics[category] = {
            'total_tweets': total_tweets,
            'sentiment_percentages': sentiment_percentages,
            'avg_engagement': round(avg_engagement, 2),
            'most_engaging_tweets': most_engaging_tweets,
            'extreme_sentiment_tweets': extreme_sentiment_tweets
        }
    
    return statistics
