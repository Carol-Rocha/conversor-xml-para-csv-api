import os
from pathlib import Path
import xml.etree.ElementTree as ET
import pandas as pd

# CONSTANTES DE TAGS

TAGS_ICMS = [
    'orig', 'CST', 'vBC', 'pRedBC', 'pICMS', 'vICMS', 'vBCFCP', 'pFCP',
    'vFCP', 'pMVAST', 'pRedBCST', 'vBCST', 'pICMSST', 'vICMSST',
    'vBCFCPST', 'pFCPST', 'vFCPST', 'vICMSDeson'
]

TAGS_PIS = ['CST', 'vBC', 'pPIS', 'vPIS']
TAGS_COFINS = ['CST', 'vBC', 'pCOFINS', 'vCOFINS']
TAGS_IPI = ['CST', 'vBC', 'pIPI', 'vIPI']


# FUNÇÕES AUXILIARES

def get_text(elem, path, ns):
    achado = elem.find(path, ns)
    if achado is None or achado.text is None:
        return None

    valor = achado.text.strip()

    try:
        float(valor)
        return valor.replace('.', ',')
    except ValueError:
        return valor


def trata_codigo_fiscal(serie: pd.Series, tamanho: int) -> pd.Series:
    return (
        serie
        .fillna(0)
        .astype(str)
        .str.replace(',', '.', regex=False)
        .str.split('.', n=1).str[0]
        .str.zfill(tamanho)
    )


# LEITURA DE UM XML

def ler_xml_completo(xml_path: Path) -> list[dict]:
    tree = ET.parse(xml_path)
    root = tree.getroot()

    ns = {'nfe': 'http://www.portalfiscal.inf.br/nfe'}
    inf = root.find('.//nfe:infNFe', ns)

    if inf is None:
        return []

    linhas = []

    chave_nfe = inf.attrib.get("Id", "").replace("NFe", "")
    ide_nNF = get_text(inf, 'nfe:ide/nfe:nNF', ns)
    dta_emi = get_text(inf, 'nfe:ide/nfe:dhEmi', ns)

    emit_CNPJ = get_text(inf, 'nfe:emit/nfe:CNPJ', ns)
    emit_xNome = get_text(inf, 'nfe:emit/nfe:xNome', ns)
    emit_UF = get_text(inf, 'nfe:emit/nfe:enderEmit/nfe:UF', ns)

    dest_CNPJ = get_text(inf, 'nfe:dest/nfe:CNPJ', ns)
    dest_xNome = get_text(inf, 'nfe:dest/nfe:xNome', ns)
    dest_UF = get_text(inf, 'nfe:dest/nfe:enderDest/nfe:UF', ns)

    for det in inf.findall('nfe:det', ns):

        linha = {
            'chave_nfe': chave_nfe,
            'dta_dhemi': dta_emi,
            'ide_nNF': ide_nNF,
            'emit_CNPJ': emit_CNPJ,
            'emit_xNome': emit_xNome,
            'emit_enderEmit_UF': emit_UF,
            'dest_CNPJ': dest_CNPJ,
            'dest_xNome': dest_xNome,
            'dest_enderDest_UF': dest_UF,
            'vItem': det.attrib.get('nItem')
        }

        prod = det.find('nfe:prod', ns)

        linha.update({
            'cProd': get_text(prod, 'nfe:cProd', ns),
            'cEAN': get_text(prod, 'nfe:cEAN', ns),
            'xProd': get_text(prod, 'nfe:xProd', ns),
            'NCM': get_text(prod, 'nfe:NCM', ns),
            'CEST': get_text(prod, 'nfe:CEST', ns),
            'CFOP': get_text(prod, 'nfe:CFOP', ns),
            'uCom': get_text(prod, 'nfe:uCom', ns),
            'qCom': get_text(prod, 'nfe:qCom', ns),
            'vFrete': get_text(prod, 'nfe:vFrete', ns),
            'vUnCom': get_text(prod, 'nfe:vUnCom', ns),
            'vProd': get_text(prod, 'nfe:vProd', ns),
            'vUnTrib': get_text(prod, 'nfe:vUnTrib', ns),
        })

        # ICMS
        soma_icms = {tag: 0.0 for tag in TAGS_ICMS}
        valor_icms = {tag: None for tag in TAGS_ICMS}

        icms = det.find('.//nfe:ICMS', ns)

        if icms is not None:
            for tipo in [
                'ICMS00', 'ICMS10', 'ICMS20', 'ICMS30', 'ICMS40',
                'ICMS41', 'ICMS50', 'ICMS51', 'ICMS60', 'ICMS70', 'ICMS90'
            ]:
                bloco = icms.find(f'nfe:{tipo}', ns)
                if bloco is not None:
                    for tag in bloco:
                        tag_name = tag.tag.split('}')[-1]
                        value = tag.text.strip().replace('.', ',') if tag.text else None
                        if tag_name in TAGS_ICMS and value:
                            valor_icms[tag_name] = value
                            try:
                                soma_icms[tag_name] += float(value.replace(',', '.'))
                            except ValueError:
                                pass

        for tag in TAGS_ICMS:
            linha[f'ICMS {tag}'] = (
                f'{soma_icms[tag]:.2f}'.replace('.', ',')
                if soma_icms[tag] > 0 else valor_icms[tag]
            )

        # IPI, PIS, COFINS
        impostos = {
            'IPI': TAGS_IPI,
            'PIS': TAGS_PIS,
            'COFINS': TAGS_COFINS
        }

        for imposto, tags in impostos.items():
            soma = {tag: 0.0 for tag in tags}
            valor = {tag: None for tag in tags}

            bloco_imp = det.find(f'.//nfe:{imposto}', ns)
            if bloco_imp is not None:
                for child in bloco_imp:
                    for tag in child:
                        tag_name = tag.tag.split('}')[-1]
                        value = tag.text.strip().replace('.', ',') if tag.text else None
                        if tag_name in tags and value:
                            valor[tag_name] = value
                            try:
                                soma[tag_name] += float(value.replace(',', '.'))
                            except ValueError:
                                pass

            for tag in tags:
                linha[f'{imposto} {tag}'] = (
                    f'{soma[tag]:.2f}'.replace('.', ',')
                    if soma[tag] > 0 else valor[tag]
                )

        linhas.append(linha)

    return linhas


