from flask import Flask, request, jsonify
from pyquery import PyQuery as pq
import urllib.request
import json
import os

app = Flask(__name__)

def get_url_content(url):
    try:
        with urllib.request.urlopen(url) as f:
            return f.read().decode('utf-8')
    except Exception as e:
        print(f"[ERRO] Falha ao acessar {url}: {e}")
        return None

def get_soundcloud_client_id():
    home = pq(url="https://soundcloud.com/")
    scripts = home("html > body > script")

    for i in range(len(scripts)):
        src = scripts.eq(i).attr("src")
        if not src:
            continue

        content = get_url_content(src)
        if not content:
            continue

        if 'client_id:"' in content:
            client_id = content.split('client_id:"')[1].split('"')[0]
            if len(client_id) == 32:
                return client_id
    return None

@app.route('/stream', methods=['GET'])
def get_stream_url():
    track_url = request.args.get('url')
    if not track_url:
        return jsonify({'error': 'Faltando parâmetro "url"'}), 400

    client_id = get_soundcloud_client_id()
    if not client_id:
        return jsonify({'error': 'Falha ao obter client_id'}), 500

    resolve_api = f"https://api-v2.soundcloud.com/resolve?url={track_url}&client_id={client_id}"
    resolved_data = get_url_content(resolve_api)
    if not resolved_data:
        return jsonify({'error': 'Erro ao resolver a URL'}), 500

    resolved = json.loads(resolved_data)
    transcodings = resolved.get("media", {}).get("transcodings", [])

    stream = next((t for t in transcodings if t["format"]["protocol"] == "progressive"), None)
    if not stream:
        return jsonify({'error': 'Nenhum stream MP3 disponível'}), 404

    stream_info_url = f"{stream['url']}?client_id={client_id}"
    stream_info_data = get_url_content(stream_info_url)
    if not stream_info_data:
        return jsonify({'error': 'Erro ao obter dados do stream'}), 500

    stream_info = json.loads(stream_info_data)
    return jsonify({'stream_url': stream_info['url']})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)