FROM python:3.9

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY avmon/ ./avmon
COPY example.cfg.toml/ ./avmon.cfg.toml

CMD [ "python", "-m", "avmon" ]