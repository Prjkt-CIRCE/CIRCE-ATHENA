# STATUS AT-06 — Handoff para Continuidade

**Data:** 2026-08-21
**Projeto:** CIRCE-ATHENA
**Unidade:** AT-06 — Workspace Investigativo & Construtor de Peças
**Branch:** `feat/at-06a-workspace-core`
**Baseline de origem:** `716b823 feat(AT-05): add local investigative context and governed assistant actions`

## 1. Caminhos conhecidos

### Máquina do trabalho

`C:\Projetos\CIRCE_ATHENA`

### Máquina de casa

`C:\Projetos\CIRCE-ATHENA`

## 2. Estado de banco

Baseline Alembic anterior:

`0005_platea`

AT-06 regularizou:

- `0006_at05_schema_reconciliation`;
- `0007_at06a_workspace_core`.

Estado validado:

`0007_at06a_workspace_core (head)`

Tabelas validadas:

- `shared_case_annotations`;
- `assistant_execution_preferences`;
- `investigative_workspaces`;
- `investigative_blocks`;
- `investigative_block_sources`.

Backup do banco foi realizado antes da migration.

## 3. Ambiente Python da máquina do trabalho

Usar sempre:

`C:\Projetos\CIRCE_ATHENA\.venv\Scripts\python.exe`

O comando `python` global da máquina do trabalho aponta para ambiente do Hermes Agent e não deve ser utilizado para o ATHENA.

## 4. AT-06A implementada até o handoff

### Núcleo

- Workspace 1:1 com Caso;
- criação automática de Workspace;
- Blocos Investigativos;
- associação de fontes;
- proveniência com chave estável + snapshot mínimo;
- contexto de Athena ligado a Caso e Bloco.

### Migrações

- reconciliação da AT-05;
- migration explícita do Workspace;
- Alembic regularizado para evolução controlada.

### Nomenclatura

Interface neutralizada:

- Gestor de Investigações;
- Caso;
- Workspace;
- proveniência nova `CASE:`.

Permanece internamente, por compatibilidade temporária:

- `/platea`;
- `app/models/platea.py`;
- `platea_service.py`;
- classes `Shared*`;
- tabelas `shared_*`;
- `platea_access_log`.

Dados antigos de teste contendo a palavra “Platea” não foram reescritos.

### Reversibilidade

- desfazer seleção;
- limpar seleção;
- remover fonte de bloco;
- desfazer criação de bloco por status `discarded`;
- auditoria de operações persistentes.

### Layout

- tiling redimensionável;
- divisores arrastáveis;
- persistência de largura;
- painéis Elementos e Blocos colapsáveis;
- restauração de layout;
- preservação de estado durante colapso.

### Testes

Smoke test validado:

`AT-06A SMOKE: OK`

Inclui criação de Workspace, Bloco, fontes e operações de undo.

`compileall` validado.

`git diff --check` sem erro; apenas warnings LF/CRLF no Windows.

## 5. Validação visual/operacional

Fluxo já validado:

`Gestor de Investigações → Caso → Abrir Workspace`

Bloco real de teste criado com fontes.

Athena reconheceu:

- Caso ativo;
- Bloco ativo.

O layout redimensionável/colapsável foi aprovado visualmente durante uso.

## 6. Nova decisão de produto

A AT-06 passa a evoluir para **Composição Investigativa Não Linear**.

Direção:

`Pool do Caso → Blocos Investigativos → Compositor da Peça → Viewer/Inspector → Produto`

Referência de interação: lógica de editores não lineares profissionais, especialmente Media Pool/Bins, composição e Inspector.

Não copiar visualmente DaVinci Resolve.

## 7. Próximo passo recomendado

Não partir ainda para DOCX/PDF.

Próximo incremento:

### Pool/Bins + Drag and Drop

Transformar a atual lista de Elementos do Caso em Pool do Caso com bins virtuais.

Primeira prova:

1. bins Pessoas / Documentos / Vínculos / Anotações;
2. expansão/recolhimento;
3. pesquisa;
4. seleção múltipla;
5. drag and drop para Bloco existente;
6. drop em área vazia para iniciar novo Bloco;
7. preservar proveniência e undo.

Depois:

- verificar isolamento contextual de Athena no Bloco;
- corrigir renderização Markdown crua na resposta da Athena;
- iniciar elementos epistemológicos da AT-06C;
- só depois avançar para Compositor da Peça.

## 8. Pendências conhecidas

1. Athena ainda pode exibir Markdown cru em algumas respostas.
2. Isolamento de contexto do Bloco precisa ser testado com caso contendo fontes externas ao bloco.
3. Rotas/modelos internos ainda carregam nomenclatura Platea.
4. Dados de teste contêm nomes legados.
5. Pool/Bins e drag and drop ainda não implementados.
6. Viewer/Inspector ainda é conceito futuro.
7. Report Builder ainda não implementado.
8. DOCX/PDF pertencem à AT-06E.

## 9. Gate para retomada em casa

Após puxar a branch:

```powershell
cd C:\Projetos\CIRCE-ATHENA
git fetch origin
git switch feat/at-06a-workspace-core
git pull --ff-only
git --no-pager log -1 --oneline
git status --short --branch
```

Em seguida:

```powershell
& ".\.venv\Scripts\python.exe" -m alembic current
& ".\.venv\Scripts\python.exe" -m scripts.smoke_at06a_workspace
```

Esperado:

- branch correta;
- worktree limpo;
- Alembic em `0007_at06a_workspace_core`;
- `AT-06A SMOKE: OK`.

## 10. Regra de continuidade

Não iniciar refatoração massiva de nomenclatura interna antes de validar Pool/Bins e drag and drop.

Não iniciar Report Builder antes de provar a linguagem de composição investigativa no Workspace.

O protótipo atual deve ser evoluído, não descartado.