# FUNÇÃO PRINCIPAL (API)

def processar_xmls(pasta_xml: Path) -> pd.DataFrame:
    xmls = [
        Path(root) / file
        for root, _, files in os.walk(pasta_xml)
        for file in files
        if file.lower().endswith('.xml')
    ]

    dados = []

    for xml in xmls:
        dados.extend(ler_xml_completo(xml))

    df = pd.DataFrame(dados)

    if 'dta_dhemi' in df.columns:
        df['dta_dhemi'] = pd.to_datetime(
            df['dta_dhemi'], errors='coerce'
        )
        import datetime
        df['dta_dhemi'] = df['dta_dhemi'].apply(
            lambda x: x.strftime('%d/%m/%Y') if isinstance(x, datetime.datetime) and not pd.isna(x) else ''
        )
    
    # cria ICMS o/cst se as colunas existirem
    if {'ICMS orig', 'ICMS CST'}.issubset(df.columns):

        df['ICMS orig'] = trata_codigo_fiscal(df['ICMS orig'], 1)
        df['ICMS CST']  = trata_codigo_fiscal(df['ICMS CST'], 2)

        # força texto no Excel
        df['ICMS o/cst'] = "'" + df['ICMS orig'] + df['ICMS CST']

        # remove colunas auxiliares
        df.drop(columns=['ICMS orig', 'ICMS CST'], inplace=True)
    
    col_ref = 'vUnTrib'
    nova_col = 'ICMS o/cst'

    cols = list(df.columns)

    if col_ref in cols and nova_col in cols:
        idx = cols.index(col_ref) + 1
        cols.insert(idx, cols.pop(cols.index(nova_col)))
        df = df[cols]
        
    return df