# AvMon - HTTP endpoint availability monitor

A microservice-based HTTP endpoint monitor using [Python](https://python.org/) for the actual code, [Apache Kafka](https://kafka.apache.org/) for combining multi-writer events into a single queue and [PostgreSQL](https://www.postgresql.org/) for long-term data storage.

![Architecture diagram](docs/architecture.svg)

Project is dockerized using single container, switched to perform different functions with the `AVMON_ROLE` environment variable.

## Running

Minimal local system (one of each component) can be started with:

```bash
docker-compose up
```

or even smaller system without dockerizing the application itself, running all Python services in a single process:

```bash
make install-deps docker-dbs run-all
```

In either case, navigate to https://localhost:8080/ for the visualization.

## Project structure

* `avmon/` - Python packages
    * `collector.py` - Polls the sites and pushes the results to Kafka. Has own config, parallelizes well.
    * `backend.py` - Receives events from Kafka and writes them to a Postgres database.
    * `frontend.py` - Simple visualization frentend
* `tests/` - Integration / E2E tests
* `docker-compose.yml` - Docker-compose-file for running the project normally
* `docker-compose-dbs.yml` - Docker-compose-file for running only the databases in Docker
* `Dockerfile` - Dockerfile to containerize
* `Makefile` - Convenient shortcut commands

## Development

Required: Python (>= 3.8), and Docker + Docker-compose

To start, run

```bash
make dev-setup
```

this installs the dev dependencies locally, and installs git hooks that make sure you will not commit unformatted code or push untested code.
