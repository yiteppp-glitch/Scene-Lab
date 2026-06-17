#!/usr/bin/env python3
import argparse
import json
import mimetypes
import os
from pathlib import Path
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from urllib import error, parse, request


TARGET_URL = "https://newapi.bananapro.top/v1beta/models/gemini-3.1-flash-image-preview:generateContent"
NPM_BASE_URL = "https://cdn.jsdelivr.net/npm/"
BG_REMOVAL_BASE_URL = "https://staticimgly.com/@imgly/background-removal-data/1.7.0/dist/"


class SceneLabHandler(SimpleHTTPRequestHandler):
    extensions_map = {
        **SimpleHTTPRequestHandler.extensions_map,
        ".js": "application/javascript",
        ".json": "application/json",
        ".webmanifest": "application/manifest+json",
    }

    def end_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization, api-key")
        path = self.path.split("?", 1)[0]
        if path.endswith((".html", ".js", ".json")) or path in {"/", "/sw.js"}:
            self.send_header("Cache-Control", "no-store, max-age=0")
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(204)
        self.end_headers()

    def do_GET(self):
        path = self.path.split("?", 1)[0]
        if path.startswith("/npm/"):
            self.proxy_asset(NPM_BASE_URL, path[len("/npm/") :])
            return
        if path.startswith("/bg-removal/"):
            self.proxy_asset(BG_REMOVAL_BASE_URL, path[len("/bg-removal/") :])
            return
        super().do_GET()

    def do_POST(self):
        if self.path.split("?", 1)[0] != "/api/generateContent":
            self.send_error(404, "Not Found")
            return

        length = int(self.headers.get("Content-Length", "0") or "0")
        body = self.rfile.read(length)
        api_key = self.headers.get("api-key", "").strip()
        auth = self.headers.get("Authorization", "").strip()
        if not auth and api_key:
            auth = f"Bearer {api_key}"

        upstream_headers = {"Content-Type": "application/json"}
        if auth:
            upstream_headers["Authorization"] = auth

        upstream_request = request.Request(
            TARGET_URL,
            data=body,
            headers=upstream_headers,
            method="POST",
        )

        try:
            with request.urlopen(upstream_request, timeout=240) as response:
                data = response.read()
                self.send_response(response.status)
                self.send_header("Content-Type", response.headers.get("Content-Type", "application/json"))
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)
        except error.HTTPError as exc:
            data = exc.read()
            self.send_response(exc.code)
            self.send_header("Content-Type", exc.headers.get("Content-Type", "application/json"))
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
        except Exception as exc:
            payload = json.dumps({"error": {"message": f"本地代理请求失败: {exc}"}}, ensure_ascii=False).encode("utf-8")
            self.send_response(502)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)

    def proxy_asset(self, base_url, asset_path):
        safe_path = "/".join(part for part in asset_path.split("/") if part and part not in {".", ".."})
        if not safe_path:
            self.send_error(404, "Not Found")
            return

        cache_root = Path(self.directory) / ".scene_lab_cache"
        cache_file = cache_root / parse.urlparse(base_url).netloc / safe_path
        try:
            if cache_file.exists():
                data = cache_file.read_bytes()
            else:
                url = parse.urljoin(base_url, safe_path)
                asset_request = request.Request(
                    url,
                    headers={
                        "User-Agent": "Mozilla/5.0 SceneLab/1.0",
                        "Accept": "*/*",
                    },
                )
                with request.urlopen(asset_request, timeout=120) as response:
                    data = response.read()
                cache_file.parent.mkdir(parents=True, exist_ok=True)
                cache_file.write_bytes(data)

            content_type = mimetypes.guess_type(safe_path)[0] or "application/octet-stream"
            if safe_path.endswith("+esm") or safe_path.endswith(".mjs"):
                content_type = "application/javascript"
            elif safe_path.endswith(".json"):
                content_type = "application/json"
            self.send_response(200)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(data)))
            self.send_header("Cache-Control", "public, max-age=31536000, immutable")
            self.end_headers()
            self.wfile.write(data)
        except error.HTTPError as exc:
            self.send_error(exc.code, exc.reason)
        except Exception as exc:
            self.send_error(502, f"Asset proxy failed: {exc}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=4177)
    parser.add_argument("--directory", default=os.path.dirname(os.path.abspath(__file__)))
    args = parser.parse_args()

    mimetypes.add_type("application/javascript", ".js")
    handler = lambda *handler_args, **handler_kwargs: SceneLabHandler(
        *handler_args,
        directory=args.directory,
        **handler_kwargs,
    )
    server = ThreadingHTTPServer((args.host, args.port), handler)
    print(f"Scene Lab intro: http://{args.host}:{args.port}/intro.html", flush=True)
    print(f"Scene Lab tool:  http://{args.host}:{args.port}/index.html", flush=True)
    server.serve_forever()


if __name__ == "__main__":
    main()
