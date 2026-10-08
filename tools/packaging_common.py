"""Comprobaciones y metadatos compartidos por los paquetes de escritorio."""
from __future__ import annotations

import hashlib
from importlib import metadata
import json
import os
from pathlib import Path
import platform
import re
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from planificador_procesos import __version__
from planificador_procesos.metadata import VERSION


def check_version(tag: str | None = None) -> str:
    match = re.search(r'^version = "([^"]+)"$', (ROOT / "pyproject.toml").read_text(encoding="utf-8"), re.M)
    if match is None or match[1] != VERSION or __version__ != VERSION:
        raise RuntimeError("Las versiones del paquete y de la interfaz no coinciden")
    if tag is not None and tag != f"v{VERSION}":
        raise RuntimeError(f"La etiqueta debe ser v{VERSION}; recibida: {tag}")
    return VERSION


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def source_fingerprint(root: Path = ROOT) -> str:
    """Identifica el código compartido, normalizando finales de línea de Git."""
    sources = [root / "run.py", *sorted((root / "src/planificador_procesos").rglob("*.py"))]
    if len(sources) < 2:
        raise RuntimeError("No se encuentran las fuentes de la aplicación")
    digest = hashlib.sha256()
    for source in sorted(sources, key=lambda item: item.relative_to(root).as_posix()):
        relative = source.relative_to(root).as_posix().encode("utf-8")
        content = source.read_bytes().replace(b"\r\n", b"\n").replace(b"\r", b"\n")
        digest.update(relative + b"\0" + len(content).to_bytes(8, "big") + content)
    return digest.hexdigest()


def build_context() -> dict:
    try:
        commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True,
                                         stderr=subprocess.DEVNULL).strip()
        dirty = bool(subprocess.check_output(["git", "status", "--porcelain"], cwd=ROOT,
                                             text=True, stderr=subprocess.DEVNULL).strip())
    except (OSError, subprocess.CalledProcessError):
        commit, dirty = None, True  # Copia de fuentes sin .git, destinada a validación local.
    return {"commit": commit, "working_tree_dirty": dirty}


def check_executable(executable: Path, report: Path, *, finder: bool = False,
                     architecture: str | None = None) -> None:
    report = report.resolve()
    report.parent.mkdir(parents=True, exist_ok=True)
    report.unlink(missing_ok=True)
    env = {key: value for key, value in os.environ.items()
           if key not in ("PYTHONPATH", "PYTHONHOME", "TCL_LIBRARY", "TK_LIBRARY",
                          "DYLD_LIBRARY_PATH", "DYLD_FRAMEWORK_PATH")}
    command = (["open", "-W", "-n", str(executable), "--args", "--self-test", str(report)]
               if finder else [str(executable), "--self-test", str(report)])
    with tempfile.TemporaryDirectory(prefix="cpu-scheduler-launch-") as directory:
        result = subprocess.run(command, cwd=directory, env=env, timeout=120)
    if result.returncode != 0 or not report.is_file():
        raise RuntimeError(f"Falló {executable.name}; consulte {report}")
    data = json.loads(report.read_text(encoding="utf-8"))
    if not data.get("success") or not data.get("frozen") or data.get("version") != VERSION:
        raise RuntimeError(f"Comprobación del paquete fallida: {data}")
    if architecture is not None and data.get("architecture") != architecture:
        raise RuntimeError(f"Arquitectura incorrecta: {data.get('architecture')}")


def third_party_notices() -> str:
    texts = ["CPU Scheduler: componentes de terceros incluidos en el paquete.\n"]
    for name in ("pyinstaller", "reportlab", "openpyxl", "pillow", "charset-normalizer", "et-xmlfile"):
        dist = metadata.distribution(name)
        texts.append(f"\n===== {dist.metadata['Name']} {dist.version} =====\n")
        for item in dist.files or ():
            if any(word in item.name.lower() for word in ("license", "licence", "copying")):
                source = Path(dist.locate_file(item))
                if source.is_file():
                    texts.append(source.read_text(encoding="utf-8", errors="replace"))
    base = Path(sys.base_prefix)
    candidates = [base / "LICENSE.txt", base / "Resources/LICENSE.txt",
                  *sorted((base / "tcl").glob("*/license.terms")),
                  *sorted((base / "lib").glob("*/license.terms"))]
    import tkinter as tk
    probe = tk.Tk()
    probe.withdraw()
    try:
        for library in (probe.tk.call("info", "library"), probe.tk.call("set", "tk_library")):
            candidates.append(Path(str(library)) / "license.terms")
            candidates.append(Path(str(library)).parent / "license.terms")
    finally:
        probe.destroy()
    for source in dict.fromkeys(candidates):
        if source.is_file():
            texts.extend([f"\n===== {source.name} ({source.parent.name}) =====\n",
                          source.read_text(encoding="utf-8", errors="replace")])
    return "\n".join(texts)


def prepare_license_files(directory: Path) -> Path:
    directory.mkdir(parents=True, exist_ok=True)
    (directory / "LICENSE.txt").write_text((ROOT / "LICENSE").read_text(encoding="utf-8"), encoding="utf-8")
    (directory / "THIRD_PARTY_NOTICES.txt").write_text(third_party_notices(), encoding="utf-8")
    return directory


def write_build_metadata(directory: Path, platform_name: str, outputs: list[Path],
                         diagnostics: Path, expected_source_sha256: str | None = None, **extra) -> None:
    source_sha256 = source_fingerprint()
    if expected_source_sha256 is not None and source_sha256 != expected_source_sha256:
        raise RuntimeError("Las fuentes cambiaron durante la construcción; no se validará este paquete")
    info = {"version": VERSION, **build_context(), "python": platform.python_version(),
            "platform": platform_name, "source_sha256": source_sha256,
            "assets": [{"name": item.name, "size": item.stat().st_size, "sha256": sha256(item)}
                       for item in outputs],
            "dependencies": {name: metadata.version(name)
                             for name in ("pyinstaller", "pyinstaller-hooks-contrib", "reportlab",
                                          "openpyxl", "pillow", "charset-normalizer", "et-xmlfile")},
            **extra}
    info_path = directory / f"BUILD_INFO_{platform_name}.json"
    info_path.write_text(json.dumps(info, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (directory / f"SHA256SUMS_{platform_name}.txt").write_text(
        "".join(f"{sha256(item)}  {item.name}\n" for item in [*outputs, info_path]), encoding="utf-8")
    diagnostics.mkdir(parents=True, exist_ok=True)
    (diagnostics / "pip-freeze.txt").write_text(
        subprocess.check_output([sys.executable, "-m", "pip", "freeze"], text=True), encoding="utf-8")
