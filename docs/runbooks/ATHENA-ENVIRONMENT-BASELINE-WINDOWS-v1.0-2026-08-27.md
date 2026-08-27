# ATHENA — Environment Baseline Windows

**Versão:** 1.0
**Data de criação:** 27/08/2026
**Status:** Baseline validada para reprodução
**Projeto:** CIRCE-ATHENA
**Ambiente de origem validado:** máquina de TRABALHO — Windows x64
**Objetivo:** reproduzir a mesma base técnica em outra máquina, especialmente a máquina de CASA, sem copiar ambientes virtuais corrompidos ou dependências implícitas.
**Relação documental:** documento novo; **não substitui** nenhuma SPEC funcional nem o Project Master. Complementa ambos como runbook de ambiente.

---

## 1. Decisão de baseline

A baseline Windows validada do CIRCE-ATHENA é:

```text
Windows x64
→ Python 3.11.9
→ .venv local criada do zero
→ requirements.txt
→ Alembic
→ smokes
→ startup
```

A baseline **não** é Python 3.12.

Durante a estabilização de 26/08/2026 foi identificada uma `.venv` inconsistente que misturava interpretador Python 3.12 com artefatos binários `cp311`, incluindo extensões de Pydantic Core/NumPy. A correção segura foi excluir completamente a `.venv` e recriá-la com Python 3.11.9.

Decisão:

> Para reproduzir o ambiente validado desta versão do ATHENA, usar Python 3.11.9 e criar uma `.venv` nova. Não copiar `.venv` entre máquinas.

---

## 2. Identidade do repositório validado

```text
REPO LOCAL (TRABALHO): C:\Projetos\CIRCE_ATHENA
REMOTE: https://github.com/Prjkt-CIRCE/CIRCE-ATHENA.git
BRANCH DE CHECKPOINT: feat/at06b-curated-01-intake-storage
HEAD VALIDADO: b7e294a2e73aa2c0fa94cd2498f9a40197362b3
SHORT SHA: b7e294a
```

No checkpoint de 27/08/2026, `HEAD` local e `origin/feat/at06b-curated-01-intake-storage` estavam alinhados e a working tree estava limpa.

---

## 3. Python canônico

### 3.1. Versão

```text
Python 3.11.9
```

Validação conhecida:

```powershell
py -3.11 --version
```

Esperado:

```text
Python 3.11.9
```

### 3.2. Interpretador da aplicação

Depois da criação da venv:

```text
C:\Projetos\CIRCE_ATHENA\.venv\Scripts\python.exe
```

Toda validação canônica deve preferir esse executável explicitamente, evitando dependência do `python` global do Windows.

---

## 4. Criação limpa da `.venv`

Na raiz do projeto:

```powershell
Set-Location "C:\Projetos\CIRCE_ATHENA"

if (Test-Path ".venv") {
    Remove-Item -Recurse -Force ".venv"
}

py -3.11 -m venv .venv

.\.venv\Scripts\python.exe -m pip install --upgrade pip setuptools wheel
.\.venv\Scripts\python.exe -m pip install --no-cache-dir -r requirements.txt
```

Não reutilizar uma `.venv` antiga se houver qualquer dúvida sobre a versão de Python que a criou.

---

## 5. Verificações mínimas de integridade

### 5.1. Interpretador

```powershell
.\.venv\Scripts\python.exe -c "import sys; print(sys.version); print(sys.executable)"
```

Confirmar:

- versão 3.11.9;
- executável dentro de `C:\Projetos\CIRCE_ATHENA\.venv\Scripts\python.exe`.

### 5.2. NumPy

```powershell
.\.venv\Scripts\python.exe -c "import numpy; print('NUMPY:', numpy.__version__); print('NUMPY: OK')"
```

Na baseline validada, NumPy foi instalado como `2.4.6`.

### 5.3. Core stack

```powershell
.\.venv\Scripts\python.exe -c "import pydantic, fastapi, sqlalchemy, alembic; print('CORE STACK: OK')"
```

### 5.4. Grafo de imports do ATHENA

```powershell
.\.venv\Scripts\python.exe -c "import app.services.face_service; print('FACE SERVICE MODULE: OK')"
.\.venv\Scripts\python.exe -c "import app.services.photo_service; print('PHOTO SERVICE MODULE: OK')"
.\.venv\Scripts\python.exe -c "import run; print('ATHENA IMPORT GRAPH: OK')"
```

