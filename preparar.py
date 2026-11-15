"""Prepara el proyecto Android de Medu Netjer (lo usa GitHub Actions).

  python preparar.py web     -> crea proyecto/www con index.html y las fuentes descargadas (funciona sin internet)
  python preparar.py iconos  -> pone el icono y la pantalla de inicio en proyecto/android
"""
import os, re, sys, glob, json, urllib.request
from PIL import Image, ImageDraw

AZUL = (31, 59, 111)
UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36'


def descargar(url):
    req = urllib.request.Request(url, headers={'User-Agent': UA})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read()


def web():
    os.makedirs('proyecto/www/fuentes', exist_ok=True)
    html = open('index.html', encoding='utf-8').read()
    m = re.search(r'<link href="(https://fonts\.googleapis\.com/css2\?[^"]+)" rel="stylesheet">', html)
    if m:
        try:
            css = descargar(m.group(1).replace('&amp;', '&')).decode('utf-8')
            for i, url in enumerate(sorted(set(re.findall(r'url\((https://[^)]+)\)', css)))):
                nombre = f'f{i}.woff2'
                open(f'proyecto/www/fuentes/{nombre}', 'wb').write(descargar(url))
                css = css.replace(url, f'fuentes/{nombre}')
            open('proyecto/www/fuentes.css', 'w', encoding='utf-8').write(css)
            html = html.replace(m.group(0), '<link href="fuentes.css" rel="stylesheet">')
            html = re.sub(r'<link rel="preconnect"[^>]*>\n?', '', html)
            print('Fuentes incluidas en la app:', i + 1, 'archivos')
        except Exception as e:
            print('AVISO: no se pudieron descargar las fuentes; la app las cargará de internet.', e)
    open('proyecto/www/index.html', 'w', encoding='utf-8').write(html)
    if not os.path.exists('proyecto/package.json'):
        json.dump({'name': 'medu-netjer', 'version': '1.0.0', 'private': True}, open('proyecto/package.json', 'w'))


def iconos():
    res = 'proyecto/android/app/src/main/res'
    icono = Image.open('icon.png').convert('RGB')
    fondo = icono.getpixel((4, 4))
    tam = {'mdpi': 48, 'hdpi': 72, 'xhdpi': 96, 'xxhdpi': 144, 'xxxhdpi': 192}
    for dens, t in tam.items():
        carpeta = f'{res}/mipmap-{dens}'
        os.makedirs(carpeta, exist_ok=True)
        normal = icono.resize((t, t), Image.LANCZOS)
        normal.save(f'{carpeta}/ic_launcher.png')
        mascara = Image.new('L', (t * 4, t * 4), 0)
        ImageDraw.Draw(mascara).ellipse((0, 0, t * 4 - 1, t * 4 - 1), fill=255)
        redondo = Image.new('RGBA', (t, t), (0, 0, 0, 0))
        redondo.paste(normal, (0, 0), mascara.resize((t, t), Image.LANCZOS))
        redondo.save(f'{carpeta}/ic_launcher_round.png')
        # icono adaptativo: lienzo de 108 dp con el dibujo en la zona segura
        f = int(t * 108 / 48)
        frente = Image.new('RGB', (f, f), fondo)
        dentro = int(f * 0.70)
        frente.paste(icono.resize((dentro, dentro), Image.LANCZOS), ((f - dentro) // 2, (f - dentro) // 2))
        frente.save(f'{carpeta}/ic_launcher_foreground.png')
    os.makedirs(f'{res}/values', exist_ok=True)
    color = '#%02X%02X%02X' % fondo
    open(f'{res}/values/ic_launcher_background.xml', 'w').write(
        f'<?xml version="1.0" encoding="utf-8"?>\n<resources>\n    <color name="ic_launcher_background">{color}</color>\n</resources>\n')
    # pantalla de inicio: fondo azul con el icono en el centro
    for ruta in glob.glob(f'{res}/drawable*/splash.png'):
        w, h = Image.open(ruta).size
        lienzo = Image.new('RGB', (w, h), fondo)
        lado = int(min(w, h) * 0.45)
        lienzo.paste(icono.resize((lado, lado), Image.LANCZOS), ((w - lado) // 2, (h - lado) // 2))
        lienzo.save(ruta)
    print('Iconos y pantalla de inicio listos')


if __name__ == '__main__':
    {'web': web, 'iconos': iconos}[sys.argv[1]]()
