# HANDOFF — AT-06B-CURATED-01 — Intake Físico e Armazenamento Canônico

**Data de criação:** 27/08/2026
**Status:** Unidade concluída / validada; pronta para fechamento documental, PR e merge
**Projeto:** CIRCE-ATHENA
**Unidade concluída:** AT-06B-CURATED-01
**Branch:** `feat/at06b-curated-01-intake-storage`
**HEAD técnico validado:** `b7e294a2e73aa2c0fa94cd2498f9a40197362b3` (`b7e294a`)
**Relação documental:** documento novo; **COMPLEMENTA / NÃO SUBSTITUI** a SPEC AT-06B-CURATED-01 v1.0 e o Project Master de 27/08/2026.

---

## 1. Unidade concluída

`AT-06B-CURATED-01 — Intake Físico e Armazenamento Canônico de Materiais do Caso`

Decisão final:

```text
APROVADO COM PENDÊNCIAS NÃO BLOQUEANTES
STATUS: DONE / VALIDATED
```

---

## 2. Objetivo

Estabelecer um contrato canônico para que um material físico possa:

```text
Caso
→ intake
→ preservação do original
→ SHA-256
→ metadados
→ storage governado
→ recuperação do Original
→ persistência
→ auditoria
```

sem depender do Workspace como requisito de domínio.

---

## 3. Resultado

A unidade foi implementada e validada em runtime real.

Foi demonstrado que:

- um PDF real pode ser incorporado a um Caso;
- o original é preservado;
- SHA-256 é persistido sobre os bytes armazenados;
- o storage usa referência relativa governada;
- duplicidade no mesmo Caso não cria segunda cópia;
- o mesmo conteúdo pode pertencer a outro Caso;
- o Original pode ser recuperado por rota governada;
- o documento persiste após reinicialização;
- conteúdo incompatível com a extensão é rejeitado;
- registros legados permanecem `metadata_only`;
- a migration não fabrica paths físicos;
- a operação é auditável;
- o serviço não exige Workspace.

---

## 4. Arquivos e componentes relevantes

### Implementação

```text
app/config.py
app/models/platea.py
app/routes/auth.py
app/routes/documents.py
app/services/document_intake_service.py
app/services/face_service.py
app/services/storage_service.py
app/templates/workspace.html
run.py
```

### Migrations

```text
alembic/versions/0009_at06b_curated_intake_storage.py
alembic/versions/0013_legacy_lineage_compat.py
```

### Smokes

```text
scripts/smoke_at06b_curated_workspace_ui.py
scripts/smoke_at06b_curated_document_http.py
scripts/smoke_at06b_curated_document_intake.py
scripts/smoke_at06b_curated_storage.py
scripts/smoke_at06b_curated_document_model.py
scripts/smoke_at06b_legacy_lineage.py
```

---

## 5. Commits relevantes

```text
c6171e1  feat(AT-06B): establish canonical physical document storage
b992882  feat(AT-06B): implement transactional case document intake
dc48a88  feat(AT-06B): expose governed document intake and retrieval
4b7e644  feat(AT-06B): integrate case document intake into workspace
c366db8  fix(AT-06B): bridge legacy Alembic lineage for curated intake
35ad3fb  test(AT-06B): decouple workspace smoke from visual wording
2f5c1e2  fix(runtime): lazy-load optional facial recognition stack
b7e294a  fix(dev): restore audited localhost auth bypass
```

Os dois últimos commits são estabilizações descobertas durante a validação e não redefinem o contrato do intake.

---

## 6. Banco e Alembic

Head validado:

```text
0009_at06b_curated_intake_storage (head)
```

O banco real da máquina de trabalho foi migrado a partir da linhagem legada:

```text
0013_at06b63_facts_topic_composition
```

Foi validado que:

- tabelas e registros legados foram preservados;
- documentos metadata-only continuaram válidos;
- nenhum `storage_relpath` foi fabricado;
- segundo upgrade permaneceu estável.

O banco operacional local não deve ser transportado pelo Git.

---

## 7. Testes e evidências

