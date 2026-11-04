import argparse
import json
from pathlib import Path

def main():
    parser = argparse.ArgumentParser(description="Faro · analizador estático local de archivos")
    commands = parser.add_subparsers(dest="command")
    web = commands.add_parser("serve", help="Abrir la interfaz local")
    web.add_argument("--host", default="127.0.0.1")
    web.add_argument("--port", default=8765, type=int)
    scan = commands.add_parser("analyze", help="Analizar un archivo y obtener JSON")
    scan.add_argument("file", type=Path)
    args = parser.parse_args()
    if args.command == "analyze":
        from .service import isolated_analysis
        from .engine import MAX_BYTES
        try:
            with args.file.open("rb") as stream:
                data = stream.read(MAX_BYTES + 1)
            print(json.dumps(isolated_analysis(data, args.file.name), ensure_ascii=False, indent=2))
        except (OSError, ValueError, RuntimeError) as exc:
            parser.exit(2, f"Faro: {exc}\n")
    else:
        from .server import serve
        serve(getattr(args, "host", "127.0.0.1"), getattr(args, "port", 8765))

if __name__ == "__main__":
    main()
