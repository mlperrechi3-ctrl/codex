"""Run Caxy in a browser using the user's extracted game files. Python 3.10+."""
import argparse
import json
import os
from pathlib import Path
import re
import shutil
import threading
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlsplit, unquote
from urllib.request import urlopen
import webbrowser

REV = 'c86992b3533095ce95ed6d9157bcf81faeabf2c6'
BASE = f'https://raw.githubusercontent.com/chkuendig/scummvm-demo/{REV}/'
PREFIX = 'data/games/Caxy'
AUDIO_GATE = '<div id="caxyGate" style="position:fixed;inset:0;z-index:100;display:grid;place-content:center;text-align:center;background:#100c21;color:#f9f4eb;font-family:system-ui;padding:25px"><h1 style="color:#ffd455">Caxy Gambá</h1><p>Clique para começar a introdução com som.</p><button id="caxyBegin" style="padding:15px 28px;border:0;border-radius:10px;background:#ffd455;font:inherit;cursor:pointer">Começar com som</button></div><button onclick="enableCaxySound()" style="position:fixed;right:12px;top:12px;z-index:99;padding:8px 12px;border-radius:8px;cursor:pointer">Ativar som</button><script>const caxyAudioContexts=new Set();\nfunction prepareCaxySound(){\n const Native=window.AudioContext||window.webkitAudioContext;\n if(!Native)return;\n const prepared=new Native();\n caxyAudioContexts.add(prepared);\n prepared.resume().catch(console.warn);\n let available=true;\n const Wrapped=new Proxy(Native,{construct(Target,args){\n  const context=available?(available=false,prepared):Reflect.construct(Target,args);\n  caxyAudioContexts.add(context);return context;\n }});\n window.AudioContext=Wrapped;\n if(window.webkitAudioContext)window.webkitAudioContext=Wrapped;\n}\nfunction enableCaxySound(){\n for(const context of caxyAudioContexts)if(context.state!==\'closed\')context.resume().catch(console.warn);\n document.getElementById(\'canvas\')?.focus();\n}\ndocument.getElementById(\'caxyBegin\').onclick=()=>{prepareCaxySound();document.getElementById(\'caxyGate\').remove();const script=document.createElement(\'script\');script.src=\'scummvm.js\';document.body.appendChild(script);};</script>'

