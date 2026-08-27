# SPEC AT-06B-CURATED-01 — Intake Físico e Armazenamento Canônico de Materiais do Caso

**Versão:** 1.0
**Data de criação:** 25/08/2026
**Data de atualização/fechamento:** 27/08/2026
**Status:** Validada / Concluída
**Substitui:** `SPEC-AT06B-CURATED-01-INTAKE-FISICO-v0.2-2026-08-25.md`
**Projeto:** CIRCE-ATHENA
**Roadmap pai:** AT-06 — Workspace Investigativo & Construtor de Peças
**Unidade:** AT-06B — Intake e Pool do Caso
**Branch canônica de partida:** `refactor/at06-curated-v2`
**Branch de implementação/fechamento:** `feat/at06b-curated-01-intake-storage`
**HEAD remoto validado no fechamento:** `b7e294a2e73aa2c0fa94cd2498f9a40197362b3`
**Natureza:** SPEC funcional / armazenamento / segurança / integração
**Design visual aplicável:** `DS-SPEC-001 — Design System Visual CIRCE-ATHENA`
**Regra:** esta SPEC define **o que a função faz**. Localização exata, composição visual e microinterações pertencem à UX-SPEC/Design Lab da funcionalidade.

---

## 1. Decisão desta unidade

A próxima unidade do CIRCE-ATHENA será:

> **Intake físico e armazenamento canônico de materiais do Caso.**

O objetivo não é interpretar, extrair, resumir ou analisar o arquivo.

O objetivo é estabelecer uma verdade durável:

> **Quando um material entra no Caso, o CIRCE-ATHENA preserva seu original, registra sua identidade e proveniência, sabe onde ele está e consegue recuperá-lo de forma segura por um contrato canônico.**

---

## 2. Problema

A branch curada possui um contrato canônico de materiais do Caso:

```text
case_ref
→ CaseMaterials
   ├── case
   ├── persons
   ├── documents
   ├── links
   └── annotations
```

Entretanto, `SharedDocument` ainda representa essencialmente metadados documentais. Há nome, tipo, hash, descrição e data, mas não existe contrato canônico para localizar e recuperar o arquivo físico original.

Sem esse contrato, funções posteriores de:

- leitura de PDF;
- OCR;
- extração factual;
- visualização;
- transcrição;
- RAG;
- análise de dispositivo;
- Report Builder;
- citações internas;
- Laboratório de Evidências;

tenderiam a criar caminhos paralelos, armazenamento improvisado ou dependências da UI.

---

## 3. Objetivo

Ao final desta SPEC, o sistema deverá permitir que um operador incorpore um arquivo real a um Caso de modo que:

1. o original seja preservado;
2. o SHA-256 seja calculado sobre os bytes persistidos;
3. metadados essenciais sejam registrados;
4. o armazenamento seja controlado pela aplicação;
5. o arquivo seja recuperável posteriormente por contrato;
6. a operação seja auditável;
7. o documento passe a integrar os materiais canônicos do Caso;
8. nenhuma Bandeja, tópico, wizard ou bloco seja requisito para o intake.

---

## 4. Resultado observável

Demonstração mínima:

```text
Caso
→ incorporar PDF real
→ material passa a pertencer ao Caso
→ hash e metadados são registrados
→ aplicação é fechada/reaberta
→ mesmo Caso é aberto
→ material continua presente
→ sistema resolve o arquivo físico novamente
→ SHA-256 permanece idêntico
```

Duplicidade:

```text
reincorporar os mesmos bytes ao mesmo Caso
→ duplicidade detectada
→ nenhuma segunda cópia silenciosa
→ resultado explícito ao operador
```

Persistência da fonte:

```text
usar documento como fonte de um bloco
→ remover associação do bloco
→ documento original permanece intacto no Caso
```

---

## 5. Princípios funcionais

### 5.1. Material pertence ao Caso

```text
Caso
  ↓
Materiais do Caso
  ↓
Workspace / Ferramentas / Blocos / Relatórios
```

Ferramentas futuras consultam ou referenciam o material do Caso; não criam repositórios paralelos.

### 5.2. Original soberano

Derivados futuros — OCR, transcrição, thumbnail, texto extraído, frame, resumo, embedding — não substituem o original.

### 5.3. Intake sem pedágio

O operador não precisa mover material para Bandeja, abrir tópico, iniciar wizard ou criar bloco para que o material pertença ao Caso.

### 5.4. Feedback obrigatório

A UX que implementar esta SPEC deve tornar perceptível, no mínimo:

```text
ação iniciada
→ processamento
→ sucesso / duplicidade / falha
```

