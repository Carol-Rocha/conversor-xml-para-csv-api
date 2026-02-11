from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pathlib import Path
import shutil
import uuid
import os
import rarfile

rarfile.UNRAR_TOOL = "unar"

from app.processor import processar_xmls

app = FastAPI(
    title="Conversor XML para CSV",
    description="""
    API para processamento de arquivos **.RAR** contendo múltiplos XMLs de Nota Fiscal (NFe).

    ### Fluxo:
    1. Envie um arquivo **.rar**
    2. A API extrai os XMLs
    3. Processa dados fiscais e tributários
    4. Gera um arquivo CSV consolidado
    5. Retorna o CSV para download
    """,
    version="1.0.0"
)

# Configuração do CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Permite todas as origens
    allow_credentials=True,
    allow_methods=["*"],  # Permite todos os métodos HTTP
    allow_headers=["*"],  # Permite todos os cabeçalhos
)

BASE_DIR = Path(__file__).resolve().parent
TEMP_DIR = BASE_DIR / "temp"
UPLOAD_DIR = TEMP_DIR / "uploads"
XML_DIR = TEMP_DIR / "xmls"
OUTPUT_DIR = TEMP_DIR / "output"

for d in [UPLOAD_DIR, XML_DIR, OUTPUT_DIR]:
    d.mkdir(parents=True, exist_ok=True)


def extrair_rar(caminho_rar: Path, destino: Path):
    destino.mkdir(parents=True, exist_ok=True)
    with rarfile.RarFile(caminho_rar) as rf:
        rf.extractall(destino)


@app.post(
    "/processar",
    summary="Processar arquivo RAR com XMLs",
    description="Recebe um arquivo **.rar** contendo XMLs de NFe e retorna um CSV processado."
)
async def processar_arquivo(file: UploadFile = File(...)):
    if not file.filename.lower().endswith(".rar"):
        raise HTTPException(
            status_code=400,
            detail="Envie um arquivo .rar contendo XMLs de NFe"
        )

    request_id = uuid.uuid4().hex

    rar_path = UPLOAD_DIR / f"{request_id}.rar"
    pasta_xml = XML_DIR / request_id
    csv_saida = OUTPUT_DIR / f"resultado_{request_id}.csv"

    # Salva o arquivo enviado
    with open(rar_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    try:
        # Extrai o RAR
        extrair_rar(rar_path, pasta_xml)

        # Processa os XMLs e gera o DataFrame
        df = processar_xmls(pasta_xml)
        # Salva o DataFrame em CSV
        df.to_csv(csv_saida, index=False)

    except rarfile.Error:
        raise HTTPException(
            status_code=400,
            detail="Erro ao extrair o arquivo RAR. Verifique se o arquivo é válido."
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erro interno ao processar arquivo: {str(e)}"
        )

    return FileResponse(
        path=csv_saida,
        filename="notas_fiscais_processadas.csv",
        media_type="text/csv"
    )