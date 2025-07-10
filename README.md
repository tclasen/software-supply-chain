# Software Supply Chain

## Project Setup

This project uses `uv` for dependency management, you can install it here: [UV install instructions](https://docs.astral.sh/uv/getting-started/installation/)

The project also uses logfire for optional telemetry, you can safely disable this.

## Downloading PyPi Metadata

To download metadata from PyPi run the following script:

```shell
uv run src/software_supply_chain/download_pypi.py
```

## Run Web Server

To run the webserver and host the data that was downloaded run:

```shell
uv run uvicorn software_supply_chain.web:app
```

## Code Quality Checks

All code quality automation tooling is run using the included makefile. The main target you need for local development is the default so all you need to do is execute:

```shell
make
```
