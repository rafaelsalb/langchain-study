from io import BufferedReader, BytesIO
from flask import Flask, jsonify, request
from werkzeug.datastructures import FileStorage

from config import Config
import preprocess
from simplify import simplify
from summarize import Prompts, summarize_section

def summarize(doc: FileStorage | BufferedReader, sections: list[int] | None = None) -> str:
    pdf: BytesIO = BytesIO(doc.read())
    if sections is None:
        raise ValueError("Sections must be provided")
    cabecalho = preprocess.partition(pdf, sections[0], sections[1])
    relatorio: str = preprocess.partition(pdf, sections[1], sections[2])
    voto: str = preprocess.partition(pdf, sections[2], sections[3])
    decisao: str = preprocess.partition(pdf, sections[3], sections[4])
    print("\n\nSUMMARIZING\n\n")
    summaries: dict[str, str] = {
        "cabecalho": summarize_section(cabecalho, prompt=Prompts.CABECALHO, verbose=True, skip_postprocess=Config.SKIP_POSTPROCESS),
        "relatorio": summarize_section(relatorio, prompt=Prompts.RELATORIO, verbose=True, skip_postprocess=Config.SKIP_POSTPROCESS),
        "voto": summarize_section(voto, prompt=Prompts.VOTO, verbose=True, skip_postprocess=Config.SKIP_POSTPROCESS),
        "decisao": summarize_section(decisao, prompt=Prompts.DECISAO, verbose=True, skip_postprocess=Config.SKIP_POSTPROCESS),
    }

    print("\n\nSIMPLIFYING\n\n")

    simplified = {
        "cabecalho": summaries["cabecalho"],
        "relatorio": simplify(summaries["relatorio"]),
        "voto": simplify(summaries["voto"]),
        "decisao": simplify(summaries["decisao"]),
    }

    result = {
        "cabecalho": simplified["cabecalho"],
        "relatorio": {
            "text": simplified["relatorio"][0],
            "score": simplified["relatorio"][1],
            "ratio": simplified["relatorio"][2],
        },
        "voto": {
            "text": simplified["voto"][0],
            "score": simplified["voto"][1],
            "ratio": simplified["voto"][2],
        },
        "decisao": {
            "text": simplified["decisao"][0],
            "score": simplified["decisao"][1],
            "ratio": simplified["decisao"][2],
        }
    }

    return result

app = Flask(__name__)

@app.post("/test/simplify")
def test_simplify():
    if request.json is None:
        raise ValueError("No JSON provided")
    text = request.json['text']
    if text is None:
        return "No text provided"
    result = simplify(text)
    return jsonify(result[0])

@app.post("/simplify")
def process():
    doc = request.files['doc']
    sections = [int(i) for i in request.form.getlist('sections')]
    print(sections)
    return jsonify(summarize(doc, sections))

if __name__ == "__main__":
    app.run()
