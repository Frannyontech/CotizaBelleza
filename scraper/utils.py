import json
import csv
import os
import random
import time
from datetime import datetime
from typing import List, Dict, Any
import logging
from .config import LOGGING_CONFIG, DELAY_CONFIG


def setup_logging(name: str = 'scraper') -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, LOGGING_CONFIG['level']))
    
    log_dir = 'logs'
    os.makedirs(log_dir, exist_ok=True)
    
    file_handler = logging.FileHandler(
        os.path.join(log_dir, LOGGING_CONFIG['file'])
    )
    file_handler.setLevel(logging.INFO)
    
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    
    formatter = logging.Formatter(LOGGING_CONFIG['format'])
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger


def random_delay(min_delay: float = None, max_delay: float = None) -> None:
    if min_delay is None:
        min_delay = DELAY_CONFIG['min_delay']
    if max_delay is None:
        max_delay = DELAY_CONFIG['max_delay']
    
    if DELAY_CONFIG['random_delay']:
        delay = random.uniform(min_delay, max_delay)
    else:
        delay = min_delay
    
    time.sleep(delay)


def clean_text(text: str) -> str:
    if not text:
        return ""
    
    text = ' '.join(text.split())
    
    text = text.replace('\xa0', ' ')
    text = text.replace('\u200b', '')
    
    return text.strip()


def extract_price(price_text: str) -> float:
    if not price_text:
        return 0.0
    
    price_text = clean_text(price_text)
    
    import re
    price_match = re.search(r'[\d,]+\.?\d*', price_text.replace(',', ''))
    
    if price_match:
        try:
            return float(price_match.group().replace(',', ''))
        except ValueError:
            return 0.0
    
    return 0.0


def extract_rating(rating_text: str) -> float:
    if not rating_text:
        return 0.0
    
    rating_text = clean_text(rating_text)
    
    import re
    rating_match = re.search(r'(\d+(?:\.\d+)?)', rating_text)
    
    if rating_match:
        try:
            rating = float(rating_match.group())
            return min(max(rating, 0.0), 5.0)
        except ValueError:
            return 0.0
    
    return 0.0


def save_to_json(data: List[Dict], filename: str) -> None:
    os.makedirs('output', exist_ok=True)
    filepath = os.path.join('output', filename)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"Datos guardados en: {filepath}")


def save_to_csv(data: List[Dict], filename: str) -> None:
    if not data:
        print("No hay datos para guardar")
        return
    
    os.makedirs('output', exist_ok=True)
    filepath = os.path.join('output', filename)
    
    fieldnames = list(data[0].keys())
    
    with open(filepath, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)
    
    print(f"Datos guardados en: {filepath}")


def generate_filename(prefix: str = "productos", extension: str = "json") -> str:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{prefix}_{timestamp}.{extension}"


def validate_url(url: str) -> bool:
    from urllib.parse import urlparse
    
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except Exception:
        return False


def chunk_list(lst: List, chunk_size: int) -> List[List]:
    return [lst[i:i + chunk_size] for i in range(0, len(lst), chunk_size)]


def print_progress(current: int, total: int, prefix: str = "Progreso") -> None:
    percentage = (current / total) * 100 if total > 0 else 0
    bar_length = 30
    filled_length = int(bar_length * current // total)
    bar = '█' * filled_length + '-' * (bar_length - filled_length)
    
    print(f'\r{prefix}: |{bar}| {percentage:.1f}% ({current}/{total})', end='')
    
    if current == total:
        print() 