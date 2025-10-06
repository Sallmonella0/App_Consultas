# logger_config.py
import logging
import sys

def setup_logging():
    """Configura o sistema de logging para a aplicação."""
    
    # Define o formato da mensagem de log
    log_format = '%(asctime)s - %(levelname)s - %(module)s - %(message)s'
    
    # Configuração básica: Nível, formato e ficheiro de saída
    logging.basicConfig(
        level=logging.INFO,
        format=log_format,
        filename='app.log', # Nome do ficheiro de log
        filemode='w'      # 'w' para sobrescrever o log a cada execução, 'a' para adicionar
    )

    # Adiciona um handler para também imprimir os logs no terminal (consola)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(logging.Formatter(log_format))
    
    # Adiciona o handler de consola ao logger principal
    logging.getLogger().addHandler(console_handler)

    logging.info("Sistema de Logging inicializado.")