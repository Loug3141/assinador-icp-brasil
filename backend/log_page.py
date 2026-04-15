"""
log_page.py — Geração da página de logs/certificado de assinatura (estilo D4Sign).
Usa reportlab canvas para controle total do layout.
"""
import io
import os
import hashlib
import socket
import uuid as uuid_module
from datetime import datetime

import pytz
import qrcode
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.pdfbase.pdfmetrics import stringWidth

# ─── Constantes ───────────────────────────────────────────────────────────────

BRASILIA_TZ = pytz.timezone('America/Sao_Paulo')
W, H = A4  # 595.27 x 841.89 points
MARGIN = 1.5 * cm
CONTENT_W = W - 2 * MARGIN

# Paleta de cores
C_DARK_GREEN   = colors.HexColor('#1B5E20')
C_MID_GREEN    = colors.HexColor('#2E7D32')
C_LIME         = colors.HexColor('#32CD32')
C_DARK         = colors.HexColor('#1A1A1A')
C_SURFACE      = colors.HexColor('#F5F5F5')
C_BORDER       = colors.HexColor('#DDDDDD')
C_TEXT         = colors.HexColor('#212121')
C_MUTED        = colors.HexColor('#757575')
C_WHITE        = colors.white
C_CHECK_BG     = colors.HexColor('#E8F5E9')


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _calculate_hashes(file_path: str) -> tuple[str, str]:
    sha256 = hashlib.sha256()
    sha512 = hashlib.sha512()
    with open(file_path, 'rb') as f:
        while chunk := f.read(65536):
            sha256.update(chunk)
            sha512.update(chunk)
    return sha256.hexdigest(), sha512.hexdigest()


def _get_local_ip() -> str:
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return '127.0.0.1'


def _wrap_text(text: str, font: str, size: float, max_width: float) -> list[str]:
    """Quebra texto em linhas que cabem em max_width."""
    words = text.split(' ')
    lines, line = [], ''
    for word in words:
        candidate = f'{line} {word}'.strip() if line else word
        if stringWidth(candidate, font, size) <= max_width:
            line = candidate
        else:
            if line:
                lines.append(line)
            line = word
    if line:
        lines.append(line)
    return lines


def _draw_text_block(c, lines: list[str], x: float, y: float,
                     font: str, size: float, color, line_gap: float = 1.3) -> float:
    """Desenha bloco de texto, retorna y final."""
    c.setFont(font, size)
    c.setFillColor(color)
    for i, line in enumerate(lines):
        c.drawString(x, y - i * size * line_gap, line)
    return y - (len(lines) - 1) * size * line_gap


def _hline(c, y: float, color=None, width: float = 0.4):
    c.setStrokeColor(color or C_BORDER)
    c.setLineWidth(width)
    c.line(MARGIN, y, W - MARGIN, y)


def _section_title(c, text: str, y: float) -> float:
    """Desenha título de seção com linha separadora abaixo. Retorna y após o bloco."""
    c.setFont('Helvetica-Bold', 9.5)
    c.setFillColor(C_TEXT)
    c.drawString(MARGIN, y, text)
    y -= 5
    _hline(c, y)
    return y - 10


# ─── Função principal ─────────────────────────────────────────────────────────

