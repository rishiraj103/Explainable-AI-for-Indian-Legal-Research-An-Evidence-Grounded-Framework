"""Serve only the Week 16 static demo and its three frozen input artifacts."""
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import argparse

ROOT = Path(__file__).resolve().parents[1]
ALLOWED = {
    '/demo/': ('demo/index.html', 'text/html'),
    '/demo/style.css': ('demo/style.css', 'text/css'),
    '/demo/app.mjs': ('demo/app.mjs', 'text/javascript'),
    '/demo/data.mjs': ('demo/data.mjs', 'text/javascript'),
    '/artifacts/week13_review_packet.md': ('artifacts/week13_review_packet.md', 'text/plain'),
    '/artifacts/week11_temporal_prerank_evaluation.json': ('artifacts/week11_temporal_prerank_evaluation.json', 'application/json'),
    '/artifacts/week13_rq3_ablation_parity.json': ('artifacts/week13_rq3_ablation_parity.json', 'application/json'),
}


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        path = self.path.split('?', 1)[0]
        if path == '/':
            self.send_response(302)
            self.send_header('Location', '/demo/')
            self.end_headers()
            return
        if path not in ALLOWED:
            self.send_error(404)
            return
        file, mime = ALLOWED[path]
        try:
            data = (ROOT / file).read_bytes()
        except FileNotFoundError:
            self.send_error(404)
            return
        self.send_response(200)
        self.send_header('Content-Type', mime + '; charset=utf-8')
        self.send_header('Content-Length', str(len(data)))
        self.end_headers()
        self.wfile.write(data)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port', type=int, default=8000)
    args = parser.parse_args()
    print(f'Week 16 demo: http://127.0.0.1:{args.port}/', flush=True)
    ThreadingHTTPServer(('127.0.0.1', args.port), Handler).serve_forever()
