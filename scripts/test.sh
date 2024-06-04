#!/bin/bash
poetry run pytest -s --tb=native --durations=5 --cov=fx_backtest --cov-report=html tests
poetry run coverage report --fail-under=0