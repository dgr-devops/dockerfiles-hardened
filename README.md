# dockerfiles-hardened

[![CI](https://github.com/dgr-devops/dockerfiles-hardened/actions/workflows/ci.yml/badge.svg)](https://github.com/dgr-devops/dockerfiles-hardened/actions/workflows/ci.yml)
[![Licencia: MIT](https://img.shields.io/badge/licencia-MIT-blue.svg)](LICENSE)

Tres aplicaciones mínimas (Python, Node.js y Java) empaquetadas dos veces: una con un
`Dockerfile.before` ingenuo, como lo escribiría alguien que empieza, y otra con un `Dockerfile`
endurecido. Cada variante se mide con **Trivy** (vulnerabilidades) y **hadolint** (buenas prácticas)
y con el tamaño de la imagen, para que la mejora se vea en números reales y no se quede en
una promesa.

## Resultado

La tabla la genera `scripts/compare.py` a partir de las imágenes construidas en local; no se
edita a mano. Detalle y lectura honesta de los números en [docs/resultados.md](docs/resultados.md).

<!-- TABLA:INICIO -->
_Medido el 2026-11-24 con Trivy 0.76.2, base de vulnerabilidades del 2026-11-24._

| Lenguaje | Variante | Tamaño (MB) | CRITICAL | HIGH | MEDIUM | LOW | UNKNOWN | Total | HIGH+CRITICAL con parche | hadolint |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| python | before | 1623.8 | 16 | 526 | 1224 | 1454 | 587 | 3807 | 347 | 1 |
| python | after | 202.7 | 0 | 53 | 86 | 82 | 14 | 235 | 0 | 0 |
| node | before | 1632.7 | 20 | 488 | 1392 | 1486 | 575 | 3961 | 6 | 0 |
| node | after | 219.9 | 0 | 2 | 34 | 17 | 2 | 55 | 0 | 0 |
| java | before | 745.7 | 0 | 0 | 83 | 20 | 0 | 103 | 0 | 0 |
| java | after | 262.0 | 0 | 8 | 27 | 25 | 7 | 67 | 0 | 0 |

Reducción de tamaño (before → after):

- python: 1623.8 MB → 202.7 MB (88 % menos)
- node: 1632.7 MB → 219.9 MB (87 % menos)
- java: 745.7 MB → 262.0 MB (65 % menos)
<!-- TABLA:FIN -->

Lo que **no** dicen los números a simple vista:

- El número de CVE depende de la base de datos del día y de lo que publique cada distribución;
  una imagen "limpia" hoy puede tener hallazgos mañana. Por eso el CI mira solo los HIGH/CRITICAL
  **con parche disponible** (ver [docs/decisiones.md](docs/decisiones.md)).
- En Java la imagen `before` (Ubuntu 26.04, más reciente) sale con menos CVE que la `after`
  (distroless sobre Debian 13). La mejora ahí es de tamaño y de superficie de ataque
  (sin shell, sin JDK, sin root), no de recuento de CVE. Está explicado en `docs/resultados.md`.
- hadolint valora la sintaxis del Dockerfile, no la seguridad del conjunto: los `before` casi no
  tienen avisos aunque corran como root y con compiladores dentro.

## Estructura

```
python/  app.py, requirements.txt, healthcheck.py, Dockerfile.before, Dockerfile, .dockerignore
node/    server.js, package.json, package-lock.json, healthcheck.js, Dockerfile.before, Dockerfile
java/    src/App.java, Dockerfile.before, Dockerfile
scripts/compare.py     regenera la tabla (README y docs/resultados.md)
Makefile               build, lint, scan, smoke, compare
.github/workflows/ci.yml
docs/                  resultados.md, decisiones.md
```

## Uso

Requisitos: Docker y `make`. Trivy y hadolint se ejecutan en contenedores, no hay que instalarlos.

```bash
make build         # construye las imágenes endurecidas (dh-<lang>:after)
make build-before  # construye las ingenuas (dh-<lang>:before)
make lint          # hadolint (falla con avisos en los Dockerfile endurecidos)
make scan          # Trivy: falla con HIGH/CRITICAL que tengan parche
make smoke         # arranca las imágenes en solo lectura y comprueba el healthcheck
make compare       # reconstruye todo, mide y regenera la tabla
```

## Medidas de endurecimiento y por qué

| Medida | Qué hace | Por qué |
|---|---|---|
| Multi-stage | Compila/instala en una etapa y copia solo el resultado | pip, npm, el JDK y los compiladores no llegan a producción: menos tamaño y menos código atacable |
| Base mínima | `python:3.12-slim`; distroless en Node y Java | Menos paquetes, menos CVE y, en distroless, sin shell ni gestor de paquetes que un atacante pueda usar |
| Versiones y digest fijados | `imagen:tag@sha256:...` | Builds reproducibles: la base no cambia sin que se vea en un commit |
| Usuario sin privilegios | UID numérico (10001 / 65532) | Si la app se compromete, no es root dentro del contenedor; el UID numérico lo entiende Kubernetes (`runAsNonRoot`) |
| Dependencias bloqueadas | `requirements.txt` con versiones exactas; `package-lock.json` + `npm ci --omit=dev --ignore-scripts` | Instalación determinista, sin dependencias de desarrollo y sin ejecutar scripts de instalación de terceros |
| Sin caché ni basura | `PIP_NO_CACHE_DIR`, `npm cache clean`, `.dockerignore` | Capas más pequeñas y sin `.git`, `.env` ni ficheros locales dentro de la imagen |
| `HEALTHCHECK` sin curl | Script propio en Python/Node; `--health` en la app Java | La imagen final no lleva curl ni shell; el orquestador puede saber si la app responde |
| Compatible con solo lectura | Las apps no escriben en disco (`--read-only --tmpfs /tmp`); gunicorn usa `/dev/shm` | Un atacante no puede modificar binarios ni dejar ficheros; se prueba en `make smoke` y en CI |
| Sin secretos en capas | Nada de `ENV`/`ARG` con credenciales; `.dockerignore` excluye `.env*` | Lo que entra en una capa se queda en el historial de la imagen |
| Formato exec en `CMD` | `CMD ["gunicorn", ...]` | La app recibe las señales (SIGTERM) y el contenedor se apaga limpio |

## Verificación

Ejecutado de verdad (2026-11-24, Docker en local y GitHub Actions):

- `make build build-before`: las seis imágenes se construyen.
- `make lint` (hadolint por contenedor): sin avisos en los tres `Dockerfile` endurecidos.
- `make scan` (Trivy `--ignore-unfixed --severity HIGH,CRITICAL`): pasa en las tres imágenes endurecidas.
- `make smoke`: las tres imágenes arrancan con `--read-only --cap-drop ALL --security-opt no-new-privileges`
  y el healthcheck llega a `healthy`.
- `make compare`: regenera la tabla de arriba con Trivy 0.76.2 y su base de datos del mismo día.
- CI en GitHub Actions en verde: job de hadolint y tres jobs `build + trivy` (python, node, java).

No verificado: otras arquitecturas (solo `linux/amd64`), ejecución con Kubernetes y comportamiento
con base de datos de Trivy de otros días (los recuentos cambian).

## Licencia

[MIT](LICENSE) © 2026 Daniel García Rodríguez
