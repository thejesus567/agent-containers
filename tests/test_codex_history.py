"""Offline Docker integration test: resume conversations without persisting auth."""

import subprocess
import textwrap
import unittest
import uuid


MOCK_SERVER = r'''
import http.server
import json
import pathlib

class Handler(http.server.BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def do_POST(self):
        self.rfile.read(int(self.headers.get("Content-Length", "0")))
        events = [
            {"type": "response.created", "response": {"id": "offline-response"}},
            {"type": "response.output_item.done", "item": {
                "id": "offline-message", "type": "message", "role": "assistant",
                "content": [{"type": "output_text", "text": "offline-test-answer"}]
            }},
            {"type": "response.completed", "response": {
                "id": "offline-response", "usage": {"input_tokens": 1, "output_tokens": 1, "total_tokens": 2}
            }},
        ]
        body = "".join("event: " + event["type"] + "\ndata: " + json.dumps(event) + "\n\n" for event in events).encode()
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

server = http.server.HTTPServer(("127.0.0.1", 8765), Handler)
pathlib.Path("/tmp/mock-ready").touch()
server.serve_forever()
'''


class HistoryPersistenceTest(unittest.TestCase):
    def test_resume_without_auth_files(self):
        suffix = uuid.uuid4().hex
        volume = "codex-history-test-" + suffix
        container_names = []

        def run_container(script):
            name = "codex-history-test-" + uuid.uuid4().hex
            container_names.append(name)
            result = subprocess.run(
                ["docker", "run", "--rm", "--interactive", "--name", name,
                 "--network=none", "--read-only", "--cap-drop=ALL",
                 "--security-opt=no-new-privileges",
                 "--tmpfs", "/tmp:rw,nosuid,nodev,mode=1777",
                 "--tmpfs", "/home/node/.codex:rw,nosuid,nodev,uid=1000,gid=1000,mode=0700",
                 "--mount", f"type=volume,source={volume},target=/home/node/codex-history",
                 "--entrypoint", "/bin/bash", "openai-codex", "-s"],
                input="set -euo pipefail\n" + script,
                text=True, capture_output=True, timeout=90,
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            return result

        def conversation(resume=False):
            command = "resume --last --all 'second-test-question'" if resume else "'first-test-question'"
            return (
                "test ! -e \"$CODEX_HOME/auth.json\"\n"
                "cat > /tmp/mock.py <<'SERVER'\n" + MOCK_SERVER + "\nSERVER\n"
                "python3 /tmp/mock.py &\n"
                "for attempt in {1..100}; do [[ -e /tmp/mock-ready ]] && break; sleep 0.05; done\n"
                "test -e /tmp/mock-ready\n"
                "/usr/local/bin/codex-entrypoint --sandbox danger-full-access -c 'model_provider=\"offline\"' "
                "-c 'model_providers.offline.name=\"Offline\"' "
                "-c 'model_providers.offline.base_url=\"http://127.0.0.1:8765/v1\"' "
                "-c 'model_providers.offline.wire_api=\"responses\"' "
                "-c 'model_providers.offline.requires_openai_auth=false' "
                "--model offline-test exec --skip-git-repo-check " + command + " < /dev/null\n"
            )

        try:
            first = run_container(conversation() + textwrap.dedent('''
                test ! -e "$CODEX_HOME/auth.json"
                printf 'temporary-test-marker' > "$CODEX_HOME/auth.json"
                printf 'temporary-test-marker' > "$CODEX_HOME/config-extra"
                test "$(readlink "$CODEX_HOME/sessions")" = /home/node/codex-history/sessions
                test -n "$(find /home/node/codex-history/sessions -name '*.jsonl' -print -quit)"
            '''))
            self.assertIn("offline-test-answer", first.stdout)
            second = run_container(conversation(resume=True) + textwrap.dedent('''
                test ! -e "$CODEX_HOME/auth.json"
                test ! -e "$CODEX_HOME/config-extra"
                python3 - <<'CHECK'
import pathlib
root = pathlib.Path('/home/node/codex-history')
files = list((root / 'sessions').rglob('*.jsonl'))
assert len(files) == 1, files
text = files[0].read_text()
assert 'first-test-question' in text
assert 'second-test-question' in text
assert 'offline-test-answer' in text
assert not list(root.rglob('auth.json'))
assert all('temporary-test-marker' not in p.read_text(errors='ignore') for p in root.rglob('*') if p.is_file())
CHECK
            '''))
            self.assertIn("offline-test-answer", second.stdout)
        finally:
            # Remove only containers and the volume created by this test.
            for name in container_names:
                subprocess.run(["docker", "rm", "--force", name], capture_output=True)
            subprocess.run(["docker", "volume", "rm", volume], capture_output=True, check=True)


if __name__ == "__main__":
    unittest.main()
