#!/usr/bin/env python3
"""Regenera la tabla comparativa antes/después (tamaño, Trivy y hadolint).

Requiere Docker y las imágenes ``dh-<lenguaje>:before|after`` ya construidas
(``make build build-before``). Trivy y hadolint se ejecutan en contenedores.

Uso:
    scripts/compare.py            # imprime las tablas por stdout
    scripts/compare.py --write    # actualiza README.md y docs/resultados.md
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LANGS = ("python", "node", "java")
SEVERITIES = ("CRITICAL", "HIGH", "MEDIUM", "LOW", "UNKNOWN")
LEVELS = ("error", "warning", "info", "style")
TRIVY = ["docker", "run", "--rm", "-v", "/var/run/docker.sock:/var/run/docker.sock",
         "-v", "trivy-cache:/root/.cache", "aquasec/trivy:latest"]
HADOLINT = ["docker", "run", "--rm", "-i", "hadolint/hadolint", "hadolint", "--format", "json", "-"]
MARK_START, MARK_END = "<!-- TABLA:INICIO -->", "<!-- TABLA:FIN -->"


def run(cmd: list[str], stdin: str | None = None) -> str:
    """Ejecuta un comando y devuelve stdout; falla de forma explícita."""
    res = subprocess.run(cmd, input=stdin, capture_output=True, text=True, check=False)
    if res.returncode not in (0, 1):  # hadolint devuelve 1 si hay hallazgos
        raise RuntimeError(f"{' '.join(cmd[:6])}... falló: {res.stderr.strip()[-400:]}")
    return res.stdout


def image_size_mb(image: str) -> float:
    size = int(run(["docker", "image", "inspect", "--format", "{{.Size}}", image]).strip())
    return round(size / 1_000_000, 1)


def trivy_counts(image: str) -> dict[str, int]:
    data = json.loads(run(TRIVY + ["image", "--format", "json", "-q", "--scanners", "vuln", image]))
    vulns = [v for r in data.get("Results", []) for v in r.get("Vulnerabilities") or []]
    counts = {s: sum(1 for v in vulns if v["Severity"] == s) for s in SEVERITIES}
    counts["TOTAL"] = len(vulns)
    counts["FIXABLE_HC"] = sum(
        1 for v in vulns if v["Severity"] in ("HIGH", "CRITICAL") and v.get("FixedVersion"))
    return counts


def hadolint_counts(dockerfile: Path) -> dict[str, int]:
    out = run(HADOLINT, stdin=dockerfile.read_text(encoding="utf-8"))
    findings = json.loads(out or "[]")
    counts = {lv: sum(1 for f in findings if f["level"] == lv) for lv in LEVELS}
    counts["TOTAL"] = len(findings)
    return counts


def trivy_meta() -> str:
    text = run(TRIVY + ["--version"])
    version = re.search(r"Version:\s*(\S+)", text)
    updated = re.search(r"UpdatedAt:\s*(\S+)", text)
    return (f"Trivy {version.group(1) if version else '?'}, "
            f"base de vulnerabilidades del {updated.group(1)[:10] if updated else '?'}")


def measure() -> dict[str, dict[str, dict]]:
    result: dict[str, dict[str, dict]] = {}
    for lang in LANGS:
        result[lang] = {}
        for variant, dockerfile in (("before", "Dockerfile.before"), ("after", "Dockerfile")):
            image = f"dh-{lang}:{variant}"
            sys.stderr.write(f"medir {image}\n")
            result[lang][variant] = {
                "size_mb": image_size_mb(image),
                "trivy": trivy_counts(image),
                "hadolint": hadolint_counts(ROOT / lang / dockerfile),
            }
    return result


def render(data: dict[str, dict[str, dict]], meta: str) -> str:
    lines = [f"_Medido el {date.today().isoformat()} con {meta}._", "",
             "| Lenguaje | Variante | Tamaño (MB) | CRITICAL | HIGH | MEDIUM | LOW | UNKNOWN | Total | HIGH+CRITICAL con parche | hadolint |",
             "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|"]
    for lang in LANGS:
        for variant in ("before", "after"):
            d = data[lang][variant]
            t = d["trivy"]
            lines.append(
                f"| {lang} | {variant} | {d['size_mb']} | {t['CRITICAL']} | {t['HIGH']} | "
                f"{t['MEDIUM']} | {t['LOW']} | {t['UNKNOWN']} | {t['TOTAL']} | "
                f"{t['FIXABLE_HC']} | {d['hadolint']['TOTAL']} |")
    lines += ["", "Reducción de tamaño (before → after):", ""]
    for lang in LANGS:
        b, a = data[lang]["before"]["size_mb"], data[lang]["after"]["size_mb"]
        lines.append(f"- {lang}: {b} MB → {a} MB ({(1 - a / b) * 100:.0f} % menos)")
    return "\n".join(lines)


def replace_block(path: Path, block: str) -> None:
    text = path.read_text(encoding="utf-8")
    pattern = re.compile(re.escape(MARK_START) + r".*?" + re.escape(MARK_END), re.S)
    if not pattern.search(text):
        raise RuntimeError(f"{path} no contiene los marcadores {MARK_START} / {MARK_END}")
    path.write_text(pattern.sub(lambda _: f"{MARK_START}\n{block}\n{MARK_END}", text), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--write", action="store_true", help="actualiza README.md y docs/resultados.md")
    args = parser.parse_args()
    data = measure()
    block = render(data, trivy_meta())
    sys.stdout.write(block + "\n")
    if args.write:
        (ROOT / "docs" / "resultados.json").write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
        for target in (ROOT / "README.md", ROOT / "docs" / "resultados.md"):
            replace_block(target, block)
    return 0


if __name__ == "__main__":
    sys.exit(main())
