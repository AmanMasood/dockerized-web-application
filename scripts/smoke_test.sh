#!/usr/bin/env bash
# Smoke test a running deployment: health, create, list, persistence.
set -euo pipefail

BASE_URL="${1:-http://localhost:8080}"
echo "Smoke testing ${BASE_URL}"

for i in $(seq 1 30); do
  if curl -fsS "${BASE_URL}/health" >/dev/null; then break; fi
  echo "waiting for app... (${i})"; sleep 2
done

curl -fsS "${BASE_URL}/health" | grep -q '"status":"ok"'
echo "health OK"

curl -fsS -X POST -H 'Content-Type: application/json' \
  -d '{"title":"smoke test task"}' "${BASE_URL}/api/tasks" | grep -q 'smoke test task'
echo "create OK"

curl -fsS "${BASE_URL}/api/tasks" | grep -q 'smoke test task'
echo "list OK"

curl -fsS "${BASE_URL}/nginx-health" | grep -q ok
echo "nginx OK"
echo "All smoke tests passed."
