#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Módulo para cargar los datos de tweets desde el archivo JSON.
"""

import json
import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

def load_tweets(file_path: str) -> List[Dict[str, Any]]:
    """
    Carga los tweets desde un archivo JSON.
    
    Args:
        file_path (str): Ruta al archivo JSON con los tweets.
        
    Returns:
        List[Dict[str, Any]]: Lista de tweets como diccionarios.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            tweets = json.load(f)
        
        # Verificar que los tweets contienen los campos esperados
        required_fields = [
            'text', 'datetime_created', 'county', 'country', 
            'count_retweet', 'count_favorite', 'sentiment', 
            'screen_name', 'description', 'gender', 
            'count_follow', 'count_follower', 'age'
        ]
        
        # Filtrar tweets que no tengan los campos requeridos
        valid_tweets = []
        for tweet in tweets:
            if all(field in tweet for field in required_fields):
                valid_tweets.append(tweet)
            else:
                missing_fields = [field for field in required_fields if field not in tweet]
                logger.warning(f"Tweet omitido por faltar campos: {missing_fields}")
        
        if len(valid_tweets) < len(tweets):
            logger.warning(f"Se omitieron {len(tweets) - len(valid_tweets)} tweets por datos incompletos")
            
        return valid_tweets
    
    except FileNotFoundError:
        logger.error(f"El archivo {file_path} no existe.")
        raise
    except json.JSONDecodeError:
        logger.error(f"Error al decodificar el JSON en {file_path}.")
        raise
    except Exception as e:
        logger.error(f"Error inesperado al cargar tweets: {str(e)}")
        raise
