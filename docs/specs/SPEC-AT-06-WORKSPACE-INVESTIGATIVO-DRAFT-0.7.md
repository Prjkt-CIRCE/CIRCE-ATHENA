# SPEC AT-06 — Workspace Investigativo & Construtor de Peças

**Versão:** Draft 0.7  
**Data:** 2026-08-22  
**Status:** Baseline funcional para AT-06B5  
**Produto:** CIRCE-ATHENA

## 1. Decisão estrutural

O ATHENA deve criar e operar casos de forma nativa. Integrações externas podem importar, sincronizar ou enriquecer casos, mas não constituem requisito para a existência do caso.

> **Caso nativo do ATHENA é canônico para novos fluxos.**

A nomenclatura interna legada `SharedCase` permanece temporariamente por compatibilidade e será regularizada em refatoração controlada posterior.

## 2. Criação nativa

O Gestor de Investigações deve oferecer `+ Novo caso`.

A criação exige apenas um título provisório. São opcionais:

- natureza/classificação;
- unidade/seção;
- observação inicial;
- materiais iniciais;
- roteiro inicial.

O sistema gera automaticamente:

- UUID interno;
- referência técnica segura para navegação;
- data de criação;
- operador criador;
- origem `native`;
- Workspace do caso.

Números oficiais de relatório, BO, IP, medida judicial, OS e outros identificadores institucionais não são chave técnica do caso e podem ser preenchidos/extrair posteriormente.

## 3. Intake inicial

Na criação do caso, o usuário pode anexar múltiplos materiais.

Cada arquivo deve:

1. ser preservado no armazenamento local soberano;
2. receber SHA-256;
3. registrar tamanho, MIME, nome original, operador e data;
4. entrar inicialmente na Bin `Entrada`;
5. manter relação com o caso;
6. não ser executado pela aplicação;
7. não ser duplicado quando o mesmo hash já existir no mesmo caso.

AT-06B5 não faz OCR nem classificação automática. Ela apenas estabelece o intake confiável.

## 4. Bin Entrada

`Entrada` é a área de chegada do material ainda não classificado/processado.

O fluxo futuro será:

`Entrada → hash/metadados → extração/OCR → classificação sugerida → confirmação humana → Bin/Smart Bins`

A fonte original permanece preservada independentemente das visões do Pool.

## 5. Intake contínuo

O caso evolui. Por isso o Workspace deve oferecer `+ Adicionar material` no Pool.

Novos arquivos seguem o mesmo contrato do intake inicial e entram em `Entrada`.

## 6. Roteiro inicial

Na criação, o usuário pode:

- iniciar o roteiro `Relatório Técnico — Análise de Dispositivo Móvel`; ou
- criar o caso sem roteiro.

O roteiro não altera os materiais originais.

## 7. Auditoria

Devem ser auditados:

- criação nativa do caso;
- quantidade de materiais iniciais;
- adição posterior de materiais ao caso;
- duplicados ignorados.

## 8. Limites AT-06B5

- até 50 arquivos por envio;
- até 250 MB por arquivo nesta vertical;
- armazenamento local em `data/cases/<case_uuid>/originals/`;
- sem OCR;
- sem parsing;
- sem preview binário;
- sem classificação automática;
- sem presets de cabeçalho ainda.

## 9. Próxima vertical real

Com um caso real criado nativamente e uma OS/BO no Pool, a próxima implementação prioritária é:

`OS/BO → extração estruturada → Cabeçalho proposto → revisão humana → preview no Inspector`.