Bateria AT-06B validada:

```text
AT-06B-CURATED-01 WORKSPACE UI SMOKE: OK
AT-06B-CURATED-01 DOCUMENT HTTP SMOKE: OK
AT-06B-CURATED-01 DOCUMENT INTAKE SMOKE: OK
AT-06B-CURATED-01 STORAGE SMOKE: OK
AT-06B-CURATED-01 DOCUMENT MODEL SMOKE: OK
AT-06B LEGACY LINEAGE SMOKE: OK
git diff --check: sem erro
```

Teste manual real comprovou:

```text
upload real
→ DISPONÍVEL
→ recuperação do Original
→ duplicidade bloqueada
→ restart
→ persistência
→ Original ainda recuperável
```

Prova mecânica:

```text
physical_originals = 1
REAL PHYSICAL PERSISTENCE: OK
```

Teste negativo manual:

```text
arquivo .pdf com conteúdo inválido
→ rejeitado
→ nenhuma nova cópia
```

---

## 8. Decisões congeladas

A partir deste fechamento, não alterar silenciosamente:

- material pertence ao Caso;
- original é soberano;
- SHA-256 identifica os bytes persistidos;
- storage é governado pela aplicação;
- referência física é relativa/opaca;
- deduplicação ocorre no escopo do Caso;
- recuperação do Original é governada;
- auditoria é obrigatória;
- serviço de intake independe do Workspace;
- legado metadata-only permanece válido.

O redesign pode substituir a apresentação, composição, labels e microinterações sem reabrir esses contratos.

Mudanças de contrato exigem nova SPEC/ADR.

---

## 9. Estabilizações laterais

### InsightFace

Commit:

```text
2f5c1e2
```

Foi validado:

```text
import app.services.face_service: OK
import app.services.photo_service: OK
import run: OK
```

Objetivo do patch:

> falha do subsistema opcional InsightFace/ONNX não deve impedir o ATHENA de iniciar.

**Não foi validado reconhecimento facial/CUDA end-to-end.**

### DEV_AUTH_BYPASS

Commit:

```text
b7e294a
```

Características:

- desligado por padrão;
- depende de `DEV_AUTH_BYPASS=true`;
- restrito a localhost;
- operador `dev-local`;
- ação auditada;
- operador local inativo não recebe sessão automática.

---

## 10. Baseline de ambiente

Baseline Windows validada:

```text
Windows x64
Python 3.11.9
.venv local criada do zero
requirements.txt
Alembic
smokes
startup em 127.0.0.1:8766
```

Não copiar `.venv` entre máquinas.

Python 3.12 não é a baseline validada desta versão.

Fonte operacional:

`ATHENA-ENVIRONMENT-BASELINE-WINDOWS-v1.0-2026-08-27.md`

---

## 11. Estado do Git no fechamento técnico

```text
REPO: C:\Projetos\CIRCE_ATHENA
REMOTE: https://github.com/Prjkt-CIRCE/CIRCE-ATHENA.git
BRANCH: feat/at06b-curated-01-intake-storage
HEAD TÉCNICO: b7e294a
LOCAL == ORIGIN: sim
WORKING TREE: limpa
```

Este HEAD é o checkpoint técnico anterior ao commit dos documentos de fechamento.

---

## 12. Documentação de fechamento

Documentos canônicos preparados em 27/08/2026:

### SUBSTITUI fonte anterior

```text
SPEC-AT06B-CURATED-01-INTAKE-FISICO-v1.0-2026-08-27.md
```

Substitui:

```text
SPEC-AT06B-CURATED-01-INTAKE-FISICO-v0.2-2026-08-25.md
```

### SUBSTITUI fonte anterior

```text
CIRCE-ATHENA-PROJECT-MASTER-CONSOLIDADO-2026-08-27.md
```

Substitui:

```text
CIRCE-ATHENA-PROJECT-MASTER-CONSOLIDADO-2026-08-25.md
```

### COMPLEMENTA / NÃO SUBSTITUI

```text
ATHENA-ENVIRONMENT-BASELINE-WINDOWS-v1.0-2026-08-27.md
```

