# Conversor XML para CSV — Backend (API)

Este projeto é uma **API em Python** desenvolvida com **FastAPI**, responsável por processar arquivos XML de Notas Fiscais (NFe) e gerar um arquivo CSV consolidado com informações fiscais, tributárias e de produtos.

A aplicação foi construída para substituir um fluxo manual anteriormente executado no Google Colab, permitindo agora **uso local, integração com frontend e futura publicação em produção**.

---

## 🚀 Funcionalidade principal

- Recebe um arquivo **.RAR contendo múltiplos XMLs** ou **um XML único**
- Extrai automaticamente os XMLs
- Processa:
  - Dados da NFe
  - Emitente e destinatário
  - Produtos
  - Tributos (ICMS, IPI, PIS, COFINS)
  - Somatórios fiscais
- Gera um **CSV final padronizado**
- Retorna o CSV para **download imediato**

---

## 🧱 Tecnologias utilizadas

- Python 3.9+
- FastAPI
- Uvicorn
- Pandas
- lxml / xml.etree
- tqdm
- Virtualenv (venv)

---

## 📁 Estrutura do projeto

conversor-xml-para-csv-api/
├── app/
│   ├── main.py          # API FastAPI (endpoint)
│   ├── processor.py     # Regra de negócio (leitura e transformação dos XMLs)
│   └── temp/
│       ├── uploads/     # Arquivos enviados
│       └── output/      # CSVs gerados
├── venv/                # Ambiente virtual (não versionado)
├── requirements.txt
├── .gitignore
└── README.md

---

## ⚙️ Como rodar o projeto localmente

### 1️⃣ Criar ambiente virtual

```bash
python3 -m venv venv
source venv/bin/activate   # macOS / Linux
# ou
venv\Scripts\activate      # Windows