def main():
    ap = argparse.ArgumentParser(description='Abre Caxy Gamba no navegador usando a pasta extraida do jogo.')
    ap.add_argument('pasta', nargs='?', help='Pasta que contem MONSTRO.EXE e MONSTRO.CXT')
    ap.add_argument('--port', type=int, default=8000)
    ap.add_argument('--no-browser', action='store_true')
    args = ap.parse_args()
    if not args.pasta:
        import tkinter as tk
        from tkinter.filedialog import askdirectory
        window = tk.Tk()
        window.withdraw()
        args.pasta = askdirectory(title='Selecione a pasta extraida do Caxy (com MONSTRO.EXE)')
        window.destroy()
        if not args.pasta:
            return
    source = Path(args.pasta).expanduser().resolve()
    if not (source / 'MONSTRO.EXE').is_file() and (source / 'Caxy').is_dir():
        source /= 'Caxy'
    for name in ['MONSTRO.EXE', 'MONSTRO.CXT', 'MENU.DXR', 'BASICA81.DXR']:
        if not (source / name).is_file():
            ap.error(f'Arquivo {name} nao encontrado em {source}. Extraia o RAR primeiro.')
    root = Path(__file__).resolve().parent / 'caxy-runtime-web'
    root.mkdir(exist_ok=True)
    files = ['scummvm.js', 'scummvm.wasm', 'scummvm.html', 'logo.svg',
             'COPYING', 'COPYRIGHT', 'AUTHORS', 'build-info.json',
             'data/plugins/libdirector.so', 'data/fonts.dat', 'data/encoding.dat',
             'data/classicmacfonts.dat', 'data/translations.dat',
             'data/scummmodern.zip', 'data/scummclassic.zip']
    for name in files:
        target = root / name
        if target.is_file() and target.stat().st_size:
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        print(f'Baixando runtime: {name}', flush=True)
        tmp = target.with_name(target.name + '.partial')
        with urlopen(BASE + name, timeout=120) as response, tmp.open('wb') as out:
            shutil.copyfileobj(response, out)
        tmp.replace(target)
    html = (root / 'scummvm.html').read_text()
    html = html.replace('<title>ScummVM</title>', '<title>Caxy Gamba</title>')
    launch = '#--config=/scummvm.ini --path=/data/games/Caxy --extrapath=/data --gfx-mode=surfacesdl director:director'
    html = html.replace('<script async type="text/javascript" src="scummvm.js"></script>',
        f'<script>if(!location.hash)history.replaceState(null,"",{json.dumps(launch)});</script><script async src="scummvm.js"></script>')
    html = html.replace('<script async src="scummvm.js"></script>', AUDIO_GATE)
    (root / 'index.html').write_text(html)
    (root / 'scummvm.ini').write_text('[scummvm]\npluginspath=/data/plugins\nextrapath=/data\ngfx_mode=surfacesdl\nfullscreen=false\n')
    def game_index(directory, relative=Path()):
        entries = {}
        for child in directory.iterdir():
            if child.name in {'index.json', 'MONSTRO3.EXE', 'MONSTRO.DIR'}:
                continue
            if child.is_dir():
                entries[child.name] = {}
                game_index(child, relative / child.name)
            elif child.is_file():
                entries[child.name] = child.stat().st_size
        if relative == Path():
            entries['MONSTRO.DIR'] = (source / 'MONSTRO.CXT').stat().st_size
        destination = root / PREFIX / relative
        destination.mkdir(parents=True, exist_ok=True)
        (destination / 'index.json').write_text(json.dumps(entries))
    game_index(source)
    def runtime_index(directory):
        entries = {}
        for child in directory.iterdir():
            if child.name == 'index.json':
                continue
            if child.is_dir():
                entries[child.name] = {}
                if not child.is_relative_to(root / PREFIX):
                    runtime_index(child)
            elif child.is_file():
                entries[child.name] = child.stat().st_size
        (directory / 'index.json').write_text(json.dumps(entries))
    runtime_index(root / 'data')
    class Handler(SimpleHTTPRequestHandler):
        def translate_path(self, path):
            relative = unquote(urlsplit(path).path).lstrip('/')
            if relative.startswith(PREFIX + '/') and not relative.endswith('/index.json'):
                suffix = relative[len(PREFIX) + 1:]
                if suffix == 'MONSTRO.DIR':
                    suffix = 'MONSTRO.CXT'
                result = (source / suffix).resolve()
                if result.is_relative_to(source):
                    return str(result)
            return super().translate_path(path)
        def send_head(self):
            self.remaining = None
            path = self.translate_path(self.path)
            match = re.fullmatch(r'bytes=(\d+)-(\d*)', self.headers.get('Range', ''))
            if not match or not os.path.isfile(path):
                return super().send_head()
            f = open(path, 'rb')
            size = os.fstat(f.fileno()).st_size
            start = int(match[1])
            end = min(int(match[2]) if match[2] else size - 1, size - 1)
            if start > end or start >= size:
                f.close()
                self.send_error(416)
                return None
            self.send_response(206)
            self.send_header('Content-Type', self.guess_type(path))
            self.send_header('Content-Range', f'bytes {start}-{end}/{size}')
            self.send_header('Accept-Ranges', 'bytes')
            self.send_header('Content-Length', str(end - start + 1))
            self.end_headers()
            f.seek(start)
            self.remaining = end - start + 1
            return f
        def copyfile(self, src, dst):
            if self.remaining is None:
                return shutil.copyfileobj(src, dst)
            while self.remaining:
                chunk = src.read(min(65536, self.remaining))
                if not chunk:
                    break
                dst.write(chunk)
                self.remaining -= len(chunk)
        def log_message(self, *args):
            pass
    os.chdir(root)
    server = ThreadingHTTPServer(('127.0.0.1', args.port), Handler)
    url = f'http://localhost:{args.port}/'
    print(f'Abra {url} no Chrome ou Edge. Mantenha esta janela aberta.', flush=True)
    if not args.no_browser:
        threading.Timer(0.5, lambda: webbrowser.open(url)).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()

if __name__ == '__main__':
    main()
