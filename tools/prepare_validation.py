"""Copia de las fuentes actuales para validar en un Mac sin commit ni acceso a GitHub."""
from __future__ import annotations

import json
from pathlib import Path
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools.packaging_common import VERSION, build_context, sha256, source_fingerprint


def prepare() -> Path:
    # Lista explícita: no incluye .git, entornos, credenciales, binarios ni archivos personales.
    sources = [ROOT / name for name in
               ("run.py", "pyproject.toml", "requirements.txt", "requirements-build.txt",
                "README.md", "LICENSE", "VALIDAR_MACOS.command", "CAMBIOS_2.0.0.md")]
    for directory in ("src", "tests", "tools", "docs", "examples", ".github/workflows"):
        sources.extend(item for item in (ROOT / directory).rglob("*")
                       if item.is_file() and "__pycache__" not in item.parts
                       and item.suffix not in (".pyc", ".pyo") and ".egg-info" not in str(item))
    destination = ROOT / "dist/validation"
    destination.mkdir(parents=True, exist_ok=True)
    archive = destination / f"CPU_Scheduler-{VERSION}-fuentes-validacion.zip"
    folder = f"CPU_Scheduler-{VERSION}"
    with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED) as bundle:
        for source in sorted(set(sources)):
            relative = source.relative_to(ROOT).as_posix()
            if source.suffix == ".command":
                info = zipfile.ZipInfo(f"{folder}/{relative}")
                info.create_system = 3
                info.external_attr = 0o100755 << 16
                info.compress_type = zipfile.ZIP_DEFLATED
                bundle.writestr(info, source.read_bytes())
            else:
                bundle.write(source, f"{folder}/{relative}")
        bundle.writestr(f"{folder}/SOURCE_INFO.json",
                        json.dumps({"version": VERSION, **build_context(),
                                    "purpose": "local-validation", "source_sha256": source_fingerprint()}, indent=2) + "\n")
    (archive.with_suffix(".sha256.txt")).write_text(f"{sha256(archive)}  {archive.name}\n", encoding="utf-8")
    print(archive)
    return archive


if __name__ == "__main__":
    prepare()
