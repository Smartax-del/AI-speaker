import logging
import socket

def check_internet(timeout=3):
    hosts_to_try = [
        ("8.8.8.8", 53),      # Google DNS
        ("1.1.1.1", 53),      # Cloudflare DNS
        ("api.openai.com", 443),  # сам API, который мы используем
    ]

    for host, port in hosts_to_try:
        try:
            socket.setdefaulttimeout(timeout)
            socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect((host, port))
            return True
        except OSError:
            continue

    return False

def setup_logger():
    logger = logging.getLogger("ai_speaker")
    logger.setLevel(logging.INFO)
    if not logger.handlers:
        file_handler = logging.FileHandler("speaker.log", encoding="utf-8")
        file_handler.setFormatter(logging.Formatter("%(asctime)s %(message)s", datefmt="%Y-%m-%d %H:%M:%S"))
        logger.addHandler(file_handler)
    return logger