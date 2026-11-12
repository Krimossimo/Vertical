"""Point d'entrée : `python -m vertical` (fenêtre de bureau) ou `python -m vertical --browser`."""
from __future__ import annotations

import argparse
import logging
import socket
import sys
import threading
import time
import urllib.request
import webbrowser
from logging.handlers import RotatingFileHandler

from .config import DATA_DIR


def setup_logging() -> None:
    fmt = logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s")
    root = logging.getLogger()
    root.setLevel(logging.INFO)
    fh = RotatingFileHandler(DATA_DIR / "vertical.log", maxBytes=2_000_000, backupCount=2, encoding="utf-8")
    fh.setFormatter(fmt)
    root.addHandler(fh)
    if sys.stderr:
        sh = logging.StreamHandler()
        sh.setFormatter(fmt)
        root.addHandler(sh)


def free_port(preferred: int = 8765) -> int:
    for port in [preferred] + list(range(preferred + 1, preferred + 30)):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(("127.0.0.1", port))
                return port
            except OSError:
                continue
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def _fix_std_streams() -> None:
    """Sous pythonw.exe (lancement sans console), stdout/stderr valent None :
    uvicorn et d'autres bibliothèques plantent dessus. On les redirige vers un fichier."""
    if sys.stdout is None or sys.stderr is None:
        f = open(DATA_DIR / "console.log", "a", encoding="utf-8", buffering=1)
        if sys.stdout is None:
            sys.stdout = f
        if sys.stderr is None:
            sys.stderr = f


def _crash(exc: BaseException) -> None:
    import traceback
    txt = "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))
    try:
        (DATA_DIR / "crash.log").write_text(txt, encoding="utf-8")
    except Exception:
        pass
    try:
        logging.getLogger("vertical").error("Plantage au démarrage :\n%s", txt)
    except Exception:
        pass
    if sys.platform == "win32":
        try:
            import ctypes
            ctypes.windll.user32.MessageBoxW(None, "Vertical n'a pas pu démarrer :\n\n" + str(exc)
                                             + "\n\nDétails dans data\\crash.log", "Vertical", 0x10)
        except Exception:
            pass


def main() -> None:
    _fix_std_streams()
    try:
        _main()
    except SystemExit:
        raise
    except BaseException as e:
        _crash(e)
        raise


def _main() -> None:
    ap = argparse.ArgumentParser(prog="vertical")
    ap.add_argument("--browser", action="store_true", help="ouvrir dans le navigateur au lieu d'une fenêtre")
    ap.add_argument("--port", type=int, default=0)
    ap.add_argument("--no-open", action="store_true")
    ap.add_argument("--check", action="store_true", help="afficher le diagnostic de l'environnement et quitter")
    args = ap.parse_args()
    setup_logging()
    log = logging.getLogger("vertical")
    log.info("Démarrage de Vertical (python %s)", sys.version.split()[0])

    if args.check:
        import json
        from . import env
        from .config import load_settings
        print(json.dumps(env.report(load_settings()), indent=2, ensure_ascii=False))
        return

    import uvicorn
    from . import server

    port = args.port or free_port()
    url = f"http://127.0.0.1:{port}/"
    config = uvicorn.Config(server.app, host="127.0.0.1", port=port, log_level="warning", access_log=False,
                            log_config=None)
    srv = uvicorn.Server(config)
    th = threading.Thread(target=srv.run, daemon=True)
    th.start()
    for _ in range(100):
        try:
            urllib.request.urlopen(url + "api/projects", timeout=0.5)
            break
        except Exception:
            time.sleep(0.1)
    log.info("Vertical prêt sur %s", url)
    server.warm_env()

    if args.no_open:
        th.join()
        return
    if not args.browser:
        try:
            import webview
            win = webview.create_window("Vertical", url, width=1440, height=920,
                                        min_size=(1100, 700), background_color="#0A0B0F")
            server.WINDOW = win
            webview.start(private_mode=False)
            srv.should_exit = True
            return
        except Exception as e:  # WebView2 absent, etc. → navigateur par défaut
            log.warning("Fenêtre native indisponible (%s) : ouverture dans le navigateur.", e)
            server.WINDOW = None
    webbrowser.open(url)
    print(f"Vertical tourne sur {url} — ferme cette fenêtre pour quitter.")
    try:
        while th.is_alive():
            time.sleep(1)
    except KeyboardInterrupt:
        srv.should_exit = True


if __name__ == "__main__":
    main()
