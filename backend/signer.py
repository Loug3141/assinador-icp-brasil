"""
signer.py — Assinatura de PDF com certificado ICP-Brasil A1 (PFX) via pyhanko.

Fluxo por arquivo:
  1. Extrai metadados do certificado (.pfx)
  2. Calcula hashes do PDF original
  3. Gera página de log (log_page.py)
  4. Mescla original + página de log → PDF temporário
  5. Assina o PDF mesclado com pyhanko (PAdES-B-T, com fallback para PAdES-B-B)
  6. Salva na pasta de saída
"""
import io
import os
import shutil
import pytz
from datetime import datetime
from cryptography.hazmat.primitives.serialization import pkcs12
from cryptography import x509


# ─── Extração de metadados do certificado ─────────────────────────────────────

def extract_cert_info(pfx_path: str, pfx_password: str) -> dict:
    """
    Lê o arquivo .pfx e extrai os metadados relevantes do certificado.
    Levanta ValueError se a senha estiver errada.
    """
    with open(pfx_path, 'rb') as f:
        pfx_data = f.read()

    password = (
        pfx_password.encode('utf-8')
        if isinstance(pfx_password, str)
        else pfx_password
    )

    try:
        private_key, cert, chain = pkcs12.load_key_and_certificates(pfx_data, password)
    except Exception as e:
        raise ValueError(
            f'Não foi possível ler o certificado. Verifique a senha.\nDetalhe: {e}'
        )

    def _get(subject, oid: x509.ObjectIdentifier) -> str:
        try:
            attrs = subject.get_attributes_for_oid(oid)
            return attrs[0].value if attrs else ''
        except Exception:
            return ''

    subject = cert.subject
    issuer = cert.issuer
    brasilia = pytz.timezone('America/Sao_Paulo')

    # Compatibilidade com versões antigas de cryptography
    try:
        not_before = cert.not_valid_before_utc
        not_after  = cert.not_valid_after_utc
    except AttributeError:
        not_before = cert.not_valid_before.replace(tzinfo=pytz.utc)
        not_after  = cert.not_valid_after.replace(tzinfo=pytz.utc)

    return {
        'cn':         _get(subject, x509.NameOID.COMMON_NAME),
        'email':      _get(subject, x509.NameOID.EMAIL_ADDRESS),
        'org':        _get(subject, x509.NameOID.ORGANIZATION_NAME),
        'issuer':     _get(issuer,  x509.NameOID.COMMON_NAME),
        'valid_from': not_before.astimezone(brasilia).strftime('%d/%m/%Y'),
        'valid_to':   not_after.astimezone(brasilia).strftime('%d/%m/%Y'),
        'serial':     format(cert.serial_number, 'X'),
    }


# ─── Mesclagem de PDFs ─────────────────────────────────────────────────────────

def merge_pdfs(original_path: str, log_page_bytes: bytes, output_path: str) -> None:
    """Concatena as páginas do PDF original com a página de log."""
    from pypdf import PdfWriter, PdfReader

    writer = PdfWriter()

    with open(original_path, 'rb') as f:
        reader = PdfReader(f)
        for page in reader.pages:
            writer.add_page(page)

    log_reader = PdfReader(io.BytesIO(log_page_bytes))
    for page in log_reader.pages:
        writer.add_page(page)

    with open(output_path, 'wb') as f:
        writer.write(f)


# ─── Assinatura com pyhanko ───────────────────────────────────────────────────

def sign_with_pyhanko(input_path: str, output_path: str,
                       pfx_path: str, pfx_password: str) -> None:
    """
    Assina o PDF usando pyhanko com PAdES-B-T (com timestamp da freetsa.org).
    Se a TSA estiver indisponível, faz fallback automático para PAdES-B-B.
    """
    from pyhanko.sign import signers
    from pyhanko.pdf_utils.incremental_writer import IncrementalPdfFileWriter
    from pyhanko.sign.fields import SigFieldSpec

    password = (
        pfx_password.encode('utf-8')
        if isinstance(pfx_password, str)
        else pfx_password
    )

    signer = signers.SimpleSigner.load_pkcs12(
        pfx_file=pfx_path,
        passphrase=password
    )

    # Campo de assinatura: invisível visualmente, presente no PDF
    field_spec = SigFieldSpec(
        'AssinaturaFEX',
        on_page=-1,           # última página (página de log)
        box=(36, 10, 280, 55) # canto inferior esquerdo
    )

    meta = signers.PdfSignatureMetadata(
        field_name='AssinaturaFEX',
        md_algorithm='sha256',
        reason='Documento assinado digitalmente pela FEX Educação',
        location='Brasil',
    )

    # Lê o PDF inteiro em memória para poder tentar 2x (com/sem TSA)
    with open(input_path, 'rb') as f:
        pdf_bytes = f.read()

    def _sign(timestamper):
        buf = io.BytesIO(pdf_bytes)
        w = IncrementalPdfFileWriter(buf)
        ps = signers.PdfSigner(
            meta,
            signer=signer,
            timestamper=timestamper,
            new_field_spec=field_spec,
        )
        with open(output_path, 'wb') as out_f:
            ps.sign_pdf(w, output=out_f)

    # Tentativa 1: com timestamp (PAdES-B-T)
    timestamper = None
    try:
        from pyhanko.sign.timestamps import HTTPTimeStamper
        timestamper = HTTPTimeStamper('https://freetsa.org/tsr')
        _sign(timestamper)
        print(f'  [OK] Assinado com timestamp (PAdES-B-T): {os.path.basename(output_path)}')
        return
    except Exception as tsa_err:
        print(f'  [AVISO] TSA indisponível ({tsa_err}). Usando PAdES-B-B (sem timestamp)...')

    # Tentativa 2: sem timestamp (PAdES-B-B)
    _sign(None)
    print(f'  [OK] Assinado sem timestamp (PAdES-B-B): {os.path.basename(output_path)}')


# ─── Função principal ─────────────────────────────────────────────────────────

def sign_pdf_file(input_path: str, output_path: str,
                  pfx_path: str, pfx_password: str,
                  original_file_name: str) -> dict:
    """
    Orquestra todo o processo para um único arquivo:
      1. Extrai info do certificado
      2. Gera página de log
      3. Mescla original + log
      4. Assina o resultado
      5. Limpa arquivo temporário

    Retorna dict com metadados da operação.
    """
    from log_page import generate_log_page

    temp_merged = input_path.replace('.pdf', '__merged_tmp.pdf')

    # 1. Certificado
    cert_info = extract_cert_info(pfx_path, pfx_password)

    # 2. Página de log
    log_bytes, doc_uuid = generate_log_page(input_path, cert_info)

    # 3. Mescla
    merge_pdfs(input_path, log_bytes, temp_merged)

    try:
        # 4. Assina
        sign_with_pyhanko(temp_merged, output_path, pfx_path, pfx_password)
    finally:
        # 5. Limpa temporário
        if os.path.exists(temp_merged):
            os.remove(temp_merged)

    return {
        'doc_uuid': doc_uuid,
        'cert_cn': cert_info.get('cn', ''),
        'output': output_path,
    }
