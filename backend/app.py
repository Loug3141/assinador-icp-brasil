"""
app.py — Servidor Flask: serve o frontend e expõe a API REST.

Rotas:
  GET  /                      → index.html
  POST /api/validate-cert     → valida o .pfx antes de iniciar
  POST /api/list-files        → lista PDFs na pasta do Drive
  POST /api/sign              → inicia job de assinatura em background
  GET  /api/progress/<job_id> → retorna progresso do job
  POST /api/open-output       → abre a pasta output/ no Explorer
"""
import os
import sys
import threading
import traceback
import uuid as uuid_lib

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

# Garante que os módulos do backend são encontrados
sys.path.insert(0, os.path.dirname(__file__))

from drive import get_drive_service, list_pdfs_in_folder, download_file
from signer import sign_pdf_file, extract_cert_info

# ─── Config ───────────────────────────────────────────────────────────────────

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEMP_DIR  = os.path.join(BASE_DIR, 'temp')
OUTPUT_DIR = os.path.join(BASE_DIR, 'output')
CREDENTIALS_DIR = os.path.join(BASE_DIR, 'credentials')

app = Flask(__name__, static_folder=os.path.join(BASE_DIR, 'frontend'))
CORS(app)

# Dict global para rastreamento de jobs em andamento
jobs: dict[str, dict] = {}


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _ensure_dirs():
    for d in [TEMP_DIR, OUTPUT_DIR, CREDENTIALS_DIR]:
        os.makedirs(d, exist_ok=True)


# ─── Job de assinatura (roda em thread separada) ──────────────────────────────

def _run_signing_job(job_id: str, folder_id: str,
                     pfx_path: str, pfx_password: str) -> None:
    job = jobs[job_id]

    try:
        service = get_drive_service(CREDENTIALS_DIR)
        files = list_pdfs_in_folder(service, folder_id)

        if not files:
            job.update({'status': 'done', 'error': 'Nenhum PDF encontrado na pasta.'})
            return

        job['total'] = len(files)
        job['file_names'] = [f['name'] for f in files]

        for file_info in files:
            file_name = file_info['id']   # id do Drive
            display_name = file_info['name']  # nome legível
            job['current_file'] = display_name

            temp_path = os.path.join(TEMP_DIR, display_name)
            output_name = display_name.replace('.pdf', '_assinado.pdf')
            output_path = os.path.join(OUTPUT_DIR, output_name)

            try:
                # Download
                download_file(service, file_info['id'], temp_path)

                # Assina
                meta = sign_pdf_file(
                    input_path=temp_path,
                    output_path=output_path,
                    pfx_path=pfx_path,
                    pfx_password=pfx_password,
                    original_file_name=display_name,
                )

                job['results'].append({
                    'name': display_name,
                    'output': output_name,
                    'status': 'success',
                    'doc_uuid': meta.get('doc_uuid', ''),
                })

            except Exception as e:
                traceback.print_exc()
                job['results'].append({
                    'name': display_name,
                    'status': 'error',
                    'error': str(e),
                })

            finally:
                # Limpa download temporário
                if os.path.exists(temp_path):
                    os.remove(temp_path)

            job['done'] += 1

        job['status'] = 'done'
        job['output_dir'] = OUTPUT_DIR

    except Exception as e:
        traceback.print_exc()
        job['status'] = 'error'
        job['error'] = str(e)


# ─── Rotas ────────────────────────────────────────────────────────────────────

@app.route('/')
def index():
    return send_from_directory(app.static_folder, 'index.html')


@app.route('/api/validate-cert', methods=['POST'])
def validate_cert():
    """Valida o certificado .pfx e retorna os metadados."""
    data = request.json or {}
    pfx_path = data.get('pfx_path', '').strip()
    pfx_password = data.get('pfx_password', '')

    if not pfx_path:
        return jsonify({'error': 'Caminho do certificado não informado.'}), 400
    if not os.path.exists(pfx_path):
        return jsonify({'error': f'Arquivo não encontrado: {pfx_path}'}), 400

    try:
        cert_info = extract_cert_info(pfx_path, pfx_password)
        return jsonify({'ok': True, 'cert_info': cert_info})
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@app.route('/api/list-files', methods=['POST'])
def list_files():
    """Lista PDFs na pasta do Google Drive."""
    data = request.json or {}
    folder_id = data.get('folder_id', '').strip()

    if not folder_id:
        return jsonify({'error': 'ID ou URL da pasta não informado.'}), 400

    try:
        service = get_drive_service(CREDENTIALS_DIR)
        files = list_pdfs_in_folder(service, folder_id)
        return jsonify({'files': files, 'count': len(files)})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/sign', methods=['POST'])
def sign():
    """Inicia o job de assinatura em background. Retorna job_id."""
    _ensure_dirs()
    data = request.json or {}

    folder_id    = data.get('folder_id', '').strip()
    pfx_path     = data.get('pfx_path', '').strip()
    pfx_password = data.get('pfx_password', '')

    # Validações
    errors = []
    if not folder_id:
        errors.append('ID ou URL da pasta não informado.')
    if not pfx_path:
        errors.append('Caminho do certificado não informado.')
    elif not os.path.exists(pfx_path):
        errors.append(f'Arquivo .pfx não encontrado: {pfx_path}')
    if errors:
        return jsonify({'error' : ' | '.join(errors)}), 400

    # Valida certificado antes de iniciar
    try:
        cert_info = extract_cert_info(pfx_path, pfx_password)
    except Exception as e:
        return jsonify({'error': f'Erro ao ler certificado: {e}'}), 400

    # Cria job
    job_id = str(uuid_lib.uuid4())
    jobs[job_id] = {
        'status':       'running',
        'total':        0,
        'done':         0,
        'current_file': '',
        'results':      [],
        'cert_info':    cert_info,
        'error':        None,
    }

    thread = threading.Thread(
        target=_run_signing_job,
        args=(job_id, folder_id, pfx_path, pfx_password),
        daemon=True,
    )
    thread.start()

    return jsonify({'job_id': job_id, 'cert_info': cert_info})


@app.route('/api/progress/<job_id>', methods=['GET'])
def progress(job_id: str):
    """Retorna o estado atual do job de assinatura."""
    if job_id not in jobs:
        return jsonify({'error': 'Job não encontrado.'}), 404
    return jsonify(jobs[job_id])


@app.route('/api/open-output', methods=['POST'])
def open_output():
    """Abre a pasta output/ no Windows Explorer."""
    import subprocess
    try:
        subprocess.Popen(['explorer', OUTPUT_DIR])
        return jsonify({'ok': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    _ensure_dirs()
    app.run(host='localhost', port=5050, debug=True)