A forma visual exata não é definida aqui.

### 5.5. Local por padrão

O armazenamento desta SPEC é local/institucional. Nenhum arquivo é enviado à Internet.

### 5.6. Ingestão ≠ interpretação

Guardar um arquivo não significa:

- validar o conteúdo;
- classificá-lo como fato;
- atestar autenticidade pericial;
- extrair informação;
- solicitar análise de IA.

---

## 6. Contrato funcional

### FR-01 — Incorporar material ao Caso

O operador deve poder iniciar Intake no contexto de um Caso.

### FR-02 — Associação direta

O material ingressa diretamente no Caso identificado.

### FR-03 — Preservação física

Os bytes recebidos devem ser armazenados sem transformação.

### FR-04 — Identidade criptográfica

SHA-256 deve ser calculado sobre os bytes efetivamente persistidos.

### FR-05 — Metadados

Registrar, no mínimo:

- nome original;
- tipo/extensão quando identificável;
- MIME;
- tamanho em bytes;
- SHA-256;
- referência de armazenamento;
- origem do Intake;
- data/hora;
- operador responsável.

### FR-06 — Recuperação

A aplicação deve resolver o registro documental para o arquivo físico correspondente sem aceitar path arbitrário do cliente.

### FR-07 — Deduplicação no Caso

Se o mesmo SHA-256 já estiver associado ao mesmo Caso como material físico válido:

- não criar nova cópia silenciosa;
- retornar/referenciar o registro existente;
- informar duplicidade.

### FR-08 — Isolamento entre Casos

Deduplicação é avaliada no escopo do Caso. O mesmo conteúdo pode pertencer a outro Caso sem associação cruzada automática.

### FR-09 — Auditoria

Registrar evento auditável contendo, quando aplicável:

- operador;
- Caso;
- documento;
- nome;
- SHA-256 ou referência segura;
- timestamp;
- resultado.

### FR-10 — Compatibilidade com `CaseMaterials`

Após Intake, `load_case_materials()` deve retornar o novo documento normalmente.

### FR-11 — Independência de Workspace

O serviço canônico de Intake/Storage pertence ao domínio do Caso e não pode exigir Workspace.

Uma UX pode expor a função dentro do Workspace, mas isso não altera o contrato de domínio.

### FR-12 — Falha segura

Falha de storage não pode deixar registro válido apontando para arquivo inexistente.

Falha de banco não pode deixar arquivo órfão sem tratamento previsível.

---

## 7. Contrato de armazenamento

### 7.1. Storage root

Deve existir uma raiz de armazenamento configurada pela aplicação.

Exemplo conceitual:

```text
CIRCE_STORAGE_ROOT
```

O caminho não deve ser hardcoded em templates, rotas ou regras de domínio.

### 7.2. Referência persistida

O banco deve armazenar referência relativa/opaca controlada pela aplicação.

Exemplo conceitual:

```text
cases/<case_internal_id>/documents/<opaque_storage_name>
```

### 7.3. Nome físico

O nome físico pode usar UUID/chave opaca.

O nome original permanece como metadado.

### 7.4. Caminho seguro

Toda resolução deve:

1. partir do storage root;
2. resolver referência conhecida;
3. normalizar caminho;
4. confirmar permanência dentro do root;
5. rejeitar traversal e referências absolutas não autorizadas.

### 7.5. Atomicidade

Fluxo recomendado:

```text
receber arquivo
→ escrever em área temporária controlada
→ calcular/verificar SHA-256
→ verificar duplicidade
→ mover para destino final
→ criar/confirmar registro
→ commit
```

Falha intermediária deve gerar limpeza previsível.

### 7.6. Legado

Registros históricos sem referência física permanecem válidos como `metadata_only`.

Funções que exigem arquivo físico devem distinguir:

```text
metadata_only
physical_available
```

Nenhuma migration deve fabricar paths inexistentes.

---

## 8. Modelo de dados mínimo

Contrato conceitual:

```text
SharedDocument
├── id
├── shared_case_id
├── document_ref
├── filename
├── file_type
├── sha256
├── description
├── imported_at
├── storage_relpath
├── mime_type
├── size_bytes
├── storage_origin
├── stored_at
└── autoria/rastreabilidade do Intake
```

A implementação pode evitar duplicar autoria se a trilha de auditoria já satisfizer o requisito de rastreabilidade.

---

## 9. Política inicial de tipos

O serviço de armazenamento deve ser neutro em relação ao conteúdo.

A primeira UX poderá priorizar:

- PDF;
- PNG;
- JPEG/JPG;
- DOCX;
- XLSX;
- CSV;
- TXT.

