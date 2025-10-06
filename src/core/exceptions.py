# src/core/exceptions.py

class ConsultaAPIException(Exception):
    """Exceção base para erros de comunicação com a API."""
    pass

class APIConnectionError(ConsultaAPIException):
    """Erro de conexão ou timeout."""
    def __init__(self, message="Falha ao conectar ou timeout com a API."):
        super().__init__(message)

class APIAuthError(ConsultaAPIException):
    """Erro de autenticação (401)."""
    def __init__(self, message="Autenticação falhou. Verifique as credenciais."):
        super().__init__(message)

class APIClientError(ConsultaAPIException):
    """Erros do cliente (4xx, exceto 401)."""
    def __init__(self, status_code, message):
        super().__init__(f"Erro do Cliente ({status_code}): {message}")

class APIServerError(ConsultaAPIException):
    """Erro do servidor (5xx)."""
    def __init__(self, status_code, message):
        super().__init__(f"Erro do Servidor ({status_code}): {message}")

class APIResponseError(ConsultaAPIException):
    """Erro na resposta da API (JSON inválido ou estrutura inesperada)."""
    def __init__(self, message="Resposta da API inválida ou inesperada."):
        super().__init__(message)