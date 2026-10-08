"""Reúne únicamente una construcción verificada de cada plataforma."""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
import shutil
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools.packaging_common import VERSION, sha256

PLATFORMS = ("windows-x64", "macos-arm64", "macos-x86_64")


def package_names(version: str, platform_name: str) -> set[str]:
    base = f"CPU_Scheduler-{version}-{platform_name}"
    if platform_name == "windows-x64":
        return {f"{base}.exe"}
    if platform_name in PLATFORMS:
        return {f"{base}.zip"}
    raise ValueError(f"Plataforma no compatible: {platform_name}")


def assemble(source: Path, output: Path) -> None:
    metadata = []
    packages = []
    for platform_name in PLATFORMS:
        candidates = list(source.rglob(f"BUILD_INFO_{platform_name}.json"))
        if len(candidates) != 1:
            raise RuntimeError(f"Falta una única construcción de {platform_name}")
        info_path = candidates[0]
        info = json.loads(info_path.read_text(encoding="utf-8"))
        if info["version"] != VERSION or info["platform"] != platform_name:
            raise RuntimeError("Versión o plataforma incorrecta en la construcción")
        if {entry["name"] for entry in info["assets"]} != package_names(VERSION, platform_name):
            raise RuntimeError(f"Paquetes incompletos para {platform_name}")
        manifest = info_path.parent / f"SHA256SUMS_{platform_name}.txt"
        expected = {entry["name"]: entry["sha256"] for entry in info["assets"]}
        expected[info_path.name] = sha256(info_path)
        actual = dict((line.split("  ", 1)[1], line.split("  ", 1)[0])
                      for line in manifest.read_text(encoding="utf-8").splitlines())
        if actual != expected:
            raise RuntimeError(f"Manifest incorrecto para {platform_name}")
        for entry in info["assets"]:
            name = entry["name"]
            if Path(name).name != name:
                raise RuntimeError("Nombre de paquete inválido")
            package = info_path.parent / name
            if package.stat().st_size != entry["size"] or sha256(package) != entry["sha256"]:
                raise RuntimeError(f"Paquete corrupto: {name}")
            packages.append(package)
        if not isinstance(info.get("source_sha256"), str) or not re.fullmatch(r"[0-9a-f]{64}", info["source_sha256"]):
            raise RuntimeError(f"Falta la huella de fuentes en {platform_name}; reconstruya el paquete")
        metadata.append(info)
    if len({item.get("commit") for item in metadata}) != 1:
        raise RuntimeError("Los paquetes proceden de commits distintos")
    if len({item["source_sha256"] for item in metadata}) != 1:
        raise RuntimeError("Los paquetes contienen fuentes distintas aunque tengan la misma versión y commit")
    output.mkdir(parents=True, exist_ok=True)
    if any(output.iterdir()):
        raise RuntimeError("El directorio final de release debe estar vacío")
    for package in packages:
        shutil.copyfile(package, output / package.name)
    info = {"version": VERSION, "commit": metadata[0].get("commit"),
            "source_sha256": metadata[0]["source_sha256"],
            "working_tree_dirty": any(item.get("working_tree_dirty", True) for item in metadata),
            "platforms": metadata,
            "assets": [entry for item in metadata for entry in item["assets"]]}
    info_path = output / "BUILD_INFO.json"
    info_path.write_text(json.dumps(info, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    sources = [*sorted(output.glob("*.zip")), *sorted(output.glob("*.exe")), info_path]
    (output / "SHA256SUMS.txt").write_text(
        "".join(f"{sha256(item)}  {item.name}\n" for item in sources), encoding="utf-8")
    print(f"Tres aplicaciones verificadas: {output}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=ROOT / "dist/release")
    args = parser.parse_args()
    assemble(args.source.resolve(), args.output.resolve())