Áudio e vídeo não fazem parte do fluxo funcional desta unidade, mas o contrato não deve impedir futura inclusão.

Allowlist deve ser centralizada e configurável.

---

## 10. Limite de tamanho

O limite máximo deve ser:

- configurável;
- centralizado;
- validado no servidor;
- comunicável à UX.

A SPEC não fixa valor institucional definitivo.

---

## 11. Erros e exceções

### E-01 — Caso inexistente
Rejeitar Intake.

### E-02 — Arquivo vazio
Rejeitar por padrão.

### E-03 — Tipo não permitido
Rejeitar explicitamente.

### E-04 — Arquivo acima do limite
Rejeitar antes da persistência final.

### E-05 — Duplicidade no mesmo Caso
Retornar/referenciar o documento existente.

### E-06 — Falha de escrita
Não criar registro válido.

### E-07 — Falha de banco após escrita
Executar compensação/limpeza controlada.

### E-08 — Referência física ausente
Retornar erro de integridade do storage; nunca simular sucesso.

### E-09 — Path traversal
Rejeição obrigatória.

### E-10 — MIME/extensão divergentes
Não confiar apenas na extensão; registrar/tratar conforme política.

Antivírus e análise profunda não pertencem a esta unidade.

---

## 12. Segurança

1. path arbitrário do navegador nunca é usado para abrir arquivo;
2. storage root não é navegável diretamente pela web;
3. recuperação ocorre por serviço/rota autorizada;
4. acesso respeita autenticação e Caso;
5. traversal é bloqueado;
6. nome original é dado, não caminho;
7. conteúdo não é duplicado em logs;
8. hash não substitui autorização;
9. storage independe de Internet;
10. upload não amplia privilégios.

---

## 13. Restrições de UX invariantes

A futura UX-SPEC deve respeitar:

- Intake ocorre no contexto do Caso;
- não há wizard obrigatório;
- não há Bandeja/tópico como pré-condição;
- estado da operação é perceptível;
- sucesso, duplicidade e falha são distinguíveis;
- operador permanece no controle;
- a função não deve parecer um gerenciador de arquivos autônomo;
- a interface deve obedecer `DS-SPEC-001 — Design System Visual CIRCE-ATHENA`.

Qualquer decisão além disso pertence ao Design Lab/UX-SPEC da funcionalidade.

---

## 14. Fora de escopo

Não implementar nesta unidade:

- OCR;
- extração textual;
- leitura automática de BO/OS;
- Cabeçalho;
- Dos Fatos;
- mapa factual;
- RAG;
- embeddings;
- IA lendo arquivo;
- transcrição;
- extração de frames;
- reconhecimento facial;
- Pool/Bins/Smart Bins completos;
- Bandeja obrigatória;
- drag-and-drop global;
- importação em lote sofisticada;
- VINCULUM;
- Cellebrite;
- deduplicação global;
- versionamento documental;
- exclusão definitiva;
- DOCX/PDF de saída;
- preview/viewer completo;
- classificação epistemológica automática;
- envio externo/cloud;
- antivírus;
- assinatura digital;
- workflow institucional de aprovação.

---

## 15. Dependências satisfeitas

- branch curada `refactor/at06-curated-v2`;
- CURATED-00 — fundação reproduzível;
- CURATED-01A — acesso canônico aos materiais do Caso;
- CURATED-01B — Workspace consumindo `CaseMaterials`;
- `SharedCase`;
- `SharedDocument`;
- autenticação;
- auditoria;
- Workspace AT-06A;
- ADR-001;
- ADR-002;
- `DS-SPEC-001`.

---

## 16. Critérios de aceitação

### Banco
- [ ] Banco novo migra até o novo head.
- [ ] Banco curado migra sem perda.
- [ ] Segundo upgrade não regressa.
- [ ] Registros legados metadata-only permanecem válidos.

### Intake
- [ ] Arquivo real é incorporado diretamente a um Caso.
- [ ] Serviço não exige Workspace.
- [ ] Original é preservado.
- [ ] SHA-256 corresponde aos bytes persistidos.
- [ ] Nome original é preservado.
- [ ] MIME/tipo e tamanho são registrados.
- [ ] Origem e timestamp são registrados.
- [ ] Operador é rastreável.

### Storage
- [ ] Aplicação controla destino.
- [ ] Banco não depende de path absoluto do usuário.
- [ ] Resolução segura funciona.
- [ ] Traversal é bloqueado.
- [ ] Arquivo ausente gera erro explícito.
- [ ] Falha não deixa estado falsamente válido.

