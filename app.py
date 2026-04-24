from fastapi import FastAPI, UploadFile, File
from fastapi.responses import FileResponse
import shutil
import os
from soma_op import ExtractorOP

app = FastAPI()

from fastapi.responses import HTMLResponse

from fastapi.responses import HTMLResponse

@app.get("/", response_class=HTMLResponse)
def home():
    with open("templates/index.html", encoding="utf-8") as f:
        return f.read()

UPLOAD_PATH = "OP_Verificado"
OUTPUT_PATH = "Planilhas_csv"

os.makedirs(UPLOAD_PATH, exist_ok=True)
os.makedirs(OUTPUT_PATH, exist_ok=True)


from fastapi.staticfiles import StaticFiles

app.mount("/static", StaticFiles(directory="static"), name="static")


@app.post("/processar")
async def processar_pdf(file: UploadFile = File(...)):
    caminho_pdf = os.path.join(UPLOAD_PATH, file.filename)

    with open(caminho_pdf, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    nome_csv = file.filename.replace(".pdf", ".csv")
    caminho_csv = os.path.join(OUTPUT_PATH, nome_csv)

    extractor = ExtractorOP(caminho_pdf)

    if extractor.extrair():
        extractor.salvar_csv(caminho_csv)
        return FileResponse(caminho_csv, filename=nome_csv)

    return {"erro": "Falha ao processar PDF"}