### COMPLEMENTA / NÃO SUBSTITUI

```text
HANDOFF-AT06B-CURATED-01-2026-08-27.md
```

---

## 13. Pendências não bloqueantes

- InsightFace/ONNX/CUDA end-to-end permanece pendente;
- a integração visual atual do intake é mínima e será substituível pelo redesign aprovado;
- smokes históricos fora da bateria nominal AT-06B podem ser reexecutados no gate de integração, se necessário.

---

## 14. Roadmap atualizado

Próxima sequência oficial:

```text
FECHAMENTO-AT06B-CURATED-01
→ commit documental
→ push
→ PR
→ merge

depois:

REVIEW-DESIGN-WORKSPACE-01
→ revisar proposta de redesign
→ classificar impactos
→ aprovar / corrigir / devolver ao Design Lab

depois:

ELEIÇÃO DA PRÓXIMA SPEC
→ AT-06B-CURATED-02 — Intake Visual / Pool mínimo
OU
→ VERTICAL-SLICE-REPORT-01
```

A escolha da próxima SPEC não é automática.

---

## 15. Próxima unidade

`REVIEW-DESIGN-WORKSPACE-01`

Objetivo:

> Revisar a proposta de redesign do Workspace contra contratos funcionais e arquiteturais já congelados antes de qualquer implementação visual ampla.

Classificar cada mudança proposta como:

```text
apresentação
layout/composição
microinteração
fluxo operacional
alteração de contrato
nova funcionalidade
```

Resultado obrigatório:

```text
APROVADO
APROVADO COM CORREÇÕES
RETORNAR AO DESIGN LAB
```

---

## 16. Arquivos que devem acompanhar o próximo chat

No mínimo:

```text
CIRCE_SPEC_DRIVEN_WORKFLOW_v1.0_2026-08-25.md
CIRCE-ATHENA-PROJECT-MASTER-CONSOLIDADO-2026-08-27.md
SPEC-AT06B-CURATED-01-INTAKE-FISICO-v1.0-2026-08-27.md
DS-SPEC-001-DESIGN-SYSTEM-VISUAL-CIRCE-ATHENA-v1.0-2026-08-25.md
ATHENA-ENVIRONMENT-BASELINE-WINDOWS-v1.0-2026-08-27.md
HANDOFF-AT06B-CURATED-01-2026-08-27.md
```

Adicionar também o mock/proposta visual mais recente do Workspace quando a revisão de design começar.

---

## 17. Prompt recomendado para a próxima unidade

```text
PROJETO:
CIRCE-ATHENA

UNIDADE:
REVIEW-DESIGN-WORKSPACE-01

OBJETIVO:
Revisar a proposta de redesign do Workspace antes de qualquer implementação.

BASELINE TÉCNICA:
AT-06B-CURATED-01 concluída e validada.
Backend de intake físico congelado.
Último HEAD técnico antes do commit documental: b7e294a.

FONTES:
- CIRCE Spec-Driven v1.0
- Project Master 27/08/2026
- SPEC AT-06B-CURATED-01 v1.0
- DS-SPEC-001 v1.0
- Environment Baseline Windows v1.0
- HANDOFF AT-06B-CURATED-01
- proposta/mock de redesign

REGRAS:
- não implementar antes da revisão;
- preservar contratos congelados;
- separar apresentação de mudança funcional;
- qualquer alteração de contrato exige nova SPEC/ADR.

PRIMEIRA AÇÃO:
Ler as fontes e classificar a proposta de redesign em apresentação, composição, microinteração, fluxo, alteração de contrato ou nova funcionalidade.
```

---

## 18. Regra documental vigente

Toda documentação nova ou atualizada deve declarar explicitamente uma das relações:

```text
SUBSTITUI / SUPERSEDE
ou
COMPLEMENTA / NÃO SUBSTITUI
```

Na entrega ao usuário, deve ser indicado claramente:

- qual fonte antiga deve ser substituída;
- qual fonte deve ser mantida;
- qual documento novo apenas complementa o conjunto.
