"""Verify launcher mounts, resume arguments, image upgrades and explicit cleanup."""

import json
import os
import pathlib
import subprocess
import tempfile
import unittest


class LauncherTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="codex-launcher-test-")
        self.addCleanup(self.temp.cleanup)
        self.root = pathlib.Path(self.temp.name)
        self.launcher = pathlib.Path(__file__).resolve().parents[1] / "codex.sh"
        fake = '''#!/usr/bin/env python3
import json, os, sys
if sys.argv[1] == "image":
    print(os.environ.get("MOCK_IMAGE_LAYOUT", "1"))
elif sys.argv[1] == "run" or sys.argv[1:3] == ["volume", "rm"]:
    print(json.dumps(sys.argv[1:]))
'''
        for name in ["podman", "docker"]:
            engine = self.root / name
            engine.write_text(fake)
            engine.chmod(0o755)
        make = self.root / "make"
        make.write_text('#!/bin/sh\nprintf "%s\\n" "$@" > "$BUILD_CAPTURE"\n')
        make.chmod(0o755)
        self.env = dict(os.environ, PATH=f"{self.root}:/usr/bin:/bin",
                        BUILD_CAPTURE=str(self.root / "build"),
                        OPENAI_API_KEY="do-not-forward", AWS_SECRET_ACCESS_KEY="do-not-forward")

    def run_launcher(self, *args):
        result = subprocess.run([str(self.launcher), *args], env=self.env,
                                text=True, capture_output=True, check=True)
        return json.loads(result.stdout)

    def test_new_conversation_has_only_history_volume(self):
        args = self.run_launcher()
        mounts = [args[i + 1] for i, arg in enumerate(args) if arg == "--mount"]
        self.assertEqual(mounts, ["type=volume,source=agent-containers-codex-history,target=/home/node/codex-history"])
        self.assertIn("--read-only", args)
        self.assertEqual(args.count("--tmpfs"), 2)
        self.assertIn('cli_auth_credentials_store="ephemeral"', args)
        self.assertNotIn("resume", args)
        environment = [args[i + 1] for i, arg in enumerate(args) if arg == "--env"]
        self.assertEqual(environment, ["NPM_CONFIG_CACHE=/tmp/npm-cache", "XDG_CACHE_HOME=/tmp/cache"])
        for forbidden in ["-v", "-e", "--env-file", "--privileged", "do-not-forward"]:
            self.assertNotIn(forbidden, args)

    def test_resume_project_with_spaces(self):
        project = self.root / "project with spaces"
        project.mkdir()
        args = self.run_launcher("--resume", "--project", str(project))
        self.assertEqual(args[-2:], ["resume", "--all"])
        mounts = [args[i + 1] for i, arg in enumerate(args) if arg == "--mount"]
        self.assertEqual(mounts, [
            "type=volume,source=agent-containers-codex-history,target=/home/node/codex-history",
            f"type=bind,source={project.resolve()},target=/app",
        ])
        self.assertIn("--read-only", args)

    def test_old_image_is_rebuilt(self):
        self.env["MOCK_IMAGE_LAYOUT"] = "0"
        self.run_launcher()
        self.assertEqual((self.root / "build").read_text().splitlines(),
                         ["-C", str(self.launcher.parent), "openai-codex", "CONTAINER_ENGINE=podman"])

    def test_cleanup_removes_only_history_without_building(self):
        args = self.run_launcher("--delete-history")
        self.assertEqual(args, ["volume", "rm", "agent-containers-codex-history"])
        self.assertFalse((self.root / "build").exists())


if __name__ == "__main__":
    unittest.main()
