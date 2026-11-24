LANGS := python node java
# Falla si hay HIGH/CRITICAL con parche disponible (ver docs/decisiones.md)
TRIVY_FAIL := --severity HIGH,CRITICAL --ignore-unfixed --exit-code 1
TRIVY := docker run --rm -v /var/run/docker.sock:/var/run/docker.sock -v trivy-cache:/root/.cache aquasec/trivy:latest
HADOLINT := docker run --rm -i hadolint/hadolint hadolint

.PHONY: help build build-before lint smoke scan scan-all compare clean

help: ## Muestra esta ayuda
	@grep -E '^[a-z-]+:.*##' $(MAKEFILE_LIST) | awk -F':.*## ' '{printf "  %-14s %s\n", $$1, $$2}'

build: ## Construye las imágenes endurecidas (dh-<lang>:after)
	@for l in $(LANGS); do docker build -t dh-$$l:after $$l || exit 1; done

build-before: ## Construye las imágenes ingenuas (dh-<lang>:before)
	@for l in $(LANGS); do docker build -f $$l/Dockerfile.before -t dh-$$l:before $$l || exit 1; done

lint: ## hadolint: falla con avisos en los Dockerfile endurecidos; informativo en los before
	@for l in $(LANGS); do echo "== $$l/Dockerfile"; \
	  $(HADOLINT) --failure-threshold warning - < $$l/Dockerfile || exit 1; done
	@for l in $(LANGS); do echo "== $$l/Dockerfile.before (informativo)"; \
	  $(HADOLINT) - < $$l/Dockerfile.before; done; true

smoke: ## Arranca cada imagen endurecida (solo lectura, sin capacidades) y comprueba el healthcheck
	@for l in $(LANGS); do docker rm -f smoke-$$l >/dev/null 2>&1; \
	  docker run -d --name smoke-$$l --read-only --tmpfs /tmp --cap-drop ALL \
	    --security-opt no-new-privileges dh-$$l:after >/dev/null || exit 1; done
	@echo "Esperando al primer healthcheck..."; sleep 40
	@rc=0; for l in $(LANGS); do st=$$(docker inspect -f '{{.State.Health.Status}}' smoke-$$l); \
	  echo "$$l: $$st"; [ "$$st" = healthy ] || rc=1; done; \
	  for l in $(LANGS); do docker rm -f smoke-$$l >/dev/null; done; exit $$rc

scan: ## Trivy sobre las imágenes endurecidas; falla con HIGH/CRITICAL con parche
	@for l in $(LANGS); do echo "== dh-$$l:after"; \
	  $(TRIVY) image --scanners vuln $(TRIVY_FAIL) dh-$$l:after || exit 1; done

scan-all: ## Trivy informativo (sin fallar) sobre before y after
	@for l in $(LANGS); do for v in before after; do echo "== dh-$$l:$$v"; \
	  $(TRIVY) image --scanners vuln --severity HIGH,CRITICAL dh-$$l:$$v | tail -n 8; done; done

compare: build build-before ## Reconstruye, mide y regenera README.md y docs/resultados.md
	python3 scripts/compare.py --write

clean: ## Borra las imágenes locales dh-*
	-docker rmi $$(docker images -q 'dh-*') 2>/dev/null
