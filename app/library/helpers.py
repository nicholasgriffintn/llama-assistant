import os.path
import markdown
import requests
import logging
import re
import string

from .config import ollama_host

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def openfile(filename):
    """
    Open a file and return its contents as HTML.

    Args:
        filename (str): The name of the file to open.

    Returns:
        dict: The contents of the file as HTML, or an error message.
    """

    filepath = os.path.join("app/pages/", filename)
    
    try:
        with open(filepath, "r", encoding="utf-8") as input_file:
            text = input_file.read()
    except FileNotFoundError:
        logger.error(f"File not found: {filepath}")
        return {"error": "File not found"}
    except IOError as e:
        logger.error(f"Error reading file {filepath}: {e}")
        return {"error": "Error reading file"}

    html = markdown.markdown(text)
    return {"text": html}

def generate(prompt, options, model_name):
    """
    Generate text using the Ollama API.

    Args:
        prompt (str): The prompt to generate text from.
        options (dict): The options to use for generation.
        model_name (str): The model to use for generation.

    Returns:
        str: The generated text.
    """

    url = f"{ollama_host}/api/generate"
    payload = {
        "prompt": prompt,
        "model": model_name,
        "stream": False,
        "options": options
    }
    
    try:
        response = requests.post(url, json=payload, timeout=120)
        response.raise_for_status()  # Raise an HTTPError for bad responses
        return response.json().get("response")
    except requests.exceptions.Timeout:
        logger.error("Request timed out")
    except requests.exceptions.RequestException as e:
        logger.error(f"Request failed: {e}")
    return None

def check_summary(summary, article):
    """
    Check if the summary quotes are sufficiently represented in the article.

    Args:
        summary (str): The summary containing quotes.
        article (str): The article to check against.

    Returns:
        bool: True if all quotes in the summary are sufficiently represented in the article, False otherwise.
    """
    
    # Find quotes in the summary
    matches = re.findall(r'"(.*?)"', summary)
    article = article.lower()

    for match in matches:
        match = match.lower()
        parts = match.split("...")
        for part in parts:
            words = part.split()
            valid_words = sum(1 for word in words if word.strip(string.punctuation) in article)
            pc_valid = valid_words / len(words)
            logger.info(f"pc_valid: {pc_valid}")
            if pc_valid < 0.8:
                return False
    return True
