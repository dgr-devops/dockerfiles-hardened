# Resultados medidos

Todo se mide con las imágenes construidas en local por `make compare` (Docker, Trivy y hadolint en
contenedores, `--scanners vuln`). El JSON bruto está en [resultados.json](resultados.json).
Columna "HIGH+CRITICAL con parche": hallazgos graves para los que la distribución ya publicó versión corregida.

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

## Lectura

- **Tamaño:** baja en los tres, sobre todo en Python y Node (imagen completa → slim/distroless).
- **Python y Node:** menos vulnerabilidades en todas las severidades y ninguna HIGH/CRITICAL con parche pendiente.
- **Java:** el `before` (`eclipse-temurin:21-jdk`, Ubuntu 26.04) tiene menos CVE que el `after`
  (distroless Debian 13): los HIGH del `after` son de `libexpat1` y `libuuid1` sin parche publicado en Debian.
  No se ha cambiado la base para maquillar el resultado: la ganancia en Java es de tamaño y de superficie
  (sin JDK, sin shell, sin root).
- **Los recuentos cambian** con la base de datos de Trivy y con las bases publicadas; no son una garantía.
- **hadolint** casi no puntúa en los `before`: comprueba la sintaxis y buenas prácticas del fichero,
  no que se corra como root ni que haya compiladores en la imagen. La mejora real se ve en Trivy y
  en la comprobación de usuario/solo lectura (`make smoke`).

## Comprobaciones en ejecución (imágenes `after`)

Con `docker run --read-only --tmpfs /tmp --cap-drop ALL --security-opt no-new-privileges`
las tres imágenes arrancan y el healthcheck pasa a `healthy`. Usuarios: Python 10001, Node y Java 65532 (nonroot).
