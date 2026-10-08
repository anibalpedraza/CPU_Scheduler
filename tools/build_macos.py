"""Construye y verifica una aplicación macOS nativa; debe ejecutarse en un Mac."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import platform
import plistlib
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools.packaging_common import (check_executable, check_version, third_party_notices,
                                    write_build_metadata, source_fingerprint, prepare_license_files)


def native_architecture() -> str:
    architecture = platform.machine().lower()
    if sys.platform != "darwin" or architecture not in ("arm64", "x86_64"):
        raise RuntimeError("Ejecute este script en macOS con Python arm64 o x86_64")
    return architecture


def symlinks(directory: Path) -> dict[str, str]:
    return {item.relative_to(directory).as_posix(): os.readlink(item)
            for item in directory.rglob("*") if item.is_symlink()}


def clean_finder_metadata(bundle: Path) -> None:
    """Retira sólo los metadatos de Finder incompatibles con codesign.

    OneDrive puede añadirlos al bundle recién construido. No se siguen enlaces
    ni se elimina la cuarentena u otros atributos de seguridad de macOS.
    """
    for name in ("com.apple.FinderInfo", "com.apple.ResourceFork"):
        # -s actúa sobre los enlaces, sin modificar sus destinos externos.
        subprocess.run(["xattr", "-drs", name, str(bundle)], check=True)


def verify_architecture(executable: Path, architecture: str) -> None:
    # lipo clásico consume todas las palabras tras -verify_arch como arquitecturas.
    subprocess.run(["lipo", str(executable), "-verify_arch", architecture], check=True)


def verify_bundle(bundle: Path, architecture: str, version: str) -> dict:
    with (bundle / "Contents/Info.plist").open("rb") as stream:
        info = plistlib.load(stream)
    if info.get("CFBundleShortVersionString") != version or info.get("CFBundleVersion") != version:
        raise RuntimeError("La versión de Info.plist no coincide con la aplicación")
    executable = bundle / "Contents/MacOS" / info["CFBundleExecutable"]
    verify_architecture(executable, architecture)
    subprocess.run(["codesign", "--verify", "--deep", "--strict", str(bundle)], check=True)
    if not os.access(executable, os.X_OK):
        raise RuntimeError("El ejecutable macOS no conserva permisos de ejecución")
    return info


def build(tag: str | None = None, expected_arch: str | None = None) -> None:
    version = check_version(tag)
    source_sha256 = source_fingerprint()
    architecture = native_architecture()
    if sys.version_info[:2] != (3, 12):
        raise RuntimeError("Para el paquete macOS use Python 3.12, como en GitHub Actions")
    if expected_arch is not None and expected_arch != architecture:
        raise RuntimeError(f"Se esperaba {expected_arch}, pero Python ejecuta {architecture}")
    for tool in ("lipo", "codesign", "ditto", "open", "xattr"):
        if shutil.which(tool) is None:
            raise RuntimeError(f"Falta {tool}. Instale las herramientas de línea de comandos de Xcode")
    platform_name = f"macos-{architecture}"
    release = ROOT / "dist/packages" / platform_name
    work = ROOT / "build" / platform_name
    destination = ROOT / "dist" / platform_name
    diagnostics = ROOT / "build/verification" / platform_name
    for directory in (release, work, diagnostics):
        directory.mkdir(parents=True, exist_ok=True)
    if any(release.iterdir()):
        raise RuntimeError(f"{release} debe estar vacío; conserve o mueva la construcción anterior")
    # La configuración se escribe antes de construir para no alterar la firma después.
    licenses = prepare_license_files(work / "licenses")
    spec = work / "CPU_Scheduler.spec"
    spec.write_text(
        "from PyInstaller.utils.hooks import collect_all\n"
        "rd, rb, rh = collect_all('reportlab')\n"
        "xd, xb, xh = collect_all('openpyxl')\n"
        f"a = Analysis([{str(ROOT / 'run.py')!r}], pathex=[{str(ROOT / 'src')!r}], "
        f"binaries=rb+xb, datas=rd+xd+[({str(licenses)!r}, 'planificador_procesos/licenses')], hiddenimports=rh+xh)\n"
        "pyz = PYZ(a.pure)\n"
        "exe = EXE(pyz, a.scripts, [], exclude_binaries=True, name='CPU_Scheduler', "
        f"console=False, strip=False, upx=False, argv_emulation=False, target_arch={architecture!r}, "
        "codesign_identity=None, entitlements_file=None)\n"
        "coll = COLLECT(exe, a.binaries, a.datas, strip=False, upx=False, name='CPU_Scheduler')\n"
        f"app = BUNDLE(coll, name='CPU_Scheduler.app', bundle_identifier='es.uclm.cpu-scheduler', "
        f"version={version!r}, info_plist={{'CFBundleVersion': {version!r}, "
        "'NSHighResolutionCapable': True})\n", encoding="utf-8")
    env = {**os.environ, "PYINSTALLER_STRICT_BUNDLE_CODESIGN_ERROR": "1"}
    subprocess.run([sys.executable, "-m", "PyInstaller", "--noconfirm", "--clean",
                    "--distpath", str(destination), "--workpath", str(work), str(spec)],
                   cwd=ROOT, env=env, check=True)
    app = destination / "CPU_Scheduler.app"
    clean_finder_metadata(app)
    info = verify_bundle(app, architecture, version)
    check_executable(app / "Contents/MacOS/CPU_Scheduler", diagnostics / "app-direct.json",
                     architecture=architecture)
    check_executable(app, diagnostics / "app-finder.json", finder=True, architecture=architecture)
    folder_name = f"CPU_Scheduler-{version}-{platform_name}"
    archive = release / f"{folder_name}.zip"
    with tempfile.TemporaryDirectory(prefix="cpu-scheduler-macos-") as directory:
        folder = Path(directory) / folder_name
        folder.mkdir()
        staged = folder / app.name
        shutil.copytree(app, staged, symlinks=True)
        clean_finder_metadata(staged)
        verify_bundle(staged, architecture, version)
        original_links = symlinks(staged)
        subprocess.run(["ditto", "-c", "-k", "--sequesterRsrc", "--keepParent",
                        str(staged), str(archive)], check=True)
    with tempfile.TemporaryDirectory(prefix="cpu-scheduler-macos-zip-") as directory:
        # ditto conserva los enlaces, permisos y recursos del bundle.
        subprocess.run(["ditto", "-x", "-k", str(archive), directory], check=True)
        extracted = Path(directory) / app.name
        if symlinks(extracted) != original_links:
            raise RuntimeError("El ZIP no ha conservado los enlaces simbólicos de la aplicación")
        verify_bundle(extracted, architecture, version)
        check_executable(extracted / "Contents/MacOS/CPU_Scheduler", diagnostics / "zip-direct.json",
                         architecture=architecture)
        check_executable(extracted, diagnostics / "zip-finder.json", finder=True, architecture=architecture)
    write_build_metadata(release, platform_name, [archive], diagnostics,
                         expected_source_sha256=source_sha256,
                         macos_build_version=platform.mac_ver()[0],
                         bundle_minimum_macos=info.get("LSMinimumSystemVersion"),
                         code_signing="ad-hoc", notarized=False)
    (diagnostics / "bundle-info.json").write_text(json.dumps(info, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Aplicación y ZIP macOS verificados: {archive}", flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tag")
    parser.add_argument("--architecture", choices=("arm64", "x86_64"))
    args = parser.parse_args()
    build(args.tag, args.architecture)
