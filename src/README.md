# Aplicação de Consulta à API

Esta é uma aplicação de desktop desenvolvida em Python com CustomTkinter para consultar, filtrar e exportar dados de uma API.

## Funcionalidades

- Consulta de dados por IDMENSAGEM e busca de todos os registos.
- Tabela com paginação para lidar com grandes volumes de dados.
- Filtro dinâmico por coluna e ordenação por data.
- Exportação de dados para os formatos CSV e Excel.
- Sistema de cache local para uma inicialização mais rápida.
- Temas claro e escuro.

## Instalação

1.  Clone o repositório:
    ```bash
    git clone [URL_DO_SEU_REPOSITORIO]
    cd app_consultas
    ```

2.  (Recomendado) Crie e ative um ambiente virtual:
    ```bash
    python -m venv venv
    source venv/bin/activate  # No Windows: venv\Scripts\activate
    ```

3.  Instale as dependências:
    ```bash
    pip install -r requirements.txt
    ```

## Como Executar

Para iniciar a aplicação, execute o ficheiro `main.py` a partir da pasta `src`:
```bash
python src/main.py