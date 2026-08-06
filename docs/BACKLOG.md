# Cerebro Backlog

> Living roadmap shared across Claude Code sessions.
> **Read this at session start. Update status when you complete an item.**
> Format: `- [ ] item — notes`

Direção registrada em [ADR-0076](../../adr-ledger/adr/proposed/ADR-0076.md) —
*Architecture Conformance Engine: de inventário para avaliação estrutural*.

---

## 0. Acoplamento com PHANTOM — **decisão do operador, 2026-08-03**

O motor de conformance e o PHANTOM evoluem **juntos**, não em paralelo isolado. Ambos
resolvem o mesmo problema em domínios diferentes — extrair estrutura de um corpus e julgar
conformidade contra uma norma — e compartilham as mesmas restrições (soberania do dado,
local-first, storage do índice).

- [ ] Mapear o que já é duplicado entre cerebro e phantom antes de construir a fase 1 — ambos
  fazem chunking, embedding e indexação; a fase 2 do conformance vai precisar de grafo
  persistido e o phantom já resolveu persistência de índice
- [ ] Decidir se o grafo de dependência é um índice novo ou uma coleção dentro do
  substrato de retrieval que o phantom já opera
- [ ] Alinhar o pipeline de sanitização: se o motor for rodar sobre repos de terceiros, o
  código-fonte alheio é dado sensível e passa pelas mesmas garantias que o phantom já dá a
  documento (o DAG `strip_metadata → redact_pii → full_sanitize` tem análogo aqui)
- [ ] Reaproveitar a arquitetura de provider adapter do phantom em vez de manter duas
  abstrações de LLM/embedding divergentes no ecossistema
- [ ] O `judge` do phantom e o `conformance checker` são a mesma forma de problema
  (predicado avaliado contra evidência, com veredito rastreável) — avaliar núcleo comum

## 1. Storage — **ADR pendente**

Decisão de desenho já tomada com o operador (2026-08-03), falta registrar em ADR próprio:

- [ ] Escrever ADR-0077: SQLite local como fonte de verdade, GCS como redundância cifrada
- [ ] SQLite para grafo e série temporal — a matriz de co-commit é grande em linhas, pequena
  em bytes, single-writer e batch; JSON em bucket exigiria varredura completa por consulta
- [ ] GCS para durabilidade, **cifrado client-side com AGE antes do upload** — Google entrega
  durabilidade, nunca vê plaintext; mesmo padrão SOPS/AGE já usado em securellm-bridge,
  owasaka e adr-ledger
- [ ] Storage class Nearline ou Coldline — padrão de acesso é "nunca, até o desastre"
- [ ] Chave AGE em caminho de recuperação **independente do bucket** — modo clássico de
  falhar é backup cifrado com a chave junto do backup
- [ ] Procedimento de restore exercitado, com data da última verificação registrada — o scan
  de 2026-08-03 mostrou 0 de 33 repos com runbook; backup nunca restaurado é esperança
- [ ] Hash do snapshot ancorado na chain do adr-ledger (integridade, não confidencialidade)

## 2. Fase 1 — Dinâmica (só precisa do git)

Barata, alto sinal, não paga custo de resolução de símbolo cross-linguagem.

- [ ] Matriz de co-commit por par de arquivos/módulos a partir do histórico git
- [ ] Identificar pares com alto acoplamento temporal e **zero** dependência estática —
  o acoplamento que nenhuma análise estática vê
- [ ] Hotspots: complexidade × frequência de mudança, por arquivo e agregado por módulo
- [ ] Piso mínimo de commits e janela temporal por repo; abaixo disso a dimensão é N/A,
  seguindo o princípio de que ausência de dado não é nota zero
- [ ] **GATE DE SINAL**: apontar ao menos um acoplamento oculto real e não-óbvio no
  ecossistema. Se só confirmar o já sabido, a técnica não paga o custo e a fase 2 não começa.

## 3. Fase 2 — Estrutura

- [ ] Profundidade de módulo (Ousterhout): razão superfície_de_interface / LOC_implementação;
  módulo raso = interface larga sobre implementação fina = abstração que não abstrai
- [ ] Amplificação de mudança: distribuição de arquivos tocados por commit, segmentada por
  tipo (feat/fix/refactor via conventional commits)
- [ ] Grafo de dependência estático cross-linguagem via Tree-sitter — começar por Python e
  TypeScript, juntos 304K das 533K linhas autorais
- [ ] Métricas de Martin: Ca, Ce, instabilidade I, abstratividade A, distância D da sequência
  principal — **documentar a definição de A adotada por linguagem**, é ambígua em
  Python/Rust/Go e precisa ser defendida, não herdada
- [ ] Modularidade emergente por Louvain vs fronteiras de módulo declaradas — divergência
  alta significa que as pastas mentem sobre a estrutura
- [ ] Raio de explosão por percolação: se o nó X cai, que fração do sistema fica inalcançável

## 4. Fase 3 — Conformance (o diferencial)

- [ ] Extrair invariantes verificáveis de ADRs já aceitos, **retroativamente e à mão** —
  provar valor antes de exigir mudança de schema
- [ ] Checker: avaliar cada invariante contra o grafo observado
- [ ] Reportar violação **com a data de aceite do ADR e o commit que a introduziu** — a
  atestação OpenTimestamps permite medir desde quando a violação existe
- [ ] Erosão como derivada: série temporal da distância entre declarado e observado; o
  produto é a tendência, não o valor absoluto
- [ ] Avaliar evolução do schema de ADR para campo de invariantes checáveis (ADR próprio,
  decisão de governança)

## 5. Transversal

- [ ] Definir licença open source e política de versionamento do rubric antes da primeira
  abertura pública — decisão de rumo já registrada no ADR-0076
- [ ] Toda métrica nova entra com **frase de interpretação obrigatória** e um exemplo tirado
  do próprio ecossistema — mitigação contra repetir, em outra escala, o erro de construir
  métrica ininterpretável
- [ ] Hierarquia explícita entre o rubric de 11 dimensões atual e as métricas estruturais
  durante a transição; hoje coexistiriam sem ordenação clara
- [ ] Validação externa do score: sem incidentes medidos, rotatividade ou custo de manutenção
  registrado, o rubric é opinião formalizada. É o passo que separa ferramenta de produto.

## 6. Débitos conhecidos do coletor atual (2026-08-03)

- [ ] `centrality` só enxerga input de flake — adr-ledger marca 28/100 sendo lido por cerebro,
  phantom e spectre via `knowledge/*.json`. A fase 1 resolve isso por outro caminho.
- [ ] Pesos do rubric são hand-tuned, defensáveis mas não calibrados empiricamente
- [ ] Flake do cerebro não expõe `packages`/`checks`/`apps` — reprodutibilidade 70/100 contra
  88–94 dos serviços irmãos; o dev shell funciona, o contrato de build está incompleto
- [ ] `legacy/` ainda presente (2 arquivos), migração não concluída
- [ ] Sem `SECURITY.md`, sem threat model, apesar de lidar com credencial de três providers
- [ ] Sem runbook operacional
