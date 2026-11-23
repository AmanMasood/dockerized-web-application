.PHONY: up down logs test lint smoke

up:            ## Build and start the stack
	cp -n .env.example .env || true
	docker compose up -d --build

down:          ## Stop the stack (data volume is kept)
	docker compose down

logs:
	docker compose logs -f

test:          ## Run unit tests
	python -m pytest -q

lint:
	flake8 app tests --max-line-length 120

smoke:         ## Hit the running stack through Nginx
	./scripts/smoke_test.sh http://localhost:$${HTTP_PORT:-8080}