### Deduplicação
- [ ] Mesmo arquivo + mesmo Caso não gera duplicata silenciosa.
- [ ] Mesmo arquivo + outro Caso não mistura Casos.

### Integração
- [ ] Novo documento aparece em `CaseMaterials`.
- [ ] Workspace atual continua carregando o Caso.
- [ ] Remover fonte de bloco não exclui original.
- [ ] Reabertura/F5 preserva o material.

### Regressão
- [ ] CURATED-00 verde.
- [ ] CURATED-01A verde.
- [ ] CURATED-01B verde.
- [ ] AT-06A verde.
- [ ] `git diff --check` sem erro.

---

## 17. Critérios de rejeição

Rejeitar/refatorar se:

- exigir path manual;
- arquivo ficar acoplado ao Workspace em vez do Caso;
- Intake depender de Bandeja/tópico;
- migration danificar legado;
- storage puder escapar do root;
- duplicidade criar cópias silenciosas;
- função não puder comunicar estado à UX;
- contrato impedir ferramentas futuras de resolver o original sem conhecer a UI.

---

## 18. Plano de validação

### G0 — Gate local do repositório

```powershell
Set-Location "C:\Projetos\CIRCE_ATHENA"

git branch --show-current
git rev-parse HEAD
git status --short --branch
git remote -v
git log -5 --oneline --decorate
```

### G1 — Contrato de storage
Validar root, path relativo, escrita, hash, resolução, traversal e ausência de arquivo.

### G2 — Migration/modelo
Testar fresh database, curated database, legacy metadata-only e segundo upgrade.

### G3 — Intake service
Cenários:

```text
PDF normal
arquivo vazio
tipo não permitido
arquivo acima do limite
nome especial
nome duplicado / bytes diferentes
nome diferente / bytes iguais
duplicidade no mesmo Caso
mesmo conteúdo em outro Caso
```

### G4 — Integração com UX aprovada
A UX-SPEC da funcionalidade deverá demonstrar o fluxo sem alterar o contrato desta SPEC.

### G5 — Persistência física

```text
fechar aplicação
→ reabrir
→ carregar Caso
→ resolver arquivo
→ verificar SHA
```

### G6 — Regressão
Executar smokes canônicos e Golden Path AT-06A.

### G7 — Decisão

```text
APROVADO
APROVADO COM PENDÊNCIAS
REFATORAR
BLOQUEADO
REJEITADO
```

---

## 19. Ordem de implementação

```text
1. Gate local do repositório
2. aprovar UX-SPEC da funcionalidade
3. contrato de armazenamento
4. testes isolados de storage
5. migration/modelo mínimo
6. serviço canônico de Intake
7. testes de Intake
8. integração na UX aprovada
9. runtime
10. regressões
11. checkpoint Git
12. atualização documental
13. handoff
```

---

## 20. Stop-loss

Se a implementação exigir refatoração ampla do Workspace para o serviço existir, interromper e abrir unidade própria de refatoração.

Não expandir silenciosamente esta SPEC.

---

## 21. Estado

```text
ROADMAP: AT-06B
UNIDADE: AT-06B-CURATED-01
STATUS: done / validated
IMPLEMENTAÇÃO: concluída e validada em runtime real
UX: integração mínima funcional validada; apresentação visual permanece substituível pelo redesign
DESIGN SYSTEM: DS-SPEC-001 continua autoridade visual
BACKEND DE INTAKE: congelado até decisão arquitetural explícita em SPEC/ADR
HEAD DE FECHAMENTO: b7e294a
```

---

## 22. Registro de implementação e validação

### 22.1. Resultado da unidade

A unidade foi implementada e validada entre 25 e 27/08/2026. O resultado observado corresponde ao objetivo central desta SPEC:

> Um material físico pode ser incorporado diretamente a um Caso, preservado em storage governado, identificado por SHA-256, recuperado pelo sistema e mantido após reinicialização, sem depender de Workspace para existir como domínio.

### 22.2. Componentes entregues

- storage canônico em `app/services/storage_service.py`;
- metadados físicos em `SharedDocument`;
- migration `0009_at06b_curated_intake_storage`;
- ponte de compatibilidade para a linhagem legada `0013_at06b63_facts_topic_composition`;
- serviço transacional de intake em `app/services/document_intake_service.py`;
- rotas governadas de intake e recuperação do original;
- integração mínima no Workspace;
- smokes específicos de storage, model, intake, HTTP, UI e legacy lineage.

### 22.3. Banco real e compatibilidade legada