Esses testes validam importabilidade da aplicação. Eles **não validam reconhecimento facial/GPU end-to-end**.

---

## 6. InsightFace / ONNX Runtime

O `requirements.txt` desta baseline contém a stack necessária ao subsistema facial, incluindo InsightFace, ONNX/ONNX Runtime GPU, NumPy e pacotes NVIDIA relevantes.

Durante a estabilização foi introduzido lazy loading em:

```text
app/services/face_service.py
commit: 2f5c1e2
```

Objetivo:

> Falha do subsistema opcional InsightFace/ONNX não deve impedir o ATHENA inteiro de iniciar.

### Estado real

```text
import face_service: validado
import photo_service: validado
import run: validado
reconhecimento facial real com CUDA: NÃO VALIDADO
```

Não tratar a presença de `onnxruntime-gpu` ou dos pacotes NVIDIA como prova de que CUDA está operacional.

A validação GPU deve ser feita em unidade técnica própria.

---

## 7. Alembic e banco

### 7.1. Head validado

```text
0009_at06b_curated_intake_storage (head)
```

Verificar:

```powershell
.\.venv\Scripts\python.exe -m alembic current
```

Para banco novo/reproduzido:

```powershell
.\.venv\Scripts\python.exe -m alembic upgrade head
```

### 7.2. Compatibilidade legada

O projeto contém ponte de linhagem para reconhecer:

```text
0013_at06b63_facts_topic_composition
```

Essa compatibilidade foi validada em cópia do backup do banco real antes da migração.

Não editar manualmente `alembic_version` para “resolver” incompatibilidades sem prova de schema e decisão explícita.

---

## 8. Banco de dados entre TRABALHO e CASA

O banco operacional local não deve ser presumido como conteúdo do Git.

Regra:

```text
GitHub
→ código, migrations, templates, scripts, documentação

athena.db
→ dado local da instalação
```

Para desenvolvimento em CASA, preferir banco local próprio criado/migrado pela aplicação.

Não copiar automaticamente o banco real da máquina do TRABALHO, especialmente quando houver material operacional ou sensível.

Se futuramente for necessária replicação de dados, tratar como procedimento separado de exportação/migração e segurança.

---

## 9. DEV_AUTH_BYPASS

A baseline contém suporte a bypass de autenticação **somente para desenvolvimento local**.

Configuração no código:

```text
dev_auth_bypass: bool = False
```

Portanto o recurso é desligado por padrão.

Quando explicitamente usado em `.env` local:

```text
DEV_AUTH_BYPASS=true
```

O bypass só deve funcionar para hosts locais permitidos:

```text
127.0.0.1
::1
localhost
```

Operador de desenvolvimento:

```text
dev-local
ATHENA Desenvolvimento Local
role: admin
```

A ação é auditada como:

```text
dev_auth_bypass
```

Commit de referência:

```text
b7e294a fix(dev): restore audited localhost auth bypass
```

### Regra de segurança

- não habilitar em produção;
- não habilitar em servidor exposto à rede;
- se `dev-local` estiver inativo no banco, o bypass não deve criar sessão para esse operador;
- `.env` continua sendo configuração local e não deve ser versionado com segredos.

---

## 10. Startup validado

Com a `.venv` íntegra:

```powershell
.\.venv\Scripts\python.exe run.py
```

Resultado observado na máquina de TRABALHO:

```text
Application startup complete.
Uvicorn running on http://0.0.0.0:8766
```

Acesso local utilizado:

```text
http://127.0.0.1:8766
```

---

## 11. Smokes mínimos da baseline AT-06B

Executar com o Python da `.venv`:

```powershell
.\.venv\Scripts\python.exe -m scripts.smoke_at06b_curated_workspace_ui
.\.venv\Scripts\python.exe -m scripts.smoke_at06b_curated_document_http
.\.venv\Scripts\python.exe -m scripts.smoke_at06b_curated_document_intake
.\.venv\Scripts\python.exe -m scripts.smoke_at06b_curated_storage
.\.venv\Scripts\python.exe -m scripts.smoke_at06b_curated_document_model
```

Para validar compatibilidade com um backup legado específico, quando o arquivo estiver legitimamente disponível:

```powershell
.\.venv\Scripts\python.exe -m scripts.smoke_at06b_legacy_lineage `
  "CAMINHO_DO_BACKUP.db"
