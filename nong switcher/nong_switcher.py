import os
import re
import shutil
import subprocess
import urllib.request

CARPETA = os.path.join(os.environ["LOCALAPPDATA"], "GeometryDash")

os.system("cls")

def comprobar_programa(nombre, winget_id):
    """Si el programa no está instalado, ofrece instalarlo."""
    if shutil.which(nombre) is None:
        resp = input(f"{nombre} not found. do you want to install it? (y/n): ").lower()
        if resp == "y":
            subprocess.run(["winget", "install", winget_id])
            print("Installed. Close and reopen this script so Windows detects it.")
        else:
            print("ok brochacho")
        input("Press Enter to exit...")
        raise SystemExit

def sacar_id_youtube(texto):
    texto = texto.strip()
    m = re.search(r"(?:youtu\.be/|v=|shorts/|embed/)([A-Za-z0-9_-]{11})", texto)
    if m:
        return m.group(1)
    if re.fullmatch(r"[A-Za-z0-9_-]{11}", texto):
        return texto
    return None


def sacar_id_newgrounds(texto):
    texto = texto.strip()
    m = re.search(r"newgrounds\.com/(?:audio/listen|portal/view)/(\d+)", texto)
    if m:
        return m.group(1)
    if texto.isdigit():
        return texto
    return None


def normalizar_url(texto):
    """Devuelve una URL válida para yt-dlp: cualquier sitio, o un ID suelto de YouTube."""
    texto = texto.strip().strip('"').strip("'")
    if not texto:
        return None

    # Enlaces de YouTube: limpiar ?si=, &feature=, etc.
    if "youtu" in texto:
        yt = sacar_id_youtube(texto)
        if yt:
            return "https://www.youtube.com/watch?v=" + yt

    # ID suelto de YouTube (11 caracteres)
    if re.fullmatch(r"[A-Za-z0-9_-]{11}", texto):
        return "https://www.youtube.com/watch?v=" + texto

    # Cualquier otro sitio: dejar el enlace tal cual (añadiendo https:// si falta)
    if texto.startswith(("http://", "https://")):
        return texto
    if "." in texto and " " not in texto:
        return "https://" + texto

    return None


def restaurar_cancion():
    ng = sacar_id_newgrounds(input("Newgrounds song id (or link) to restore: "))
    if ng is None:
        print("No pude sacar el ID de Newgrounds de eso.")
        return

    url = "https://www.newgrounds.com/audio/download/" + ng
    original = os.path.join(CARPETA, ng + ".download.tmp")
    convertido = os.path.join(CARPETA, ng + ".convert.tmp")
    destino = os.path.join(CARPETA, ng + ".mp3")
    sobrante = os.path.join(CARPETA, ng + ".ogg")

    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    try:
        with urllib.request.urlopen(req) as r, open(original, "wb") as f:
            shutil.copyfileobj(r, f)

        res = subprocess.run([
            "ffmpeg", "-y", "-i", original,
            "-vn", "-c:a", "libvorbis", "-q:a", "5",
            "-f", "ogg", convertido,
        ])
        if res.returncode != 0:
            raise RuntimeError("ffmpeg falló al convertir")

        os.replace(convertido, destino)  # pisa el <id>.mp3 existente
        if os.path.exists(sobrante):
            os.remove(sobrante)  # borra el .ogg suelto de pruebas anteriores
        print("Restored", ng + ".mp3 (vorbis)")
    except Exception as e:
        print("No se pudo restaurar:", e)
    finally:
        for tmp in (original, convertido):
            if os.path.exists(tmp):
                os.remove(tmp)


def reemplazar_cancion():
    url = normalizar_url(input("Link of the song to download (YouTube, SoundCloud, any site yt-dlp supports): "))
    if url is None:
        print("Eso no parece un enlace ni un ID de YouTube.")
        return
    nombre = input("Geometry Dash song number (the file will be saved as <number>.mp3): ").strip()
    if not nombre:
        print("Tienes que escribir un número.")
        return

    res = subprocess.run([
        "yt-dlp",
        "-x", "--audio-format", "mp3",
        "--no-playlist",
        "--force-overwrites",
        "-P", CARPETA,
        "-o", nombre + ".%(ext)s",
        url,
    ])
    if res.returncode == 0:
        print("Replaced", nombre + ".mp3")
    else:
        print("yt-dlp falló.")

comprobar_programa("yt-dlp", "yt-dlp.yt-dlp")
comprobar_programa("ffmpeg", "Gyan.FFmpeg")

while True:
    print("")
    print("1) Restore a song")
    print("2) Replace a song")
    print("3) Exit")
    print(" ")
    opcion = input("Choose an option: ").strip()

    if opcion == "1":
        restaurar_cancion()
        input("\nPress Enter to continue...")
        os.system("cls")
    elif opcion == "2":
        reemplazar_cancion()
        input("\nPress Enter to continue...")
        os.system("cls")
    elif opcion == "3":
        break
    else:
        print("Opción no válida.")