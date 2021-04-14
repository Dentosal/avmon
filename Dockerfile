FROM python:3.9

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt && touch avmon.cfg.toml
COPY avmon/ ./avmon

CMD [ "python", "-m", "avmon" ]