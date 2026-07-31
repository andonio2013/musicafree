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
        body { font-family: -apple-system, BlinkMacSystemFont, sans-serif; background-color: #121212; color: white; text-align: center; padding: 20px; margin: 0; }
        h1 { color: #1DB954; font-size: 24px; margin-top: 10px; }
        input, select { width: 85%; max-width: 400px; padding: 12px; border-radius: 8px; border: 1px solid #333; background: #222; color: white; font-size: 16px; margin-bottom: 12px; }
        button { background-color: #1DB954; color: black; font-weight: bold; border: none; padding: 12px 25px; border-radius: 8px; font-size: 16px; cursor: pointer; }
        #status { margin-top: 15px; color: #888; font-size: 14px; }
        audio, video { width: 95%; max-width: 500px; margin-top: 15px; border-radius: 10px; }
        .lyrics-box { background: #1e1e1e; padding: 15px; border-radius: 10px; margin-top: 20px; max-height: 220px; overflow-y: auto; font-size: 14px; line-height: 1.6; white-space: pre-wrap; color: #ddd; text-align: left; }
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
    <button onclick="cercaEAvvia()">Riproduci 🚀</button>

    <div id="status"></div>
    <div id="media-container"></div>
    <div id="lyrics-container"></div>

    <script>
        async function cercaEAvvia() {
            const query = document.getElementById('query').value;
            const mode = document.getElementById('mode').value;
            const status = document.getElementById('status');
            const media = document.getElementById('media-container');
            const lyrics = document.getElementById('lyrics-container');

            if (!query) return;

            status.innerText = "Cerco la traccia... ⏳";
            media.innerHTML = "";
            lyrics.innerHTML = "";

            try {
                const res = await fetch('/get_stream?q=' + encodeURIComponent(query) + '&mode=' + mode);
                const data = await res.json();

                if (data.success) {
                    status.innerHTML = "<b style='color:#1DB954'>" + data.title + "</b>";
                    
                    if (mode === 'audio') {
                        media.innerHTML = `<audio controls autoplay src="${data.stream_url}"></audio>`;
                    } else {
                        media.innerHTML = `<video controls autoplay src="${data.stream_url}"></video>`;
                    }

                    if (data.lyrics) {
                        lyrics.innerHTML = `<div class="lyrics-box"><b>Testo Canzone 🎤</b><br><br>${data.lyrics}</div>`;
                    }
                } else {
                    status.innerText = "Errore: " + data.error;
                }
            } catch (e) {
                status.innerText = "Errore di connessione 😅";
            }
        }
    </script>
</body>
</html>
"""

@app.route('/')
def home():
    return render_template_string(HTML_TEMPLATE)

@app.route('/get_stream')
def get_stream():
    query = request.args.get('q')
    mode = request.args.get('mode', 'audio')

    if not query:
        return jsonify({'success': False, 'error': 'Inserisci un titolo'})

    try:
        search_res = requests.get(f"https://pipedapi.kavin.rocks/search?q={query}&filter=all", timeout=8).json()
        
        if not search_res.get('items'):
            return jsonify({'success': False, 'error': 'Canzone non trovata'})

        video_id = search_res['items'][0]['url'].split('v=')[-1]
        title = search_res['items'][0]['title']

        stream_data = requests.get(f"https://pipedapi.kavin.rocks/streams/{video_id}", timeout=8).json()

        stream_url = None
        if mode == 'audio':
            audio_streams = stream_data.get('audioStreams', [])
            if audio_streams:
                stream_url = audio_streams[0]['url']
        else:
            video_streams = stream_data.get('videoStreams', [])
            for v in video_streams:
                if v.get('videoOnly') == False:
                    stream_url = v['url']
                    break
            if not stream_url and video_streams:
                stream_url = video_streams[0]['url']

        lyrics_text = ""
        try:
            lrc_res = requests.get(f"https://lrclib.net/api/search?q={title}", timeout=5).json()
            if lrc_res and isinstance(lrc_res, list):
                lyrics_text = lrc_res[0].get('plainText', '')
        except: pass

        if stream_url:
            return jsonify({'success': True, 'title': title, 'stream_url': stream_url, 'lyrics': lyrics_text})
        else:
            return jsonify({'success': False, 'error': 'Impossibile caricare il flusso'})

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)