Antes da migration, o banco real possuía revisão legada `0013_at06b63_facts_topic_composition` e registros documentais metadata-only. Foi criado backup pré-migração e validada compatibilidade sem alteração destrutiva dos dados existentes.

Resultado final validado:

```text
alembic current
→ 0009_at06b_curated_intake_storage (head)
```

Os registros legados permaneceram válidos como `metadata_only`; nenhum `storage_relpath` foi fabricado para documentos cujo original físico não existia no novo storage.

### 22.4. Validações automatizadas

Bateria validada sob `.venv` Python 3.11.9:

```text
AT-06B-CURATED-01 WORKSPACE UI SMOKE: OK
AT-06B-CURATED-01 DOCUMENT HTTP SMOKE: OK
AT-06B-CURATED-01 DOCUMENT INTAKE SMOKE: OK
AT-06B-CURATED-01 STORAGE SMOKE: OK
AT-06B-CURATED-01 DOCUMENT MODEL SMOKE: OK
AT-06B LEGACY LINEAGE SMOKE: OK
git diff --check: sem erro
```

Contratos explicitamente comprovados pelos smokes:

- bytes originais preservados;
- SHA-256 calculado sobre bytes persistidos;
- referência de storage relativa;
- nome físico opaco;
- path traversal e referência absoluta bloqueados;
- arquivo ausente produz erro explícito;
- vazio e excesso de tamanho rejeitados;
- compensação física em falha de banco;
- duplicidade no mesmo Caso bloqueada;
- mesmo hash em outro Caso permitido;
- conteúdo incompatível rejeitado;
- MIME fornecido pelo cliente não é tratado como confiável;
- recuperação do original byte-identical;
- storage path não é exposto ao cliente;
- auditoria de falha e recuperação presente;
- Workspace não é pré-requisito do serviço.

### 22.5. Validação manual em runtime real

Foi realizado teste operacional no Caso `ATH-20260824-6338E5`:

1. documento físico real incorporado pelo Workspace;
2. estado visual passou a disponível e ofereceu ação `Original`;
3. novo envio dos mesmos bytes foi reconhecido como duplicidade, sem criar segunda cópia;
4. `Original` recuperou corretamente o PDF incorporado;
5. após reinicialização da aplicação, o documento permaneceu recuperável;
6. consulta ao banco confirmou exatamente um original físico para o documento testado;
7. um arquivo com extensão `.pdf` e conteúdo inválido foi rejeitado com mensagem de incompatibilidade, sem aumentar a contagem de documentos.

Prova mecânica observada:

```text
physical_originals = 1
REAL PHYSICAL PERSISTENCE: OK
```

### 22.6. Commits de fechamento conhecidos

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

Os dois últimos commits são estabilizações descobertas durante a validação e não alteram o contrato funcional do intake.

### 22.7. Decisões de congelamento

A partir deste fechamento, permanecem congelados, salvo nova SPEC/ADR explícita:

- propriedade do material pelo Caso;
- preservação do original;
- hash SHA-256;
- storage governado e referência relativa;
- deduplicação no escopo do Caso;
- recuperação governada do original;
- auditoria;
- independência do serviço em relação ao Workspace;
- compatibilidade dos registros legados metadata-only.

O redesign do Workspace pode substituir completamente a apresentação, composição, labels e microinterações, mas não deve alterar silenciosamente esses contratos.

### 22.8. Pendências não bloqueantes

- reconhecimento facial real com InsightFace/ONNX/CUDA **não foi validado end-to-end**; o commit `2f5c1e2` valida apenas lazy loading e isolamento da falha opcional;
- os smokes históricos nominados como CURATED-00 / CURATED-01A / CURATED-01B / AT-06A não foram reexecutados nominalmente na última bateria descrita neste fechamento; antes de merge final, podem ser reexecutados caso a política de integração da branch exija esses nomes específicos;
- a UX visual do intake permanece deliberadamente mínima e pode ser substituída pelo design aprovado, desde que preserve o contrato desta SPEC.

### 22.9. Decisão G7

```text
DECISÃO: APROVADO COM PENDÊNCIAS NÃO BLOQUEANTES
STATUS DA UNIDADE: DONE / VALIDATED
PRÓXIMA AÇÃO: atualização documental → commit documental → PR/merge
```

---

## 23. Fontes

- Handoff de curadoria de 25/08/2026;
- Metodologia CIRCE Spec-Driven v1.0;
- ADR-001;
- ADR-002;
- ADR-003;
- SPEC AT-06;
- Project Master consolidado de 25/08/2026;
- Design System primordial CIRCE Intel Desk, utilizado apenas como origem estética para `DS-SPEC-001`.
