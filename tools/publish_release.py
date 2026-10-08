"""Publica únicamente después de descargar y verificar todos los assets del borrador."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
import sys
sys.path.insert(0, str(ROOT))
from tools.assemble_release import PLATFORMS, package_names
from tools.packaging_common import source_fingerprint


def gh(*args: str) -> str:
    return subprocess.check_output(["gh", *args], text=True)


def verify_assets(directory: Path, expected: dict[str, str]) -> None:
    actual = {source.name for source in directory.iterdir() if source.is_file()}
    if actual != set(expected) | {"SHA256SUMS.txt"}:
        raise RuntimeError(f"Archivos de release inesperados: {actual}")
    for name, digest in expected.items():
        if hashlib.sha256((directory / name).read_bytes()).hexdigest() != digest:
            raise RuntimeError(f"Integridad incorrecta: {name}")


def publish(tag: str, repository: str, assets: Path) -> None:
    info = json.loads((assets / "BUILD_INFO.json").read_text(encoding="utf-8"))
    if tag != f"v{info['version']}":
        raise RuntimeError("La etiqueta no coincide con la versión compilada")
    expected = {}
    for line in (assets / "SHA256SUMS.txt").read_text(encoding="utf-8").splitlines():
        digest, name = line.split("  ", 1)
        if Path(name).name != name or len(digest) != 64 or name in expected:
            raise RuntimeError("Manifest de integridad inválido")
        expected[name] = digest
    verify_assets(assets, expected)
    required = set().union(*(package_names(info["version"], item) for item in PLATFORMS))
    if info.get("working_tree_dirty", True) or not info.get("commit"):
        raise RuntimeError("No se publicarán paquetes de fuentes sin commit o con cambios locales")
    if {item["platform"] for item in info.get("platforms", [])} != set(PLATFORMS):
        raise RuntimeError("La release debe incluir Windows, Apple Silicon e Intel")
    if info.get("source_sha256") != source_fingerprint():
        raise RuntimeError("El código de los paquetes no coincide con las fuentes de publicación")
    if any(item.get("source_sha256") != info["source_sha256"] for item in info["platforms"]):
        raise RuntimeError("Los paquetes contienen fuentes distintas")
    if set(expected) != required | {"BUILD_INFO.json"}:
        raise RuntimeError("La release debe incluir las tres aplicaciones Windows/macOS y BUILD_INFO.json")
    if {entry["name"] for entry in info["assets"]} != required:
        raise RuntimeError("BUILD_INFO.json no describe las tres aplicaciones")
    for entry in info["assets"]:
        source = assets / entry["name"]
        if entry["sha256"] != expected[entry["name"]] or entry["size"] != source.stat().st_size:
            raise RuntimeError("BUILD_INFO.json no coincide con los paquetes")
    notes = ROOT / "docs" / f"RELEASE_{info['version']}.md"
    if not notes.is_file():
        raise RuntimeError(f"Faltan las notas de versión: {notes.name}")
    # Listar también borradores: no interpretar un error de red como release ausente.
    releases = json.loads(gh("api", "--paginate", "--slurp", f"repos/{repository}/releases?per_page=100"))
    existing = next((item for page in releases for item in page if item["tag_name"] == tag), None)
    if existing and not existing["draft"]:
        raise RuntimeError("La release ya está publicada; no se sustituirán sus archivos")
    if not existing:
        gh("release", "create", tag, "--repo", repository, "--verify-tag", "--draft",
           "--title", f"CPU Scheduler {info['version']}", "--notes-file", str(notes))
    gh("release", "upload", tag, "--repo", repository, "--clobber",
       *[str(source) for source in sorted(assets.iterdir()) if source.is_file()])
    with tempfile.TemporaryDirectory(prefix="cpu-scheduler-release-") as directory:
        downloaded = Path(directory)
        gh("release", "download", tag, "--repo", repository, "--dir", directory)
        if (downloaded / "SHA256SUMS.txt").read_bytes() != (assets / "SHA256SUMS.txt").read_bytes():
            raise RuntimeError("El manifest descargado no coincide")
        verify_assets(downloaded, expected)
    gh("release", "edit", tag, "--repo", repository, "--draft=false",
       "--title", f"CPU Scheduler {info['version']}", "--notes-file", str(notes))
    published = json.loads(gh("release", "view", tag, "--repo", repository,
                              "--json", "isDraft,assets,url"))
    remote = {item["name"]: item["size"] for item in published["assets"]}
    local = {source.name: source.stat().st_size for source in assets.iterdir() if source.is_file()}
    if published["isDraft"] or remote != local:
        raise RuntimeError("La verificación final de la release ha fallado")
    print(published["url"])


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tag", required=True)
    parser.add_argument("--repo", required=True)
    parser.add_argument("--assets", type=Path, required=True)
    args = parser.parse_args()
    publish(args.tag, args.repo, args.assets.resolve())
