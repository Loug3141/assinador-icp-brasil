"""
drive.py — Integração com Google Drive via OAuth 2.0.
"""
import os
import io

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload, MediaFileUpload

SCOPES = ['https://www.googleapis.com/auth/drive']


def get_drive_service(credentials_dir: str):
    """
    Retorna um serviço autenticado do Google Drive.
    Na primeira vez, abre o browser para OAuth. Salva o token em cache.
    """
    token_path = os.path.join(credentials_dir, 'token.json')
    oauth_path = os.path.join(credentials_dir, 'google_oauth.json')

    if not os.path.exists(oauth_path):
        raise FileNotFoundError(
            f'Arquivo "google_oauth.json" não encontrado em:\n{credentials_dir}\n\n'
            'Faça o download no Google Cloud Console e salve nessa pasta.\n'
            'Consulte o README.md para instruções detalhadas.'
        )

    creds = None

    if os.path.exists(token_path):
        try:
            creds = Credentials.from_authorized_user_file(token_path, SCOPES)
            # Se os escopos salvos não cobrem os escopos necessários, forçar re-autenticação
            if creds and creds.scopes and not set(SCOPES).issubset(set(creds.scopes)):
                creds = None
        except (ValueError, KeyError):
            # token.json malformado ou sem refresh_token — apaga e re-autentica
            creds = None

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
            except Exception:
                creds = None  # Falhou ao renovar; forçar re-auth completo

        if not creds or not creds.valid:
            if os.path.exists(token_path):
                os.remove(token_path)
            flow = InstalledAppFlow.from_client_secrets_file(oauth_path, SCOPES)
            # access_type='offline' + prompt='consent' garantem que o refresh_token seja sempre devolvido
            creds = flow.run_local_server(
                port=8080,
                access_type='offline',
                prompt='consent',
            )

        with open(token_path, 'w', encoding='utf-8') as token_file:
            token_file.write(creds.to_json())

    return build('drive', 'v3', credentials=creds)


def _extract_folder_id(folder_input: str) -> str:
    """
    Aceita um ID de pasta ou uma URL do Google Drive e retorna o ID da pasta.
    Exemplos de URL suportados:
      https://drive.google.com/drive/folders/<ID>
      https://drive.google.com/drive/u/0/folders/<ID>
    """
    import re
    match = re.search(r'/folders/([a-zA-Z0-9_-]+)', folder_input)
    if match:
        return match.group(1)
    # Remove espaços e retorna diretamente como ID
    return folder_input.strip()


def list_pdfs_in_folder(service, folder_id: str) -> list[dict]:
    """
    Lista todos os PDFs dentro de uma pasta do Google Drive pelo ID ou URL.
    Retorna lista de dicts com keys: id, name, size.
    """
    folder_id = _extract_folder_id(folder_id)

    # Listar PDFs dentro da pasta (suporta Drives Compartilhados e Meu Drive)
    pdf_query = (
        f"'{folder_id}' in parents "
        f"and mimeType='application/pdf' "
        f"and trashed=false"
    )
    pdf_result = service.files().list(
        q=pdf_query,
        fields='files(id, name, size)',
        orderBy='name',
        pageSize=200,
        supportsAllDrives=True,
        includeItemsFromAllDrives=True,
    ).execute()

    return pdf_result.get('files', [])


def download_file(service, file_id: str, dest_path: str) -> None:
    """Baixa um arquivo do Drive para o caminho local (suporta Drives Compartilhados)."""
    request = service.files().get_media(fileId=file_id, supportsAllDrives=True)

    with open(dest_path, 'wb') as fh:
        downloader = MediaIoBaseDownload(fh, request)
        done = False
        while not done:
            _, done = downloader.next_chunk()


def upload_file(service, local_path: str, filename: str, parent_folder_id: str) -> dict:
    """
    Faz upload de um arquivo local para uma pasta no Google Drive.
    Retorna dict com id, name e webViewLink do arquivo criado.
    Suporta Meu Drive e Drives Compartilhados.
    """
    parent_id = _extract_folder_id(parent_folder_id)

    file_metadata = {
        'name': filename,
        'parents': [parent_id],
    }

    media = MediaFileUpload(local_path, mimetype='application/pdf', resumable=True)

    result = service.files().create(
        body=file_metadata,
        media_body=media,
        fields='id, name, webViewLink',
        supportsAllDrives=True,
    ).execute()

    return result
