#!/usr/bin/env python3
"""Setup wizard -- single GUI to configure and test the FOMO backend."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import threading
import webbrowser
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from urllib.parse import urlparse

HOST = "127.0.0.1"
PORT = 9876
BACKEND_DIR = Path(__file__).parent / "backend"
ENV_FILE = BACKEND_DIR / ".env"

HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>FOMO Backend Setup</title>
<style>
  *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
  body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, sans-serif;
    background: #f4f5f7; color: #1a1a2e; line-height: 1.5; padding: 2rem 1rem;
  }
  .container { max-width: 720px; margin: 0 auto; }
  h1 { font-size: 1.5rem; font-weight: 600; margin-bottom: 0.25rem; }
  p.subtitle { color: #6b7280; font-size: 0.875rem; margin-bottom: 1.5rem; }
  .card {
    background: #fff; border-radius: 12px; box-shadow: 0 1px 3px rgba(0,0,0,0.08);
    padding: 1.5rem; margin-bottom: 1rem;
  }
  .card h2 { font-size: 1rem; font-weight: 600; margin-bottom: 1rem; padding-bottom: 0.5rem; border-bottom: 1px solid #e5e7eb; }
  .field { margin-bottom: 0.875rem; }
  .field label { display: block; font-size: 0.8125rem; font-weight: 500; color: #374151; margin-bottom: 0.25rem; }
  .field input, .field textarea {
    width: 100%; padding: 0.5rem 0.75rem; font-size: 0.875rem;
    border: 1px solid #d1d5db; border-radius: 8px; outline: none;
    transition: border-color 0.15s, box-shadow 0.15s;
    font-family: inherit;
  }
  .field input:focus, .field textarea:focus { border-color: #6366f1; box-shadow: 0 0 0 3px rgba(99,102,241,0.15); }
  .field textarea { resize: vertical; min-height: 60px; font-family: 'SF Mono', 'Fira Code', monospace; font-size: 0.8125rem; }
  .btn-row { display: flex; gap: 0.75rem; flex-wrap: wrap; margin-top: 1rem; }
  .btn {
    display: inline-flex; align-items: center; gap: 0.375rem;
    padding: 0.625rem 1.25rem; font-size: 0.875rem; font-weight: 500;
    border: none; border-radius: 8px; cursor: pointer; transition: opacity 0.15s;
  }
  .btn:disabled { opacity: 0.5; cursor: not-allowed; }
  .btn-primary { background: #6366f1; color: #fff; }
  .btn-primary:hover:not(:disabled) { background: #4f46e5; }
  .btn-secondary { background: #e5e7eb; color: #374151; }
  .btn-secondary:hover:not(:disabled) { background: #d1d5db; }
  .btn-success { background: #059669; color: #fff; }
  .btn-danger { background: #dc2626; color: #fff; }
  #log {
    background: #1e1e2e; color: #cdd6f4; font-family: 'SF Mono', 'Fira Code', monospace;
    font-size: 0.8125rem; padding: 1rem; border-radius: 8px; max-height: 400px;
    overflow-y: auto; white-space: pre-wrap; word-break: break-all; margin-top: 0.75rem; display: none;
  }
  #log .info { color: #89b4fa; }
  #log .ok { color: #a6e3a1; }
  #log .err { color: #f38ba8; }
  #progress-bar {
    height: 4px; background: #e5e7eb; border-radius: 2px; margin-top: 0.75rem; overflow: hidden; display: none;
  }
  #progress-bar div {
    height: 100%; width: 0%; background: #6366f1; border-radius: 2px; transition: width 0.3s;
  }
  .badge {
    display: inline-block; font-size: 0.75rem; font-weight: 500; padding: 0.125rem 0.5rem;
    border-radius: 999px; margin-left: 0.5rem;
  }
  .badge-ready { background: #d1fae5; color: #065f46; }
  .badge-pending { background: #fef3c7; color: #92400e; }
  .badge-error { background: #fce4ec; color: #c62828; }
  .flex-between { display: flex; justify-content: space-between; align-items: center; }
  @media (max-width: 600px) { body { padding: 1rem 0.5rem; } .card { padding: 1rem; } }
</style>
</head>
<body>
<div class="container">
  <div class="flex-between">
    <div>
      <h1>FOMO Backend Setup</h1>
      <p class="subtitle">Configure API keys and run the collection pipeline</p>
    </div>
    <div id="env-status">
      <span id="env-badge" class="badge badge-pending">not saved</span>
    </div>
  </div>

  <div class="card" style="background:#fef3c7;border:1px solid #f59e0b;">
    <p style="font-size:0.8125rem;color:#92400e;">
      Before running the pipeline, open your Supabase SQL Editor and run the migration from
      <code style="background:#fff3cd;padding:0.125rem 0.375rem;border-radius:4px;">supabase/001_schema.sql</code>
      to create all database tables.
    </p>
  </div>

  <div class="card">
    <h2>Supabase</h2>
    <div class="field">
      <label for="SUPABASE_URL">Project URL</label>
      <input id="SUPABASE_URL" placeholder="https://your-project.supabase.co" value="">
    </div>
    <div class="field">
      <label for="SUPABASE_KEY">Service Role Key</label>
      <input id="SUPABASE_KEY" placeholder="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." value="">
    </div>
  </div>

  <div class="card">
    <h2>Groq (LLM scoring)</h2>
    <div class="field">
      <label for="GROQ_API_KEY">API Key</label>
      <input id="GROQ_API_KEY" placeholder="gsk_your_groq_key" value="">
    </div>
  </div>

  <div class="card">
    <h2>Reddit</h2>
    <div class="field">
      <label for="REDDIT_CLIENT_ID">Client ID</label>
      <input id="REDDIT_CLIENT_ID" placeholder="your_client_id" value="">
    </div>
    <div class="field">
      <label for="REDDIT_CLIENT_SECRET">Client Secret</label>
      <input id="REDDIT_CLIENT_SECRET" placeholder="your_client_secret" value="">
    </div>
  </div>

  <div class="card">
    <h2>YouTube</h2>
    <div class="field">
      <label for="YOUTUBE_API_KEY">API Key</label>
      <input id="YOUTUBE_API_KEY" placeholder="your_youtube_api_key" value="">
    </div>
  </div>

  <div class="btn-row">
    <button class="btn btn-primary" id="btn-save" onclick="saveEnv()">Save Keys</button>
    <button class="btn btn-success" id="btn-run" onclick="runPipeline()" disabled>Run Collection</button>
  </div>

  <div id="progress-bar"><div id="progress-fill"></div></div>
  <div id="log"></div>
</div>

<script>
const fields = ['SUPABASE_URL','SUPABASE_KEY','GROQ_API_KEY','REDDIT_CLIENT_ID','REDDIT_CLIENT_SECRET','YOUTUBE_API_KEY'];

async function saveEnv() {
  const btn = document.getElementById('btn-save');
  btn.disabled = true; btn.textContent = 'Saving...';
  const data = {};
  fields.forEach(f => data[f] = document.getElementById(f).value.trim());
  try {
    const r = await fetch('/api/save-env', { method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(data) });
    const res = await r.json();
    if (res.ok) {
      document.getElementById('env-badge').textContent = 'saved';
      document.getElementById('env-badge').className = 'badge badge-ready';
      document.getElementById('btn-run').disabled = false;
      log('Environment saved successfully', 'ok');
    } else {
      log('Failed to save environment: ' + (res.error || 'unknown'), 'err');
    }
  } catch(e) {
    log('Error saving: ' + e.message, 'err');
  }
  btn.disabled = false; btn.textContent = 'Save Keys';
}

async function runPipeline() {
  const btn = document.getElementById('btn-run');
  btn.disabled = true; btn.textContent = 'Running...';
  const bar = document.getElementById('progress-bar');
  const fill = document.getElementById('progress-fill');
  bar.style.display = 'block'; fill.style.width = '0%';

  log('Step 1/3: Running collector...', 'info');
  fill.style.width = '33%';
  let r = await fetch('/api/run-collector', { method:'POST' });
  let res = await r.json();
  if (res.ok) log('Collector done: ' + (res.result || 'ok'), 'ok'); else log('Collector: ' + (res.error || 'failed'), 'err');

  log('Step 2/3: Running filter...', 'info');
  fill.style.width = '66%';
  r = await fetch('/api/run-filter', { method:'POST' });
  res = await r.json();
  if (res.ok) log('Filter done: ' + (res.result || 'ok'), 'ok'); else log('Filter: ' + (res.error || 'failed'), 'err');

  fill.style.width = '100%';
  log('Step 3/3: Pipeline complete', 'ok');
  log('Verify data in your Supabase dashboard -> Table Editor -> items', 'info');
  btn.disabled = false; btn.textContent = 'Run Again';
  setTimeout(() => { bar.style.display = 'none'; fill.style.width = '0%'; }, 2000);
}

function log(msg, cls = 'info') {
  const el = document.getElementById('log');
  el.style.display = 'block';
  const ts = new Date().toLocaleTimeString();
  el.innerHTML += `<span class="${cls}">[${ts}] ${msg}</span>\n`;
  el.scrollTop = el.scrollHeight;
}
</script>
</body>
</html>"""


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == "/":
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(HTML.encode("utf-8"))
        else:
            self.send_error(404)

    def do_POST(self):
        parsed = urlparse(self.path)
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length).decode("utf-8") if length else "{}"
        data = json.loads(body) if body else {}

        if parsed.path == "/api/save-env":
            self._handle_save_env(data)
        elif parsed.path == "/api/run-collector":
            self._handle_run_script("collector.py")
        elif parsed.path == "/api/run-filter":
            self._handle_run_script("filter.py")
        else:
            self._json(404, {"ok": False, "error": "not found"})

    def _json(self, status, data):
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode("utf-8"))

    def _handle_save_env(self, data):
        required = ["SUPABASE_URL", "SUPABASE_KEY", "GROQ_API_KEY"]
        missing = [k for k in required if not data.get(k, "").strip()]
        if missing:
            return self._json(400, {"ok": False, "error": f"Missing: {', '.join(missing)}"})
        lines = [f"{k}={data.get(k, '')}" for k in data]
        ENV_FILE.parent.mkdir(parents=True, exist_ok=True)
        ENV_FILE.write_text("\n".join(lines) + "\n", encoding="utf-8")
        os.environ.update({k: data.get(k, "") for k in data})
        self._json(200, {"ok": True})

    def _handle_run_script(self, script_name):
        if not ENV_FILE.exists():
            return self._json(400, {"ok": False, "error": "Save .env first"})
        try:
            env = self._load_env()
            full_env = {**os.environ, **env}
            result = subprocess.run(
                [sys.executable, str(BACKEND_DIR / script_name)],
                capture_output=True, text=True, timeout=120, env=full_env,
                cwd=str(BACKEND_DIR),
            )
            output = result.stdout + result.stderr
            ok = result.returncode == 0
            self._json(200, {"ok": ok, "result": output[:2000]})
        except subprocess.TimeoutExpired:
            self._json(200, {"ok": False, "error": "timed out after 120s"})
        except Exception as e:
            self._json(500, {"ok": False, "error": str(e)})

    def _load_env(self):
        env = {}
        if ENV_FILE.exists():
            for line in ENV_FILE.read_text("utf-8").strip().splitlines():
                if "=" in line:
                    k, _, v = line.partition("=")
                    env[k.strip()] = v.strip()
        return env

    def log_message(self, *a):
        pass


def main():
    server = HTTPServer((HOST, PORT), Handler)
    webbrowser.open(f"http://{HOST}:{PORT}")
    print(f"Setup wizard at http://{HOST}:{PORT}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.shutdown()


if __name__ == "__main__":
    main()
