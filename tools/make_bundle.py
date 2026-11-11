"""Package the bot for Optiver's browser VS Code ("Dev Environment"), three ways.

  python tools/make_bundle.py
    dist/optibook-bot.zip       drag into the VS Code file explorer, then: unzip optibook-bot.zip
    dist/install_paste.py       open it, copy ALL, paste into a new file in VS Code, run: python install_paste.py
                                (works even if uploads are blocked: it is plain text that unpacks itself)
See docs/DEPLOY.md for the full checklist.
"""
import base64
import io
import os
import zipfile

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INCLUDE = ["optisim", "strategies", "runlog", "tools", "ui", "tests", "docs", "run_live.py", "run_sim.py",
           "README.md", "requirements.txt"]
SKIP_DIRS = {"__pycache__", ".pytest_cache", "logs", "rounds", "notebooks", "dist"}


def files():
    for item in INCLUDE:
        p = os.path.join(BASE, item)
        if os.path.isfile(p):
            yield item
        elif os.path.isdir(p):
            for root, dirs, fs in os.walk(p):
                dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
                for f in fs:
                    if not f.endswith((".pyc", ".png")):
                        yield os.path.relpath(os.path.join(root, f), BASE)


def main():
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        for rel in sorted(files()):
            z.write(os.path.join(BASE, rel), os.path.join("optibook-bot", rel))
    data = buf.getvalue()
    os.makedirs(os.path.join(BASE, "dist"), exist_ok=True)
    with open(os.path.join(BASE, "dist", "optibook-bot.zip"), "wb") as f:
        f.write(data)
    b64 = base64.b64encode(data).decode()
    lines = [b64[k:k + 100] for k in range(0, len(b64), 100)]
    with open(os.path.join(BASE, "dist", "install_paste.py"), "w") as f:
        f.write('"""Self-unpacking copy of the bot. Run: python install_paste.py  -> creates ./optibook-bot/"""\n')
        f.write("import base64, io, zipfile\nDATA = (\n")
        for ln in lines:
            f.write(f'    "{ln}"\n')
        f.write(")\nzipfile.ZipFile(io.BytesIO(base64.b64decode(DATA))).extractall('.')\n")
        f.write("print('unpacked into ./optibook-bot  ->  cd optibook-bot && python tools/intro_exercises.py')\n")
    print(f"dist/optibook-bot.zip ({len(data) // 1024} KB), dist/install_paste.py ({len(b64) // 1024} KB of text)")


if __name__ == "__main__":
    main()
