# AvMon - HTTP endpoint availability monitor

A microservice-based HTTP endpoint monitor using [Python](https://python.org/) for the actual code, [Apache Kafka](https://kafka.apache.org/) for combining multi-writer events into a single queue and [PostgreSQL](https://www.postgresql.org/) for long-term data storage.

## Project structure

* `avmon/` - Python packages
    * `collector.py` - Polls the sites and pushes the results to Kafka. Has own config, parallelizes well.
    * `backend.py` - Receives events from Kafka and writes them to a Postgres database.
    * `frontend.py` - Simple visualization frentend
* `tests/` - Integration / E2E tests