def generate_log_page(original_pdf_path: str, cert_info: dict,
                      doc_uuid: str | None = None) -> tuple[bytes, str]:
    """
    Gera a página de certificado de assinatura como PDF (bytes).

    Parâmetros:
        original_pdf_path: caminho do PDF original (para calcular hashes)
        cert_info: dict com keys: cn, email, issuer, valid_from, valid_to, serial, org
        doc_uuid: UUID do documento (gerado automaticamente se None)

    Retorno:
        (pdf_bytes, doc_uuid)
    """
    if doc_uuid is None:
        doc_uuid = str(uuid_module.uuid4())

    sha256, sha512 = _calculate_hashes(original_pdf_path)
    local_ip = _get_local_ip()
    now = datetime.now(BRASILIA_TZ)
    ts_short = now.strftime('%d %b %Y, %H:%M:%S')
    ts_long = now.strftime('%d/%m/%Y às %H:%M:%S') + ' (Brasília, Brasil)'
    file_name = os.path.basename(original_pdf_path)

    # ── QR Code com hash do documento ────────────────────────────────────────
    qr = qrcode.QRCode(version=2, box_size=3, border=1,
                       error_correction=qrcode.constants.ERROR_CORRECT_M)
    qr.add_data(f'SHA256:{sha256}')
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color='black', back_color='white')
    qr_buf = io.BytesIO()
    qr_img.save(qr_buf, format='PNG')
    qr_buf.seek(0)
    qr_buf = ImageReader(qr_buf)

    # ── Canvas ────────────────────────────────────────────────────────────────
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)

    y = H - MARGIN  # cursor vertical (cresce para baixo)

    # ═══════════════════════════════════════════════════════════════
    # HEADER — barra verde escuro
    # ═══════════════════════════════════════════════════════════════
    BAR_H = 1.3 * cm
    c.setFillColor(C_DARK_GREEN)
    c.rect(MARGIN, y - BAR_H, CONTENT_W, BAR_H, fill=1, stroke=0)

    # Logo / nome FEX
    c.setFillColor(C_WHITE)
    c.setFont('Helvetica-Bold', 12)
    c.drawString(MARGIN + 10, y - BAR_H * 0.62, 'FEX EDUCAÇÃO')

    # Subtítulo direita
    c.setFont('Helvetica', 7.5)
    c.drawRightString(W - MARGIN - 10, y - BAR_H * 0.35, 'Certificado de Assinatura Digital')
    c.drawRightString(W - MARGIN - 10, y - BAR_H * 0.75, 'Documento assinado via FEX Assinador')

    # Linha verde limão decorativa
    c.setFillColor(C_LIME)
    c.rect(MARGIN, y - BAR_H - 2, CONTENT_W, 2, fill=1, stroke=0)

    y -= BAR_H + 10

    # ═══════════════════════════════════════════════════════════════
    # DOCUMENTO INFO — caixa cinza claro
    # ═══════════════════════════════════════════════════════════════
    DOC_BOX_H = 2.1 * cm
    c.setFillColor(C_SURFACE)
    c.setStrokeColor(C_BORDER)
    c.setLineWidth(0.5)
    c.roundRect(MARGIN, y - DOC_BOX_H, CONTENT_W, DOC_BOX_H, 4, fill=1, stroke=1)

    # QR code (canto direito)
    QR_SIZE = 1.7 * cm
    c.drawImage(qr_buf,
                W - MARGIN - QR_SIZE - 8,
                y - DOC_BOX_H + (DOC_BOX_H - QR_SIZE) / 2,
                QR_SIZE, QR_SIZE)

    # Texto do documento
    # Largura disponível: do início do texto até o QR code (com margem)
    MAX_FN_W = CONTENT_W - QR_SIZE - 32
    fn_display = file_name
    while stringWidth(fn_display, 'Helvetica-Bold', 9) > MAX_FN_W and len(fn_display) > 4:
        fn_display = fn_display[:-2]
    if fn_display != file_name:
        fn_display = fn_display[:-1] + '…'

    c.setFont('Helvetica-Bold', 9)
    c.setFillColor(C_TEXT)
    c.drawString(MARGIN + 12, y - 16, fn_display)

    c.setFont('Helvetica', 7.5)
    c.setFillColor(C_MUTED)
    c.drawString(MARGIN + 12, y - 30, f'Código do documento: {doc_uuid}')

    c.setFont('Helvetica', 7)
    c.drawString(MARGIN + 12, y - 43,
                 f'Datas e horários baseados em Brasília, Brasil  •  '
                 f'Gerado em {ts_short}')

    y -= DOC_BOX_H + 18

    # ═══════════════════════════════════════════════════════════════
    # ASSINATURAS
    # ═══════════════════════════════════════════════════════════════
    y = _section_title(c, 'Assinaturas', y)

    SIG_BOX_H = 3.0 * cm
    c.setFillColor(C_WHITE)
    c.setStrokeColor(C_BORDER)
    c.setLineWidth(0.5)
    c.roundRect(MARGIN, y - SIG_BOX_H, CONTENT_W, SIG_BOX_H, 4, fill=1, stroke=1)

    # Faixa verde à esquerda da caixa
    c.setFillColor(C_MID_GREEN)
    c.roundRect(MARGIN, y - SIG_BOX_H, 4, SIG_BOX_H, 2, fill=1, stroke=0)

    # Círculo com checkmark
    CX = MARGIN + 26
    CY = y - SIG_BOX_H / 2
    c.setFillColor(C_CHECK_BG)
    c.setStrokeColor(C_MID_GREEN)
    c.setLineWidth(1.2)
    c.circle(CX, CY, 12, fill=1, stroke=1)
    c.setFillColor(C_MID_GREEN)
    c.setFont('Helvetica-Bold', 12)
    c.drawCentredString(CX, CY - 4, '✓')

    # Dados do signatário
    TX = MARGIN + 48
    cn = cert_info.get('cn', 'N/A')
    email = cert_info.get('email', '')
    issuer = cert_info.get('issuer', '')
    serial = cert_info.get('serial', '')
    vfrom = cert_info.get('valid_from', '')
    vto = cert_info.get('valid_to', '')

    c.setFont('Helvetica-Bold', 9)
    c.setFillColor(C_TEXT)
    # Trunca CN se muito longo
    cn_display = cn if stringWidth(cn, 'Helvetica-Bold', 9) <= CONTENT_W - 60 else cn[:60] + '…'
    c.drawString(TX, y - 14, cn_display)

    c.setFont('Helvetica', 7.5)
    c.setFillColor(C_MUTED)
    c.drawString(TX, y - 26, f'Certificado Digital ICP-Brasil  •  Emissor: {issuer}')
    c.drawString(TX, y - 38, email if email else '(e-mail não disponível no certificado)')

    c.setFont('Helvetica-Bold', 7.5)
    c.setFillColor(C_MID_GREEN)
    c.drawString(TX, y - 52, f'Assinou em {ts_long}')

    c.setFont('Helvetica', 7)
    c.setFillColor(C_MUTED)
    c.drawString(TX, y - 64, f'IP: {local_ip}  •  Serial do certificado: {serial}')
    c.drawString(TX, y - 75, f'Validade do certificado: {vfrom} a {vto}')

    # Badge "Assinou"
    c.setFillColor(C_MID_GREEN)
    c.roundRect(W - MARGIN - 60, y - 20, 52, 16, 3, fill=1, stroke=0)
    c.setFillColor(C_WHITE)
    c.setFont('Helvetica-Bold', 8)
    c.drawCentredString(W - MARGIN - 34, y - 13, 'Assinou')

    y -= SIG_BOX_H + 18

    # ═══════════════════════════════════════════════════════════════
    # EVENTOS DO DOCUMENTO
    # ═══════════════════════════════════════════════════════════════
    y = _section_title(c, 'Eventos do documento', y)

    events = [
        (ts_short, f'Processo de assinatura iniciado pelo FEX Assinador'),
        (ts_short,
         f'Assinatura digital ICP-Brasil aplicada por {cn}  •  '
         f'Email: {email}  •  IP: {local_ip}'),
    ]

    for evt_time, evt_desc in events:
        c.setFont('Helvetica-Bold', 8)
        c.setFillColor(C_TEXT)
        c.drawString(MARGIN, y, evt_time)
        y -= 12

        wrapped = _wrap_text(evt_desc, 'Helvetica', 7.5, CONTENT_W - 8)
        for line in wrapped:
            c.setFont('Helvetica', 7.5)
            c.setFillColor(C_MUTED)
            c.drawString(MARGIN + 8, y, line)
            y -= 11

        y -= 6

    y -= 4

    # ═══════════════════════════════════════════════════════════════
    # HASHES
    # ═══════════════════════════════════════════════════════════════
    _hline(c, y)
    y -= 12

    c.setFont('Helvetica-Bold', 8)
    c.setFillColor(C_TEXT)
    c.drawString(MARGIN, y, 'Hash do documento original')
    y -= 13

    c.setFont('Courier', 6.5)
    c.setFillColor(C_MUTED)
    c.drawString(MARGIN, y, f'(SHA256) {sha256}')
    y -= 10

    # SHA512 em 2 linhas (comprido demais para uma linha)
    half = len(sha512) // 2
    c.drawString(MARGIN, y, f'(SHA512) {sha512[:half]}')
    y -= 10
    c.drawString(MARGIN + 51, y, sha512[half:])
    y -= 12

    c.setFont('Helvetica-Oblique', 7)
    c.setFillColor(C_MUTED)
    c.drawString(MARGIN, y,
                 'Este log pertence única e exclusivamente ao documento de hash acima.')

    y -= 18

    # ═══════════════════════════════════════════════════════════════
    # FOOTER — Certificação ICP-Brasil
    # ═══════════════════════════════════════════════════════════════
    _hline(c, y, C_BORDER, 1)
    y -= 14

    # Caixa ICP-Brasil
    FOOTER_H = 1.4 * cm
    c.setFillColor(C_SURFACE)
    c.setStrokeColor(C_BORDER)
    c.setLineWidth(0.5)
    c.roundRect(MARGIN, y - FOOTER_H, CONTENT_W, FOOTER_H, 4, fill=1, stroke=1)

    # Selo ICP-Brasil (representação textual)
    SEAL_X = MARGIN + 10
    SEAL_Y = y - FOOTER_H / 2
    c.setFillColor(C_MID_GREEN)
    c.circle(SEAL_X + 8, SEAL_Y, 10, fill=1, stroke=0)
    c.setFillColor(C_WHITE)
    c.setFont('Helvetica-Bold', 5)
    c.drawCentredString(SEAL_X + 8, SEAL_Y + 2, 'ICP')
    c.drawCentredString(SEAL_X + 8, SEAL_Y - 4, 'Brasil')

    TEXT_X = SEAL_X + 24
    c.setFont('Helvetica-Bold', 8)
    c.setFillColor(C_TEXT)
    c.drawString(TEXT_X, y - 12, 'Documento assinado com Certificado Digital ICP-Brasil')

    c.setFont('Helvetica-Bold', 7.5)
    c.setFillColor(C_MID_GREEN)
    c.drawString(TEXT_X, y - 23, 'Integridade certificada no padrão ICP-BRASIL')

    c.setFont('Helvetica', 6.8)
    c.setFillColor(C_MUTED)
    c.drawString(TEXT_X, y - 34,
                 'Validade legal conforme MP 2.200-2/2001 e Lei 14.063/2020. '
                 'Assinaturas eletrônicas e físicas têm igual validade.')

    # ═══════════════════════════════════════════════════════════════
    # BORDA GERAL DA PÁGINA
    # ═══════════════════════════════════════════════════════════════
    c.setStrokeColor(C_BORDER)
    c.setLineWidth(0.8)
    c.rect(MARGIN - 4, 0.8 * cm, CONTENT_W + 8, H - MARGIN - 0.8 * cm + 4,
           fill=0, stroke=1)

    c.save()
    buf.seek(0)
    return buf.read(), doc_uuid
