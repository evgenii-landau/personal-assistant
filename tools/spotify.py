import os
import logging
import spotipy
from spotipy.oauth2 import SpotifyOAuth

logger = logging.getLogger(__name__)

SCOPE = "user-modify-playback-state user-read-playback-state user-read-currently-playing streaming user-read-email user-read-private"

def get_client():
    return spotipy.Spotify(auth_manager=SpotifyOAuth(
        client_id=os.getenv("SPOTIFY_CLIENT_ID"),
        client_secret=os.getenv("SPOTIFY_CLIENT_SECRET"),
        redirect_uri="https://example.com/callback",
        scope=SCOPE,
        open_browser=False
    ))

def get_active_device_id(sp):
    devices = sp.devices()
    for d in devices.get("devices", []):
        if d["is_active"]:
            return d["id"]
    all_devices = devices.get("devices", [])
    if all_devices:
        return all_devices[0]["id"]
    return None

async def handle_spotify_command(command: str) -> str:
    try:
        sp = get_client()
        cmd = command.lower()
        device_id = get_active_device_id(sp)

        if not device_id:
            return "❌ Spotify не найден. Открой Spotify на Mac."

        if any(w in cmd for w in ["пауза", "pause", "стоп", "stop", "останови"]):
            sp.pause_playback(device_id=device_id)
            return "⏸️ Поставил на паузу."

        if any(w in cmd for w in ["продолжи", "resume", "возобнови"]):
            sp.start_playback(device_id=device_id)
            return "▶️ Продолжаю воспроизведение."

        if any(w in cmd for w in ["следующий", "next", "дальше", "скип", "пропусти"]):
            sp.next_track(device_id=device_id)
            return "⏭️ Следующий трек."

        if any(w in cmd for w in ["предыдущий", "previous", "назад", "прошлый"]):
            sp.previous_track(device_id=device_id)
            return "⏮️ Предыдущий трек."

        if any(w in cmd for w in ["что играет", "сейчас играет", "какой трек", "что за песня", "что за музыка"]):
            current = sp.current_playback()
            if current and current.get("item"):
                track = current["item"]
                artist = track["artists"][0]["name"]
                name = track["name"]
                return f"🎵 Сейчас играет: **{artist} — {name}**"
            return "🔇 Ничего не играет."

        if any(w in cmd for w in ["громче", "тише", "громкость"]):
            current = sp.current_playback()
            vol = current["device"]["volume_percent"] if current else 50
            if "громче" in cmd:
                new_vol = min(100, vol + 20)
            else:
                new_vol = max(0, vol - 20)
            sp.volume(new_vol, device_id=device_id)
            return f"🔊 Громкость: {new_vol}%"

        if any(w in cmd for w in ["мой плейлист", "my playlist", "мои плейлисты"]):
            playlists = sp.current_user_playlists(limit=10)
            items = playlists.get("items", [])
            if not items:
                return "❌ Плейлисты не найдены."
            stop = ["мой", "плейлист", "включи", "поставь", "играй", "spotify"]
            words = [w for w in cmd.split() if w not in stop and len(w) > 2]
            for item in items:
                if any(w in item["name"].lower() for w in words):
                    sp.start_playback(device_id=device_id, context_uri=item["uri"])
                    return f"🎵 Включаю плейлист **{item['name']}**"
            first = items[0]
            sp.start_playback(device_id=device_id, context_uri=first["uri"])
            return f"🎵 Включаю плейлист **{first['name']}**"

        genre_map = {
            "джаз": "jazz", "рок": "rock", "поп": "pop",
            "классика": "classical", "хип-хоп": "hip hop",
            "электронн": "electronic", "лаунж": "lounge",
            "реггетон": "reggaeton", "блюз": "blues", "соул": "soul",
            "рэп": "rap", "метал": "metal", "кантри": "country",
        }

        for word, genre in genre_map.items():
            if word in cmd:
                results = sp.search(q=genre, type="playlist", limit=10)
                playlists = results["playlists"]["items"]
                spotify_pl = [p for p in playlists if p["owner"]["id"] == "spotify"]
                target = spotify_pl[0] if spotify_pl else (playlists[0] if playlists else None)
                if target:
                    sp.start_playback(device_id=device_id, context_uri=target["uri"])
                    return f"🎵 Включаю **{target['name']}**"

        stop_words = ["включи", "поставь", "играй", "запусти", "spotify",
                      "спотифай", "музыку", "музыка", "песню", "трек", "поставь"]
        search_words = [w for w in cmd.split() if w not in stop_words and len(w) > 1]
        search_query = " ".join(search_words)

        if search_query:
            results = sp.search(q=search_query, type="artist", limit=1)
            artists = results["artists"]["items"]
            if artists:
                artist = artists[0]
                top_tracks = sp.artist_top_tracks(artist["id"], country="US")
                tracks = top_tracks.get("tracks", [])
                if tracks:
                    uris = [t["uri"] for t in tracks[:10]]
                    sp.start_playback(device_id=device_id, uris=uris)
                    return f"🎵 Включаю топ треки **{artist['name']}**"

            results = sp.search(q=search_query, type="track", limit=1)
            tracks = results["tracks"]["items"]
            if tracks:
                track = tracks[0]
                artist_name = track["artists"][0]["name"]
                sp.start_playback(device_id=device_id, uris=[track["uri"]])
                return f"🎵 Включаю: **{artist_name} — {track['name']}**"

        return "❌ Не понял что включить. Попробуй: 'включи ASAP Rocky' или 'включи джаз'"

    except spotipy.exceptions.SpotifyException as e:
        logger.error(f"Spotify ошибка: {e}")
        if "NO_ACTIVE_DEVICE" in str(e):
            return "❌ Открой Spotify на Mac и начни воспроизведение вручную."
        return f"❌ Ошибка Spotify: {str(e)}"
    except Exception as e:
        logger.error(f"Ошибка: {e}", exc_info=True)
        return f"❌ Ошибка: {str(e)}"

def is_spotify_command(text: str) -> bool:
    keywords = [
        "spotify", "спотифай", "музык", "включи", "поставь", "играй",
        "пауза", "стоп", "следующий", "предыдущий", "громче", "тише",
        "что играет", "сейчас играет", "какой трек", "что за песня",
        "плейлист", "джаз", "рок", "поп", "рэп", "хип-хоп", "классика",
        "скип", "трек"
    ]
    return any(kw in text.lower() for kw in keywords)
