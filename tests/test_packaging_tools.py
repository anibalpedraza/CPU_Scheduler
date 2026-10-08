"""Protecciones de versión, reunión de plataformas e integridad antes de publicar."""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from planificador_procesos.metadata import VERSION
from tools.assemble_release import PLATFORMS, assemble, package_names
from tools.build_macos import clean_finder_metadata, native_architecture
from tools.packaging_common import build_context, check_version, source_fingerprint, write_build_metadata

SOURCE_SHA256 = source_fingerprint()
from tools.publish_release import publish, verify_assets


def write_manifest(root, names, manifest="SHA256SUMS.txt"):
    (root / manifest).write_text("".join(
        f"{hashlib.sha256((root / name).read_bytes()).hexdigest()}  {name}\n"
        for name in sorted(names)), encoding="utf-8")


class PackagingToolsTests(unittest.TestCase):
    @unittest.skipUnless(sys.platform == "darwin", "Atributos nativos de macOS")
    def test_finder_cleanup_preserves_quarantine_and_external_symlink_target(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            bundle = root / "Example.app"
            bundle.mkdir()
            binary = bundle / "binary"
            binary.write_bytes(b"content")
            external = root / "external"
            external.write_bytes(b"external")
            (bundle / "link").symlink_to(external)
            for item in (bundle, binary, external):
                subprocess.run(["xattr", "-wx", "com.apple.FinderInfo", "5445585474747874" + "00" * 24, str(item)], check=True)
                if item.is_file():
                    subprocess.run(["xattr", "-w", "com.apple.ResourceFork", "metadata", str(item)], check=True)
            subprocess.run(["xattr", "-w", "com.apple.quarantine", "0081;00000000;validation;", str(binary)], check=True)
            clean_finder_metadata(bundle)
            for item in (bundle, binary):
                attributes = subprocess.check_output(["xattr", str(item)], text=True).splitlines()
                self.assertNotIn("com.apple.FinderInfo", attributes)
                self.assertNotIn("com.apple.ResourceFork", attributes)
            self.assertEqual(binary.read_bytes(), b"content")
            self.assertEqual(subprocess.check_output(["xattr", "-p", "com.apple.quarantine", str(binary)], text=True).strip(), "0081;00000000;validation;")
            attributes = subprocess.check_output(["xattr", str(external)], text=True).splitlines()
            self.assertIn("com.apple.FinderInfo", attributes)
            self.assertIn("com.apple.ResourceFork", attributes)
            self.assertTrue((bundle / "link").is_symlink())

    def make_assets(self, root):
        entries = []
        platforms = []
        for platform_name in PLATFORMS:
            current = []
            for name in sorted(package_names(VERSION, platform_name)):
                (root / name).write_bytes(b"package for publication test")
                entry = {"name": name, "size": (root / name).stat().st_size,
                         "sha256": hashlib.sha256((root / name).read_bytes()).hexdigest()}
                current.append(entry)
                entries.append(entry)
            platforms.append({"platform": platform_name, "version": VERSION,
                              "commit": "a" * 40, "working_tree_dirty": False, "source_sha256": SOURCE_SHA256, "assets": current})
        (root / "BUILD_INFO.json").write_text(json.dumps(
            {"version": VERSION, "commit": "a" * 40, "working_tree_dirty": False,
             "platforms": platforms, "source_sha256": SOURCE_SHA256, "assets": entries}), encoding="utf-8")
        write_manifest(root, [item.name for item in root.iterdir()])

    def make_platform_builds(self, root):
        for platform_name in PLATFORMS:
            target = root / platform_name
            target.mkdir()
            entries = []
            for name in sorted(package_names(VERSION, platform_name)):
                (target / name).write_bytes(b"platform package")
                entries.append({"name": name, "size": (target / name).stat().st_size,
                                "sha256": hashlib.sha256((target / name).read_bytes()).hexdigest()})
            info_path = target / f"BUILD_INFO_{platform_name}.json"
            info_path.write_text(json.dumps({"version": VERSION, "platform": platform_name,
                "commit": "a" * 40, "working_tree_dirty": False, "source_sha256": SOURCE_SHA256, "assets": entries}), encoding="utf-8")
            write_manifest(target, [item.name for item in target.iterdir()],
                           f"SHA256SUMS_{platform_name}.txt")


    def test_source_fingerprint_normalizes_line_endings_but_detects_code_changes(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "src/planificador_procesos").mkdir(parents=True)
            (root / "run.py").write_bytes(b"main()\n")
            code = root / "src/planificador_procesos/app.py"
            code.write_bytes(b"x = 1\ny = 2\n")
            expected = source_fingerprint(root)
            (root / "run.py").write_bytes(b"main()\r\n")
            code.write_bytes(b"x = 1\r\ny = 2\r\n")
            self.assertEqual(source_fingerprint(root), expected)
            code.write_bytes(b"x = 2\r\ny = 2\r\n")
            self.assertNotEqual(source_fingerprint(root), expected)

    def test_changed_sources_during_build_prevent_successful_metadata(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            with self.assertRaisesRegex(RuntimeError, "cambiaron durante"):
                write_build_metadata(target, "windows-x64", [], target,
                                     expected_source_sha256="0" * 64)
            self.assertFalse((target / "BUILD_INFO_windows-x64.json").exists())

    def test_assembly_rejects_same_commit_with_different_source_content(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source"
            source.mkdir()
            self.make_platform_builds(source)
            target = source / "macos-arm64"
            info_path = target / "BUILD_INFO_macos-arm64.json"
            info = json.loads(info_path.read_text())
            info["source_sha256"] = "0" * 64
            info_path.write_text(json.dumps(info), encoding="utf-8")
            write_manifest(target, [item.name for item in target.iterdir() if item.suffix != ".txt"],
                           "SHA256SUMS_macos-arm64.txt")
            with self.assertRaisesRegex(RuntimeError, "fuentes distintas"):
                assemble(source, root / "output")
            self.assertFalse((root / "output").exists())

    def test_publication_rejects_packages_from_other_source_content(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.make_assets(root)
            info_path = root / "BUILD_INFO.json"
            info = json.loads(info_path.read_text())
            info["source_sha256"] = "0" * 64
            info_path.write_text(json.dumps(info), encoding="utf-8")
            write_manifest(root, [item.name for item in root.iterdir() if item.name != "SHA256SUMS.txt"])
            with patch("tools.publish_release.gh") as command:
                with self.assertRaisesRegex(RuntimeError, "fuentes de publicación"):
                    publish(f"v{VERSION}", "example/repo", root)
                command.assert_not_called()

    def test_tag_must_match_application_version(self):
        self.assertEqual(check_version(f"v{VERSION}"), VERSION)
        with self.assertRaises(RuntimeError):
            check_version("v0.0.0")

    def test_build_without_git_is_marked_for_local_validation(self):
        with patch("tools.packaging_common.subprocess.check_output", side_effect=FileNotFoundError):
            self.assertEqual(build_context(), {"commit": None, "working_tree_dirty": True})

    def test_macos_build_cannot_run_on_windows(self):
        with patch("tools.build_macos.sys.platform", "win32"):
            with self.assertRaisesRegex(RuntimeError, "macOS"):
                native_architecture()

    def test_hash_verification_rejects_corruption_and_extra_files(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "package.zip").write_bytes(b"original")
            (root / "SHA256SUMS.txt").write_text("manifest")
            expected = {"package.zip": hashlib.sha256(b"original").hexdigest()}
            verify_assets(root, expected)
            (root / "package.zip").write_bytes(b"changed")
            with self.assertRaises(RuntimeError):
                verify_assets(root, expected)
            (root / "package.zip").write_bytes(b"original")
            (root / "unexpected.exe").write_bytes(b"extra")
            with self.assertRaises(RuntimeError):
                verify_assets(root, expected)

    def test_assembly_requires_all_three_platforms(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source"
            source.mkdir()
            self.make_platform_builds(source)
            shutil.rmtree(source / "macos-x86_64")
            with self.assertRaisesRegex(RuntimeError, "macos-x86_64"):
                assemble(source, root / "output")
            self.assertFalse((root / "output").exists())

    def test_assembly_rejects_corrupt_package(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source"
            source.mkdir()
            self.make_platform_builds(source)
            next((source / "macos-arm64").glob("*.zip")).write_bytes(b"corrupt")
            with self.assertRaisesRegex(RuntimeError, "corrupto"):
                assemble(source, root / "output")
            self.assertFalse((root / "output").exists())

    def test_assembly_rejects_packages_from_different_commits(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source"
            source.mkdir()
            self.make_platform_builds(source)
            target = source / "macos-arm64"
            info_path = target / "BUILD_INFO_macos-arm64.json"
            info = json.loads(info_path.read_text())
            info["commit"] = "b" * 40
            info_path.write_text(json.dumps(info), encoding="utf-8")
            write_manifest(target, [item.name for item in target.iterdir() if item.suffix != ".txt"],
                           "SHA256SUMS_macos-arm64.txt")
            with self.assertRaisesRegex(RuntimeError, "commits distintos"):
                assemble(source, root / "output")

    def test_assembly_produces_three_verified_applications(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source"
            source.mkdir()
            self.make_platform_builds(source)
            assemble(source, root / "output")
            info = json.loads((root / "output/BUILD_INFO.json").read_text())
            self.assertEqual(len(info["assets"]), 3)
            self.assertEqual({item["platform"] for item in info["platforms"]}, set(PLATFORMS))
            expected = {line.split("  ", 1)[1]: line.split("  ", 1)[0]
                        for line in (root / "output/SHA256SUMS.txt").read_text().splitlines()}
            verify_assets(root / "output", expected)

    def test_uncommitted_validation_packages_cannot_be_published(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.make_assets(root)
            info_path = root / "BUILD_INFO.json"
            info = json.loads(info_path.read_text())
            info["working_tree_dirty"] = True
            info_path.write_text(json.dumps(info), encoding="utf-8")
            write_manifest(root, [item.name for item in root.iterdir() if item.name != "SHA256SUMS.txt"])
            with patch("tools.publish_release.gh") as command:
                with self.assertRaisesRegex(RuntimeError, "cambios locales"):
                    publish(f"v{VERSION}", "example/repo", root)
                command.assert_not_called()

    def test_published_release_is_never_overwritten(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.make_assets(root)
            remote = json.dumps([[{"tag_name": f"v{VERSION}", "draft": False}]])
            with patch("tools.publish_release.gh", return_value=remote) as command:
                with self.assertRaisesRegex(RuntimeError, "ya está publicada"):
                    publish(f"v{VERSION}", "example/repo", root)
                self.assertEqual(command.call_count, 1)

    def test_corrupt_download_prevents_publication(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.make_assets(root)

            def fake_gh(*args):
                if args[0] == "api":
                    return "[]"
                if args[:2] == ("release", "download"):
                    target = Path(args[args.index("--dir") + 1])
                    for source in root.iterdir():
                        shutil.copyfile(source, target / source.name)
                    next(target.glob("*.zip")).write_bytes(b"corrupt download")
                return ""

            with patch("tools.publish_release.gh", side_effect=fake_gh) as command:
                with self.assertRaisesRegex(RuntimeError, "Integridad incorrecta"):
                    publish(f"v{VERSION}", "example/repo", root)
                self.assertFalse(any(call.args[:2] == ("release", "edit")
                                     for call in command.call_args_list))

    def test_publication_follows_successful_download_verification(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.make_assets(root)

            def fake_gh(*args):
                if args[0] == "api":
                    return "[]"
                if args[:2] == ("release", "download"):
                    target = Path(args[args.index("--dir") + 1])
                    for source in root.iterdir():
                        shutil.copyfile(source, target / source.name)
                if args[:2] == ("release", "view"):
                    return json.dumps({"isDraft": False, "url": "https://example.invalid/release",
                        "assets": [{"name": source.name, "size": source.stat().st_size}
                                   for source in root.iterdir()]})
                return ""

            with patch("tools.publish_release.gh", side_effect=fake_gh) as command:
                publish(f"v{VERSION}", "example/repo", root)
                actions = [call.args[:2] for call in command.call_args_list]
                self.assertLess(actions.index(("release", "download")), actions.index(("release", "edit")))
