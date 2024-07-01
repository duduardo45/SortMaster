import os

import certifi
from decouple import config
from detect_and_classify.integration import (
    take_photo_command_arduino,  # Substitua 'sua_funcao' pela função correta
)

# Uso da função importada
from flask import Flask, jsonify, redirect, render_template, request, session, url_for
from pymongo import MongoClient
from werkzeug.utils import secure_filename

# Certifique-se de substituir 'take_photo_command_arduino' pelo nome real da função que você deseja importar


app = Flask(__name__)
app.secret_key = "your_secret_key"

# Configuração do MongoDB Atlas
uri = str(config("MONGO_DB_URI"))
cliente = MongoClient(uri, tlsCAFile=certifi.where())
banco = cliente["projeto"]
colecao = banco["objetos"]

# Configuração do upload de arquivos
UPLOAD_FOLDER = "static/uploads/"
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif"}
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route("/")
def index():
    series = colecao.find()
    return render_template("index.html", series=series)


@app.route("/registro", methods=["GET", "POST"])
def registro():
    if request.method == "POST":
        num_boxes = request.form["numBoxes"]
        session["num_boxes"] = num_boxes  # Salva na sessão
        return redirect(url_for("registro"))

    num_boxes = session.get("num_boxes", 0)  # Recupera da sessão ou define 0
    return render_template("registro.html", num_boxes=num_boxes)


@app.route("/dados", methods=["GET"])
def dados():
    dados = list(colecao.find())
    return render_template("dados.html", dados=dados)


@app.route("/form/<int:box_id>", methods=["GET", "POST"])
def form(box_id):
    if request.method == "POST":
        name = request.form["name"]
        box_id = int(request.form["box_id"])  # Certifique-se de que é um inteiro
        mode = request.form["mode"]
        position_x = int(request.form["positionX"])
        position_y = int(request.form["positionY"])
        descricao = request.form["descricao"]

        document = {
            "name": name,
            "box_id": box_id,
            "mode": mode,
            "position_x": position_x,
            "position_y": position_y,
            "descricao": descricao,  # Campo único para descrição
        }

        if mode == "polygon":
            polygon = request.form["polygon"]
            color = request.form["color"]
            document["polygon"] = polygon
            document["color"] = color
        elif mode == "image":
            nfeatures = int(request.form["nfeatures"])
            ratio_test_threshold = float(request.form["ratio_test_threshold"])
            document["nfeatures"] = nfeatures
            document["ratio_test_threshold"] = ratio_test_threshold

            image = request.files["image"]
            if image and allowed_file(image.filename):
                filename = secure_filename(image.filename)
                image.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))
                image_url = url_for("static", filename="uploads/" + filename)
                document["image_url"] = image_url

        existing_data = colecao.find_one({"box_id": box_id})
        if existing_data:
            colecao.update_one({"box_id": box_id}, {"$set": document})
        else:
            colecao.insert_one(document)

        return redirect(url_for("index"))

    existing_data = colecao.find_one({"box_id": box_id})
    return render_template("form.html", box_id=box_id, data=existing_data)




@app.route("/start", methods=["GET"])
def start():
    objetos = list(colecao.find())
    objetos_list = []
    for obj in objetos:
        objeto_dict = {
            "name": obj.get("name"),
            "box_id": obj.get("box_id"),
            "mode": obj.get("mode"),
            "position_x": obj.get("position_x"),
            "position_y": obj.get("position_y"),
            "polygon": obj.get("polygon"),
            "color": obj.get("color"),
            "descricao": obj.get("descricao"),
            "nfeatures": obj.get("nfeatures"),
            "ratio_test_threshold": obj.get("ratio_test_threshold"),
            "image_url": obj.get("image_url"),
        }
        objetos_list.append(objeto_dict)

    # Chama a função do integration.py passando a lista de objetos
    take_photo_command_arduino(objetos_list)

    return jsonify(objetos_list)


if __name__ == "__main__":
    app.run(debug=True)
