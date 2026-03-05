"""
Server Workbench — Flask local (porta 5002)
Salva/carrega imagens aprovadas e exporta finais para ML.
"""

import os
import re
import base64
import glob
from flask import Flask, send_file, request, jsonify

app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
APROVADOS_DIR = os.path.join(BASE_DIR, "Fotos_Infograficos_aprovados")
PRONTOS_DIR = os.path.join(BASE_DIR, "Prontos_ML")

os.makedirs(APROVADOS_DIR, exist_ok=True)
os.makedirs(PRONTOS_DIR, exist_ok=True)


def add_cors(response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type"
    return response


app.after_request(add_cors)


@app.route("/")
def index():
    return send_file(os.path.join(BASE_DIR, "workbench-ilustracoes.html"))


@app.route("/api/carregar")
def carregar():
    """Lista imagens salvas em Fotos_Infograficos_aprovados/.
    Retorna mapa panelId -> filename (ex: {"p01": "p01_Foto_Capa.png"})
    """
    result = {}
    for f in os.listdir(APROVADOS_DIR):
        match = re.match(r"^(p\d{2})_", f)
        if match and f.lower().endswith((".png", ".jpg", ".jpeg")):
            result[match.group(1)] = f
    return jsonify(result)


@app.route("/Fotos_Infograficos_aprovados/<path:filename>")
def serve_aprovado(filename):
    filepath = os.path.join(APROVADOS_DIR, filename)
    if not os.path.isfile(filepath):
        return "Not found", 404
    return send_file(filepath)


@app.route("/api/salvar", methods=["POST", "OPTIONS"])
def salvar():
    if request.method == "OPTIONS":
        return "", 204

    data = request.get_json()
    panel_id = data.get("panelId", "")
    name = data.get("name", "imagem")
    image_data = data.get("imageData", "")

    if not re.match(r"^p\d{2}$", panel_id):
        return jsonify({"ok": False, "error": "panelId invalido"}), 400

    if not image_data.startswith("data:image/"):
        return jsonify({"ok": False, "error": "imageData invalido"}), 400

    # Remover arquivo anterior do mesmo painel
    for old in glob.glob(os.path.join(APROVADOS_DIR, panel_id + "_*")):
        os.remove(old)

    # Decodificar base64
    header, b64 = image_data.split(",", 1)
    ext = "png"
    if "jpeg" in header or "jpg" in header:
        ext = "jpg"

    # Sanitizar nome
    safe_name = re.sub(r"[^a-zA-Z0-9_\-]", "_", name)
    filename = f"{panel_id}_{safe_name}.{ext}"
    filepath = os.path.join(APROVADOS_DIR, filename)

    with open(filepath, "wb") as f:
        f.write(base64.b64decode(b64))

    return jsonify({"ok": True, "filename": filename})


@app.route("/api/finalizar", methods=["POST", "OPTIONS"])
def finalizar():
    if request.method == "OPTIONS":
        return "", 204

    data = request.get_json()
    paineis = data.get("paineis", [])

    if not paineis:
        return jsonify({"ok": False, "error": "Nenhum painel enviado"}), 400

    count = 0
    for item in paineis:
        panel_id = item.get("panelId", "")
        image_data = item.get("imageData", "")

        if not re.match(r"^p\d{2}$", panel_id):
            continue
        if not image_data.startswith("data:image/"):
            continue

        num = panel_id.replace("p", "")
        header, b64 = image_data.split(",", 1)
        filename = f"{num}.png"
        filepath = os.path.join(PRONTOS_DIR, filename)

        with open(filepath, "wb") as f:
            f.write(base64.b64decode(b64))
        count += 1

    return jsonify({"ok": True, "total": count})


@app.route("/api/status")
def status():
    """Retorna status de cada painel: salvo em aprovados e/ou pronto em ML."""
    aprovados = {}
    for f in os.listdir(APROVADOS_DIR):
        match = re.match(r"^(p\d{2})_", f)
        if match and f.lower().endswith((".png", ".jpg", ".jpeg")):
            aprovados[match.group(1)] = f

    prontos = {}
    for f in os.listdir(PRONTOS_DIR):
        match = re.match(r"^(\d{2})\.png$", f)
        if match:
            prontos["p" + match.group(1)] = f

    result = {}
    for pid in [f"p{i:02d}" for i in range(1, 11)]:
        result[pid] = {
            "salvo": pid in aprovados,
            "arquivo_salvo": aprovados.get(pid, None),
            "pronto_ml": pid in prontos,
        }

    return jsonify(result)


if __name__ == "__main__":
    print("=" * 50)
    print("  Workbench Server — http://localhost:5002")
    print(f"  Aprovados: {APROVADOS_DIR}")
    print(f"  Prontos ML: {PRONTOS_DIR}")
    print("=" * 50)
    app.run(host="127.0.0.1", port=5002, debug=True)
