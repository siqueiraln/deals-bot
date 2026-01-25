import logging
import os
from datetime import datetime

def setup_logging(log_dir="logs"):
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    log_file = os.path.join(log_dir, f"bot_{datetime.now().strftime('%Y%m%d')}.log")

    from logging.handlers import TimedRotatingFileHandler
    
    # Rotação de logs: troca todo dia à meia noite, mantém últimos 7 dias
    file_handler = TimedRotatingFileHandler(log_file, when="midnight", interval=1, backupCount=7, encoding='utf-8')

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(message)s',
        handlers=[
            file_handler,
            logging.StreamHandler()
        ]
    )
    return logging.getLogger("DealsBot")

logger = setup_logging()
