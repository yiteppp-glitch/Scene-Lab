# Scene Lab

Scene Lab 产品场景图工具。

## 本地启动

双击 `一键启动-Mac.command`，默认打开介绍页：

```text
http://127.0.0.1:4178/intro.html
```

也可以手动运行：

```bash
python3 scene_lab_server.py --host 127.0.0.1 --port 4178 --directory .
```

## GitHub Pages

GitHub Pages 可以打开静态介绍页：

```text
https://<你的用户名>.github.io/<仓库名>/intro.html
```

完整生图工具需要 `scene_lab_server.py` 代理服务。只用 GitHub Pages 无法运行 `/api/generateContent`。

## 公网完整运行

要完整生图，请把这个仓库部署到 Render / Railway / VPS 等能运行 Python 的服务。

启动命令：

```bash
python3 scene_lab_server.py --host 0.0.0.0 --port $PORT --directory .
```

