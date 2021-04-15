# AvMon - HTTP endpoint availability monitor

A microservice-based HTTP endpoint monitor using [Python](https://python.org/) for the actual code, [Apache Kafka](https://kafka.apache.org/) for combining multi-writer events into a single queue and [PostgreSQL](https://www.postgresql.org/) for long-term data storage.

![Architecture diagram](docs/architecture.svg)

The project is dockerized using a single container, which is switched to perform different functions with the `AVMON_ROLE` environment variable. Collector components are configured using a mounted config file.

## Running

A minimal local system (one of each component) can be started with:

```bash
make create-dotenv docker-up
```

or even smaller system without dockerizing the application itself, running all Python services in a single process (requires Python >= 3.8):

```bash
make create-dotenv install-deps docker-dbs run-all
```

In either case, navigate to https://localhost:8080/ for the visualization. Then proceed to tweak the [configuration file](avmon.cfg.toml) to include sites you would like to monitor.

### Using external databases

If you are going to use external non-dockerized database, such as a cloud-hosted one, then the authentication must be configured using either a `.env` file or actual environment variables:

```
POSTGRES_HOST=host.example.org
POSTGRES_PORT=5432
POSTGRES_USER=avmon
POSTGRES_PASSWORD=PASSWORD_HERE
POSTGRES_DB=avmon

AVMON_KAFKA=host.example.org:9092
AVMON_KAFKA_SSL=1
```

Moreover, with `AVMON_KAFKA_SSL=1` you must pass the actual SSL keys and certificates. They should be placed in a folder named `keys` and the filenames should be `access-key`, `access-cert`, `ca-cert`.

Remote databases must also be set up properly. Usually that means at least that PostgreSQL user and database must be created. Kafka should require no special setup, but make sure that it is configured to automatically create topics (`kafka.auto_create_topics_enable=1`) or manually create a topic called `messages`.


## Project structure

Most important project files are:

* [`avmon/`](avmon/) - Python modules
    * [`collector.py`](avmon/collector.py) - Polls the sites and pushes the results to Kafka. Has own config, parallelizes well.
    * [`backend.py`](avmon/backend.py) - Receives events from Kafka and writes them to a Postgres database.
    * [`frontend.py`](avmon/frontend.py) - Simple visualization frentend
    * [`frontend.html`](avmon/frontend.html) - Frontend HTML template
* [`tests/`](tests/) - Integration / E2E tests
* [`requirements.txt`](requirements.txt) - Runtime Python package dependencies
* [`requirements-dev.txt`](requirements-dev.txt) - Development Python package dependencies
* [`docker-compose.yml`](docker-compose.yml) - Docker-compose-file for running the project normally
* [`docker-compose-dbs.yml`](docker-compose-dbs.yml) - Docker-compose-file for running only the databases in Docker
* [`Dockerfile`](Dockerfile) - Dockerfile to containerize this project
* [`Makefile`](Makefile) - Convenient shortcut commands
* [`avmon.cfg.toml`](avmon.cfg.toml) - Example configuration file
* [`docs/`](docs/) - Auxiliary documentation files

## Development

Requireds Python (>= 3.8), and Docker + Docker-compose. Most of the commands are rather \*nix-specific, so Linux or macOS is recommended.

### Setup

```bash
make dev-setup
```

Installs the dev dependencies locally. It also creates git hooks that make sure you will not commit unformatted code or push untested code.

### Formatter

The project uses [Black](https://github.com/psf/black) for code formatting to ensure uniform style. To automatically format code, run `make format`.

### Type checking

[Mypy](http://mypy-lang.org/) is used for type checking. To make sure you have not introduced type errors, run `make type-check`.

### Tests

`make test` runs the whole test suite, which takes quite some time. Use `python -m pytest -k testname` to run one test at a time. `python -m pytest -s` can be used to see test output while the test is still running. Please note that the E2E tests use docker-compose to manage environment and cannot be ran if the system is already running.

## License

MIT
