# FEX Assinador em Massa

Ferramenta local para assinar PDFs em lote com **Certificado Digital ICP-Brasil A1** (.pfx),
gerando uma página de certificado de assinatura no estilo D4Sign.

---

## Pré-requisitos

- **Python 3.11+** instalado e no PATH
- **Arquivo `.pfx`** do seu certificado A1 acessível na máquina
- **Conta Google** com acesso ao Google Drive onde os PDFs estão

---

## 1. Estrutura de pastas

Após baixar os arquivos, a estrutura deve ser:

```
fex-assinador/
├── backend/
│   ├── app.py
│   ├── drive.py
│   ├── log_page.py
│   └── signer.py
├── frontend/
│   └── index.html
├── credentials/       ← você vai colocar o google_oauth.json aqui
├── output/            ← criada automaticamente
├── temp/              ← criada automaticamente
├── requirements.txt
└── run.py
```

---

## 2. Configuração do Google Cloud Console (uma vez só)

Você precisa criar credenciais OAuth para que a ferramenta acesse seu Google Drive.

### Passo a passo:

1. Acesse [console.cloud.google.com](https://console.cloud.google.com)
2. Crie um novo projeto (ex.: **FEX Assinador**)
3. No menu lateral: **APIs e Serviços → Biblioteca**
4. Pesquise **"Google Drive API"** e clique em **Ativar**
5. No menu lateral: **APIs e Serviços → Credenciais**
6. Clique em **+ Criar credenciais → ID do cliente OAuth**
7. Se solicitado, configure a **Tela de consentimento OAuth**:
   - Tipo: **Externo** → Criar
   - Nome do app: `FEX Assinador`
   - E-mail de suporte: seu e-mail
   - Salvar e continuar (pode ignorar os campos opcionais)
   - Em **Escopos**: adicionar `.../auth/drive.readonly`
   - Em **Usuários de teste**: adicionar seu e-mail Google
8. De volta em **Criar ID do cliente OAuth**:
   - Tipo de aplicativo: **Aplicativo para computador**
   - Nome: `FEX Assinador`
   - Criar
9. Clique em **Baixar JSON** (ícone de download)
10. **Renomeie** o arquivo baixado para `google_oauth.json`
11. **Mova** para a pasta `credentials/` do projeto

---

## 3. Instalação das dependências

Abra o **terminal** (Prompt de Comando ou PowerShell) na pasta do projeto:

```bash
# 1. Crie um ambiente virtual (recomendado)
python -m venv .venv

# 2. Ative o ambiente virtual
# Windows:
.venv\Scripts\activate

# 3. Instale as dependências
pip install -r requirements.txt
```

> ⚠️ A instalação pode levar 2–5 minutos. A biblioteca `pyhanko` tem várias dependências.

---

## 4. Executando

```bash
# Com o venv ativado:
python run.py
```

O browser abrirá automaticamente em `http://localhost:5050`.

---

## 5. Como usar

### Aba Certificado Digital

1. **Caminho do .pfx**: Cole o caminho completo do seu arquivo de certificado.
   - Exemplo: `C:\Users\SeuNome\Documents\certificado_fex.pfx`
   - Dica: no Windows Explorer, segure Shift e clique com botão direito no arquivo → **"Copiar como caminho"**
2. **Senha**: Digite a senha do certificado
3. Clique em **Verificar** — os dados do certificado aparecerão confirmados

### Aba Google Drive

1. **Nome da pasta**: Digite o nome exato da pasta no Drive que contém os PDFs
2. Clique em **Listar PDFs**
3. Na **primeira execução**, o browser abrirá pedindo login Google — autorize o acesso
4. Os PDFs encontrados serão listados

### Assinatura

1. Com os PDFs listados, clique em **Assinar todos os PDFs**
2. Acompanhe o progresso em tempo real
3. Ao finalizar, clique em **Abrir pasta output/** para ver os arquivos assinados

---

## 6. O que é gerado

Para cada `arquivo.pdf`, é gerado `arquivo_assinado.pdf` na pasta `output/`, contendo:

- Todas as páginas originais do PDF
- Uma página extra de certificado de assinatura com:
  - Nome do signatário (CN do certificado)
  - Timestamp (horário de Brasília)
  - IP da máquina
  - Hashes SHA256 e SHA512 do documento original
  - Dados do certificado (emissor, validade, serial)
  - QR code com o hash do documento
  - Texto legal (MP 2.200-2/2001 e Lei 14.063/2020)
- Assinatura digital PAdES-B-T embutida no PDF (com timestamp criptográfico via freetsa.org)

---

## 7. Padrão de assinatura

| Padrão     | Descrição                              | Quando é usado          |
|-----------|----------------------------------------|-------------------------|
| PAdES-B-T | Assinatura + timestamp criptográfico   | Quando a TSA está disponível |
| PAdES-B-B | Assinatura sem timestamp externo       | Fallback automático     |

Ambos têm **validade jurídica** conforme a ICP-Brasil. O PAdES-B-T é mais robusto pois
prova o momento exato da assinatura por uma terceira parte confiável (TSA).

---

## 8. Solução de problemas

**"Arquivo google_oauth.json não encontrado"**
→ Siga o passo 2 e coloque o arquivo em `credentials/`.

**"Erro ao ler certificado"**
→ Verifique se a senha está correta e se o caminho não contém caracteres especiais.

**"Pasta não encontrada no Google Drive"**
→ O nome deve ser exato, incluindo maiúsculas/minúsculas. Certifique-se de que a pasta está no seu Drive (não apenas compartilhada com você).

**"TSA indisponível"**
→ A ferramenta fará fallback automático para PAdES-B-B. Isso é normal.

**Erro de importação Python**
→ Certifique-se de que o venv está ativado e que `pip install -r requirements.txt` foi executado com sucesso.

---

## 9. Autenticação Google (token em cache)

Após o primeiro login, o token é salvo em `credentials/token.json`. Nas próximas execuções,
o login não será necessário. Para reconectar com outra conta, delete esse arquivo.

---

## Suporte

Desenvolvido para uso interno da FEX Educação.
