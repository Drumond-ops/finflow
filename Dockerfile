# Imagem da API FinFlow: Python 3.14 oficial + dependências do projeto.
# Assim a API roda igual em qualquer computador, independente do Python instalado na máquina.
FROM python:3.14-slim

# Não gera arquivos .pyc e mostra os logs na hora
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Instala as dependências primeiro: o Docker reaproveita esta etapa enquanto o requirements.txt não mudar
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia o código do projeto
COPY . .

EXPOSE 8000

# Modo desenvolvimento: recarrega sozinho quando um arquivo .py é salvo
CMD ["fastapi", "dev", "main.py", "--host", "0.0.0.0", "--port", "8000"]
