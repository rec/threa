#!/bin/bash

set -eux

isort threa test
black threa
ruff check --fix threa
mypy threa
pytest