```

Resultados esperados dos smokes AT-06B:

```text
WORKSPACE UI SMOKE: OK
DOCUMENT HTTP SMOKE: OK
DOCUMENT INTAKE SMOKE: OK
STORAGE SMOKE: OK
DOCUMENT MODEL SMOKE: OK
```

Finalizar com:

```powershell
git diff --check
git status --short --branch
```

---

## 12. Procedimento recomendado para retomar na máquina de CASA

### Etapa A — gate read-only

```powershell
Set-Location "C:\Projetos\CIRCE_ATHENA"

git status --short --branch
git remote -v
git branch --show-current
git fetch origin
git log -5 --oneline --decorate
```

Não modificar nada antes de conhecer o estado real da cópia doméstica.

### Etapa B — alinhar código

A branch de checkpoint validada é:

```text
feat/at06b-curated-01-intake-storage
```

O commit de referência é:

```text
b7e294a
```

A forma exata de checkout/pull deve ser escolhida somente após o gate read-only, para não sobrescrever eventual trabalho local da máquina de CASA.

### Etapa C — validar Python

```powershell
py -0p
py -3.11 --version
```

Se Python 3.11.9 não estiver disponível, instalar a versão compatível antes de criar `.venv`.

### Etapa D — recriar `.venv`

Usar o procedimento da Seção 4.

### Etapa E — banco e migrations

Para banco doméstico novo ou descartável:

```powershell
.\.venv\Scripts\python.exe -m alembic upgrade head
.\.venv\Scripts\python.exe -m alembic current
```

### Etapa F — smokes e startup

Executar Seções 5, 10 e 11.

Somente depois considerar o ambiente doméstico equivalente para desenvolvimento.

---

## 13. Sintomas de `.venv` contaminada

Sinais observados durante a investigação:

- Python 3.12 carregando extensões `cp311`;
- erros de import de `_pydantic_core`;
- erros de NumPy em `_multiarray_umath.cp311-win_amd64.pyd`;
- comportamento incoerente mesmo após reinstalação parcial de pacotes.

Se isso ocorrer:

> Não “consertar por cima”. Excluir `.venv`, confirmar o Python-base e recriar do zero.

---

## 14. Dependências globais e PATH

A aplicação não deve depender de um Python global específico quando a `.venv` está ativa/explicitamente chamada.

Durante a estabilização, um ambiente do Hermes havia colocado um Python próprio no PATH do usuário e foi removido. A baseline não depende de Hermes.

Verificações úteis:

```powershell
where.exe python
py -0p
.\.venv\Scripts\python.exe -c "import sys; print(sys.executable)"
```

O último comando é a autoridade para saber qual interpretador está executando o ATHENA.

---

## 15. Checklist de equivalência entre máquinas

Considerar a máquina de CASA equivalente para desenvolvimento apenas quando:

- [ ] repositório correto;
- [ ] remoto correto;
- [ ] branch/commit desejados conhecidos;
- [ ] Python 3.11.9 disponível;
- [ ] `.venv` criada localmente do zero;
- [ ] `requirements.txt` instalado sem erro;
- [ ] core stack importa;
- [ ] ATHENA import graph importa;
- [ ] Alembic está no head esperado;
- [ ] smokes da unidade atual passam;
- [ ] aplicação sobe em `127.0.0.1:8766`;
- [ ] configuração local necessária está definida;
- [ ] nenhum dado operacional foi copiado inadvertidamente.

---

## 16. Baseline de referência

```text
DATA: 27/08/2026
OS: Windows x64
PYTHON: 3.11.9
VENV: .venv local e descartável/recriável
REPO: Prjkt-CIRCE/CIRCE-ATHENA
BRANCH: feat/at06b-curated-01-intake-storage
HEAD: b7e294a
ALEMBIC: 0009_at06b_curated_intake_storage
STARTUP: validado
AT-06B SMOKES: validados
INSIGHTFACE IMPORT ISOLATION: validada
INSIGHTFACE/CUDA E2E: pendente
DEV_AUTH_BYPASS: local, opcional, auditável, desligado por padrão
```

---

## 17. Regra de manutenção deste documento

Sempre que a baseline de ambiente mudar de forma material — versão de Python, stack binária, forma de startup, banco, migrations ou procedimento de replicação — gerar nova versão deste documento.

A nova versão deve declarar explicitamente:

```text
SUBSTITUI a baseline anterior
ou
COMPLEMENTA a baseline anterior
```

Não manter duas baselines concorrentes sem indicação de autoridade.
