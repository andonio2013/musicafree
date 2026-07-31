import os
import requests
from flask import Flask, render_template_string, request, jsonify

app = Flask(__name__)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="it">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AnDonio Music 🎵</title>
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, sans-serif; background-color: #121212; color: white; text-align: center; padding: 15px; margin: 0; }
        h1 { color: #1DB954; font-size: 24px; margin-top: 10px; }
        input, select { width: 85%; max-width: 400px; padding: 12px; border-radius: 8px; border: 1px solid #333; background: #222; color: white; font-size: 16px; margin-bottom: 10px; }
        .btn-group { display: flex; justify-content: center; gap: 10px; margin-bottom: 10px; }
        button { background-color: #1DB954; color: black; font-weight: bold; border: none; padding: 12px 18px; border-radius: 8px; font-size: 15px; cursor: pointer; }
        button.secondary { background-color: #333; color: white; }
        #status { margin-top: 10px; color: #888; font-size: 14px; }
        audio, video { width: 95%; max-width: 500px; margin-top: 15px; border-radius: 10px; }
        .box { background: #1e1e1e; padding: 15px; border-radius: 10px; margin-top: 15px; text-align: left; max-width: 500px; margin-left: auto; margin-right: auto; }
        .queue-item { display: flex; justify-content: space-between; align-items: center; padding: 8px 0; border-bottom: 1px solid #333; font-size: 14px; }
        .queue-item:last-child { border-bottom: none; }
        .queue-actions button { padding: 5px 8px; font-size: 12px; margin-left: 5px; }
        .lyrics-box { max-height: 200px; overflow-y: auto; font-size: 14px; line-height: 1.6; white-space: pre-wrap; color: #ddd; }
    </style>
</head>
<body>
    <h1>AnDonio Player 🎵⚡</h1>
    
    <input type="text" id="query" placeholder="Titolo canzone o artista...">
    <br>
    <select id="mode">
        <option value="audio">🎵 Solo Audio (Streaming)</option>
        <option value="video">🎬 Video HD</option>
    </select>
    <br>
    <div class="btn-group">
        <button onclick="azioneCanzone('play')">Riproduci Ora 🚀</button>
        <button class="secondary" onclick="azioneCanzone('add')">Aggiungi in Coda ➕</button>
    </div>

    <div id="status"></div>
    <div id="media-container"></div>
    
    <!-- BOX CODA DI RIPRODUZIONE -->
    <div class="box" id="queue-box" style="display:none;">
        <b style="color:#1DB954;">Coda di Riproduzione 📜</b>
        <div id="queue-list" style="margin-top: 10px;"></div>
    </div>

    <div id="lyrics-container"></div>

    <script>
        let coda = [];
        let inRiproduzione = false;

        async function azioneCanzone(tipo) {
            const query = document.getElementById('query').value;
            const mode = document.getElementById('mode').value;
            const status = document.getElementById('status');

            if (!query) return;

            if (tipo === 'play') {
                coda.unshift({ query: query, mode: mode });
                aggiornaGraficaCoda();
                riproduciProssimo();
            } else {
                coda.push({ query: query, mode: mode });
                status.innerText = "Canzone aggiunta alla coda!";
                aggiornaGraficaCoda();
                if (!inRiproduzione) {
                    riproduciProssimo();
                }
            }
            document.getElementById('query').value = "";
        }

        async function riproduciProssimo() {
            if (coda.length === 0) {
                inRiproduzione = false;
                document.getElementById('status').innerText = "Coda terminata!";
                return;
            }

            inRiproduzione = true;
            const brano = coda[0];
            const status = document.getElementById('status');
            const media = document.getElementById('media-container');
            const lyrics = document.getElementById('lyrics-container');

            status.innerText = "Carico traccia dalla coda... ⏳";

            try {
                const res = await fetch('/get_stream?q=' + encodeURIComponent(brano.query) + '&mode=' + brano.mode);
                const data = await res.json();

                if (data.success) {
                    status.innerHTML = "<b style='color:#1DB954'>In Riproduzione: " + data.title + "</b>";
                    
                    if (brano.mode === 'audio') {
                        media.innerHTML = `<audio id="player" controls autoplay src="${data.stream_url}"></audio>`;
                    } else {
                        media.innerHTML = `<video id="player" controls autoplay src="${data.stream_url}"></video>`;
                    }

                    const player = document.getElementById('player');
                    player.onended = () => {
                        rimuoviDallaCoda(0);
                        riproduciProssimo();
                    };

                    if (data.lyrics) {
                        lyrics.innerHTML = `<div class="box lyrics-box"><b style="color:#1DB954;">Testo Canzone 🎤</b><br><br>${data.lyrics}</div>`;
                    } else {
                        lyrics.innerHTML = "";
                    }
                } else {
                    status.innerText = "Errore: " + data.error;
                    rimuoviDallaCoda(0);
                    riproduciProssimo();
                }
            } catch (e) {
                status.innerText = "Errore di connessione 😅";
            }
        }

        function rimuoviDallaCoda(idx) {
            coda.splice(idx, 1);
            aggiornaGraficaCoda();
        }

        function forzaPlay(idx) {
            const elemento = coda.splice(idx, 1)[0];
            coda.unshift(elemento);
            aggiornaGraficaCoda();
            riproduciProssimo();
        }

        function aggiornaGraficaCoda() {
            const queueBox = document.getElementById('queue-box');
            const queueList = document.getElementById('queue-list');

            if (coda.length <= 1) {
                if (coda.length === 0) queueBox.style.display = 'none';
                else queueBox.style.display = 'block';
            } else {
                queueBox.style.display = 'block';
            }

            queueList.innerHTML = "";
            coda.forEach((item, index) => {
                const tag = index === 0 ? "▶️ " : `${index + 1}. `;
                queueList.innerHTML += `
                    <div class="queue-item">
                        <span>${tag}${item.query} (${item.mode})</span>
                        <div class="queue-actions">
                            ${index !== 0 ? `<button onclick="forzaPlay(${index})">▶</button>` : ''}
                            <button class="secondary" onclick="rimuoviDallaCoda(${index})">❌</button>
                        </div>
                    </div>
                `;
            });
        }
    </script>
</body>
</html>
"""

INVIDIOUS_INSTANCES = [
    "https://invidious.nerdvpn.de",
    "https://inv.tux.pizza",
    "https://invidious.projectsegfau.lt",
    "https://yt.artemislena.eu"
]

@app.route('/')
def home():
    return render_template_string(HTML_TEMPLATE)

@app.route('/get_stream')
def get_stream():
    query = request.args.get('q')
    mode = request.args.get('mode', 'audio')

    if not query:
        return jsonify({'success': False, 'error': 'Inserisci un titolo'})

    video_data = None
    target_instance = None

    for instance in INVIDIOUS_INSTANCES:
        try:
            search_url = f"{instance}/api/v1/search?q={requests.utils.quote(query)}&type=video"
            search_res = requests.get(search_url, timeout=5)
            if search_res.status_code == 200:
                items = search_res.json()
                if items and len(items) > 0:
                    video_id = items[0]['videoId']
                    video_data = requests.get(f"{instance}/api/v1/videos/{video_id}", timeout=5).json()
                    target_instance = instance
                    break
        except Exception:
            continue

    if not video_data or 'title' not in video_data:
        return jsonify({'success': False, 'error': 'Tutti i server sono occupati. Riprova!'})

    title = video_data.get('title', query)
    stream_url = None

    if mode == 'audio':
        adaptive_formats = video_data.get('adaptiveFormats', [])
        audio_streams = [f for f in adaptive_formats if f.get('type', '').startswith('audio/')]
        if audio_streams:
            stream_url = audio_streams[0].get('url')
    else:
        format_streams = video_data.get('formatStreams', [])
        if format_streams:
            stream_url = format_streams[-1].get('url')

    if not stream_url:
        stream_url = f"{target_instance}/latest_version?id={video_data['videoId']}&itag=18"

    lyrics_text = ""
    try:
        lrc_res = requests.get(f"https://lrclib.net/api/search?q={requests.utils.quote(title)}", timeout=4).json()
        if lrc_res and isinstance(lrc_res, list):
            lyrics_text = lrc_res[0].get('plainText', '')
    except Exception:
        pass

    return jsonify({'success': True, 'title': title, 'stream_url': stream_url, 'lyrics': lyrics_text})

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)