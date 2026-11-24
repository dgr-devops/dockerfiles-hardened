# Decisiones

## Umbral de Trivy en el CI

**Decisión:** el CI falla si Trivy encuentra vulnerabilidades `HIGH` o `CRITICAL` **que tengan
versión corregida disponible** (`--severity HIGH,CRITICAL --ignore-unfixed --exit-code 1`).

**Por qué.** Probé el umbral estricto (`HIGH,CRITICAL` sin `--ignore-unfixed`) y las imágenes
endurecidas no lo pasan: quedan hallazgos en paquetes de Debian (por ejemplo `util-linux`,
`libexpat1`, `libuuid1`) sin parche publicado. No dependen del Dockerfile y no se pueden
arreglar desde este repo; un CI que está siempre en rojo se acaba ignorando. Con
`--ignore-unfixed` el CI falla justo cuando **sí hay algo que hacer**: actualizar la base o una
dependencia. Los no corregidos siguen contados en la tabla (columna HIGH/CRITICAL) para no esconderlos.

**Coste.** Un CVE grave sin parche no rompe el CI. Es una aceptación consciente: se vigila en la tabla.

## Distroless en Node y Java, slim en Python

Distroless no incluye shell ni gestor de paquetes. En Node y Java la app no los necesita. Para
Python se usa `python:3.12-slim`: no hay distroless de Python al nivel de versión que quería
(3.12) y mantener un runtime Python a medida no compensa para este repo.

## Node 24 y distroless sobre Debian 13

La primera versión usaba Node 22 sobre distroless Debian 12. El escaneo encontró OpenSSL con
CRITICAL/HIGH corregibles porque esa base iba por detrás. Se pasó a Node 24 (LTS) y
`nodejs24-debian13`, que no los tiene. Para Java se usa `java21-debian13` por lo mismo.

## HEALTHCHECK

En distroless no hay shell ni curl, así que la comprobación es un script del propio runtime
(`healthcheck.js`, `healthcheck.py`) o un modo `--health` de la app Java. En Java cada comprobación
arranca una JVM; para un ejemplo es aceptable, en producción sería mejor usar la sonda del orquestador.

## Gunicorn en lugar del servidor de desarrollo de Flask

`app.run()` de Flask es un servidor de desarrollo. La imagen usa gunicorn con `--worker-tmp-dir /dev/shm`
para que funcione con el sistema de ficheros en solo lectura.

## Por qué no se reutiliza `docker-build-scan-push.yml`

El repo de workflows reutilizables construye, escanea y **publica en GHCR**. Aquí no se publican
imágenes (son ejemplos) y hace falta una matriz de tres lenguajes con prueba de arranque, así
que el CI es propio y corto. Se reutilizaría tal cual si algún día se publicaran las imágenes.

## Digests fijados

Los `FROM` llevan `@sha256` para que el build sea reproducible. Contrapartida: hay que
actualizarlos a mano (Dependabot o Renovate lo automatizan; no está configurado aquí).

## Lo que no se hace

- No se escanean secretos ni configuración en las imágenes (solo `--scanners vuln`).
- No se firman imágenes ni se genera SBOM.
- Las apps no tienen tests propios: son solo vehículo para los Dockerfile.
