#!/bin/bash
set -e

# Wrapper for dedicated dev compose file.
docker compose -f docker-compose.yml -f docker-compose.dev.yml "$@"
