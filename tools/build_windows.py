"""Valida Windows en carpeta y publica un único ejecutable autónomo."""
from __future__ import annotations

import argparse
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT))
from tools.packaging_common import (check_version, check_executable, sha256,
                                    write_build_metadata, source_fingerprint, prepare_license_files)


def build(tag: str | None = None) -> None:
    version = check_version(tag)
    source_sha256 = source_fingerprint()
    if sys.platform != "win32" or platform.machine().lower() not in ("amd64", "x86_64"):
        raise RuntimeError("La distribución Windows x64 debe construirse con Python x64 en Windows")
    release = ROOT / "dist/packages/windows-x64"
    diagnostics = ROOT / "build/verification/windows-x64"
    release.mkdir(parents=True, exist_ok=True)
    diagnostics.mkdir(parents=True, exist_ok=True)
    # No mezclar archivos antiguos en el directorio que se publicará.
    if any(release.iterdir()):
        raise RuntimeError("dist/packages/windows-x64 debe estar vacío; conserve o mueva la construcción anterior")
    outputs = []
    for mode in ("onedir", "onefile"):
        # No compartir temporales/caché con OneDrive ni con otra plataforma.
        with tempfile.TemporaryDirectory(prefix=f"cpu-scheduler-windows-{mode}-") as directory:
            local = Path(directory)
            destination = ROOT / "dist" / mode
            licenses = prepare_license_files(local / "licenses")
            command = [sys.executable, "-m", "PyInstaller", "--noconfirm", "--clean",
                       f"--{mode}", "--windowed", "--noupx", "--name", "CPU_Scheduler",
                       "--paths", str(ROOT / "src"), "--collect-all", "reportlab",
                       "--collect-all", "openpyxl", "--add-data",
                       f"{licenses}{os.pathsep}planificador_procesos/licenses",
                       "--distpath", str(destination),
                       "--workpath", str(local / "work"),
                       "--specpath", str(local / "spec"),
                       "--version-file", str(local / "windows_version.txt"),
                       str(ROOT / "run.py")]
            numeric_version = ", ".join(version.split(".") + ["0"])
            (local / "windows_version.txt").write_text(
                "VSVersionInfo(ffi=FixedFileInfo(filevers=(" + numeric_version +
                "), prodvers=(" + numeric_version + "), mask=0x3f, flags=0x0, OS=0x40004, "
                "fileType=0x1, subtype=0x0, date=(0, 0)), kids=[StringFileInfo([StringTable('040904B0', "
                "[StringStruct('CompanyName', 'Aníbal Pedraza Dorado'), "
                "StringStruct('ProductName', 'CPU Scheduler'), "
                f"StringStruct('FileVersion', '{version}'), StringStruct('ProductVersion', '{version}'), "
                "StringStruct('FileDescription', 'Simulador educativo de planificación de CPU'), "
                "StringStruct('OriginalFilename', 'CPU_Scheduler.exe')])]), "
                "VarFileInfo([VarStruct('Translation', [1033, 1200])])])", encoding="utf-8")
            environment = {**os.environ, "PYINSTALLER_CONFIG_DIR": str(local / "cache")}
            try:
                subprocess.run(command, cwd=ROOT, env=environment, check=True)
            finally:
                for warning in (local / "work").rglob("warn-*.txt"):
                    shutil.copyfile(warning, diagnostics / f"warn-{mode}.txt")
        executable = destination / ("CPU_Scheduler/CPU_Scheduler.exe" if mode == "onedir" else "CPU_Scheduler.exe")
        check_executable(executable, diagnostics / f"{mode}.json")
        # La versión en carpeta sólo se conserva como prueba interna.
        if mode == "onefile":
            published = release / f"CPU_Scheduler-{version}-windows-x64.exe"
            shutil.copyfile(executable, published)
            with tempfile.TemporaryDirectory(prefix="cpu-scheduler-published-exe-") as directory:
                copied = Path(directory) / published.name
                shutil.copyfile(published, copied)
                check_executable(copied, diagnostics / "published-exe.json")
            outputs.append(published)
    write_build_metadata(release, "windows-x64", outputs, diagnostics, expected_source_sha256=source_sha256)
    shutil.copyfile(ROOT / "requirements-build.txt", diagnostics / "requirements-build.txt")
    (diagnostics / "pip-freeze.txt").write_text(
        subprocess.check_output([sys.executable, "-m", "pip", "freeze"], text=True), encoding="utf-8")
    print(f"Construcción y comprobaciones correctas: {release}", flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tag", help="Etiqueta de release, debe coincidir con la versión")
    args = parser.parse_args()
    build(args.tag)
