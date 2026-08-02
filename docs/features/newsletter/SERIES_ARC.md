# 🗺️ voidnxlabs intel — Arco da Série

> 10 edições. Cada uma compõe sobre a anterior. No fim, leitor tem um sistema completo de knowledge moat rodando.

---

## #001 — Você não precisa de mais cursos. Precisa de um knowledge moat. ✅
**Status:** Publicado.  
**Thesis:** A indústria de tutorial é teatro. Quem constrói indexa, não consome.  
**Cobre:** Inner Circle (15 pessoas), 3 plays compostos (Personal MIT, GitHub Intel, Content Arbitrage), matemática do moat, quality signals, plano semanal.  
**Audience:** Dev mid-sênior cansado de listicles.  
**Hook pra #002:** "Como extrair conhecimento de codebase de 1M+ linhas em 1 hora."

---

## #002 — Codebase mining: 5 queries que cortam direto pro coração de uma arquitetura
**Thesis:** Você não precisa ler 1M linhas de Tokio pra entender Tokio. Precisa fazer as 5 perguntas certas.  
**Cobre:**
- As 5 queries canônicas (boundary, error, concurrency, state, perf)
- Demo ao vivo: Cerebro contra `tokio-rs/tokio`
- Output real (a resposta + arquivo + linha)
- Por que isso é melhor que ler `ARCHITECTURE.md`: arquivos lie, código não
- Como adaptar pra qualquer codebase (template de queries)

**Audience:** Quem quer fazer onboarding rápido em projeto novo.  
**Demo:** Captura de Cerebro respondendo "como Tokio implementa work-stealing scheduler?"  
**Hook pra #003:** "Aplicar o mesmo princípio em entrevista FAANG: como decompor um system design problem em 5 queries."

---

## #003 — Interview hacking: o banco FAANG que vale R$ 500k–1M
**Thesis:** Empresa não te entrevista pra saber se você é bom. Te entrevista pra confirmar que você fez a lição. O moat é ter a lição feita antes.  
**Cobre:**
- 50 queries de system design indexadas (Instagram feed, Uber matching, Tinder swipe, Netflix CDN)
- 30 queries de behavioral STAR (conflito, failure, deadline)
- Como gerar respostas usando Cerebro contra glassdoor + blind + system-design-primer
- Anti-pattern: decorar respostas. Pattern: indexar e re-derivar sob pressão
- Negociação: usando levels.fyi como fonte indexada (com caveats)

**Audience:** Quem está em ciclo de entrevista (ou planejando).  
**Demo:** "Design Uber" com Cerebro — resposta com referências a 4 system design books indexados.  
**Hook pra #004:** "Quais codebases especificamente indexar pra cada stack — guia do GitHub Intelligence."

---

## #004 — GitHub Intelligence: 30 codebases que valem mais que 30 cursos
**Thesis:** Cada stack tem 3 codebases canônicos. Indexa esses 3 e você passa 90% dos engenheiros que trabalham na stack.  
**Cobre:**
- 10 stacks (web infra, distributed, async, db, k8s, ml, security, frontend, devtools, embedded)
- Pra cada stack, os 3 repos canônicos + por que cada um
- Como indexar issues fechadas (debugging real) vs source (decisões)
- Workflow: clone, ingest, query, document
- Anti-pattern: indexar tudo. Pattern: indexar com objetivo.

**Audience:** Quem quer profundidade técnica em uma stack específica.  
**Tabela:** stack × repo × o que aprender × queries-chave.  
**Hook pra #005:** "Você indexou. Agora extrai retorno: como transformar 100 queries em 100 posts no LinkedIn."

---

## #005 — Content arbitrage: a fábrica de LinkedIn de 1 post/dia
**Thesis:** LinkedIn é o canal mais sub-precificado do planeta pra dev. Você está pagando 0.04% do CPM equivalente em ads. Por que mais gente não faz isso? Porque dá trabalho — e é por isso que funciona.  
**Cobre:**
- Pipeline: query → rascunho LLM → edit humano (15min) → post
- Templates: hot take, personal story, numbered, question, carousel
- Cadência: 1×/dia útil por 90 dias (não negocia)
- Métricas reais: o que medir (saved > liked), o que ignorar (vanity)
- Anti-pattern: ghost-writing total. Pattern: opinião sua, evidência indexada.

**Audience:** Quem tem o conhecimento mas zero distribuição.  
**Demo:** 5 variações do post #001 pra LinkedIn (já produzido — link).  
**Hook pra #006:** "Visibilidade só vale se você sabe negociar quando o inbound chegar — próxima edição é sobre isso."

---

## #006 — Salary negotiation: quando o inbound chega
**Thesis:** 80% dos devs perdem R$ 50–200k/ano por não saber negociar. A diferença não é técnica de negociação, é **dado**. Quem tem dado, dita.  
**Cobre:**
- Fontes: levels.fyi (público), Blind (verified), Rora (negotiation), HN comments antigas (ground truth)
- Como indexar e correlacionar (mesma role × empresa × ano × localização)
- O número errado: "qual sua expectativa". O número certo: "quanto vocês pagam pra esse nível"
- Counter-offer math: equity vesting, sign-on, refresh
- Anti-pattern: aceitar o primeiro número. Pattern: silêncio + dados.
- Caso real (anonimizado): R$ 320k → R$ 510k em 1 conversa.

**Audience:** Quem está pra fechar oferta nas próximas 4 semanas.  
**Demo:** Snippet de query Cerebro contra base levels.fyi indexada.  
**Hook pra #007:** "Você sabe negociar. Mas e se a sua **role** fosse tão única que negociação fosse pro forma?"

---

## #007 — Niche moat: a interseção de 3 techs que ninguém mais domina
**Thesis:** Generalista compete com 100k pessoas. Especialista em 1 tech compete com 5k. Especialista na **interseção** de 3 techs compete com 50. Você vira a busca padrão pra aquela combinação.  
**Cobre:**
- Como escolher: Venn diagram (tech madura × tech emergente × tech vertical)
- Exemplos concretos: NixOS+Rust+SEC (eu), Postgres+ML+streaming, K8s+eBPF+observability
- Como construir: 6 meses de Personal MIT em cada uma + interseção em 3
- Como sinalizar: domínio em GitHub, posts na interseção, talk em conf de nicho
- Por que isso fura ATS: keyword stuffing fura algoritmo, não fura humano. Domínio fura ambos.

**Audience:** Quem quer parar de ser commodity.  
**Caso real:** Trajetória de quem era "DevOps" e virou "NixOS Security Architect".  
**Hook pra #008:** "Pra dominar a interseção, papers > tutoriais. Próxima: os 10 papers que pagam 5 anos de experiência."

---

## #008 — Top 10 papers que pagam 5 anos de experiência
**Thesis:** Papers parecem acadêmicos. Não são. Cada paper canônico é uma destilação de 5 anos de tentativas malsucedidas em algum lab. Você lê em 2h o que custou anos pra alguém aprender.  
**Cobre:**
- 10 papers escolhidos: Lamport (1978), GFS (2003), MapReduce (2004), Dynamo (2007), Spanner (2012), Raft (2014), Time-Clocks (revisitado), TAO (2013), Hellerstein DB (2007), Lampson Hints (1983)
- Como ler paper (não é livro): ler abstract → conclusion → tabelas → experimento → introdução → meio
- Como indexar paper no Cerebro pra consulta cross-reference
- Pra cada paper: 1 insight que muda como você projeta sistemas hoje
- Anti-pattern: ler paper porque "deveria". Pattern: ler porque está projetando algo similar.

**Audience:** Quem está num ponto de carreira onde "boas práticas" não basta mais.  
**Demo:** Query Cerebro: "como Spanner resolve clock skew?" → resposta cita papers e código aberto inspirado.  
**Hook pra #009:** "Você consumiu, indexou, dominou. Hora de monetizar — newsletter e produto."

---

## #009 — Como uma newsletter de 10k subs vira R$ 50k/mês
**Thesis:** Newsletter técnica é o melhor business model pra dev individual em 2026. Margem alta, audience qualificada, escala assíncrona, ativo composto.  
**Cobre:**
- Math: 10k subs × 2% conversion × R$ 30/mês × 12 meses = R$ 72k/ano (free tier)
- Pirâmide: free (blog) → paid newsletter (R$ 30) → course (R$ 800) → consulting (R$ 30k/projeto)
- Stack mínimo: Substack/Buttondown + Cerebro (geração) + Stripe (paid)
- O que NÃO fazer: começar com paywall, prometer cadência impossível, escrever "sobre tech genericamente"
- O que faz: nicho claro, cadência sustentável, ativo no GitHub público
- Caso real: cresci de 0 → X em Y meses (com números reais quando publicar)

**Audience:** Quem quer renda paralela ou caminho pra empreender.  
**Demo:** Pipeline: query Cerebro → rascunho → newsletter → e-mail.  
**Hook pra #010:** "Tudo o que você leu nas 9 edições anteriores é parte de um sistema. Edição final mostra o sistema completo, end-to-end."

---

## #010 — Capstone: o sistema completo, end-to-end
**Thesis:** Cada edição foi uma peça. Esta edição costura tudo num pipeline operacional que roda no seu hardware, em loop contínuo, gerando knowledge + content + revenue sem você abrir o terminal.  
**Cobre:**
- Arquitetura: Cerebro (knowledge) + spider-nix (intel discovery) + LLM local + cron + outputs
- Daily loop: 06h ingest novos posts/papers → 08h gera digest → 10h posta no LinkedIn → 18h coleta métricas → 22h re-prioriza queue
- Weekly loop: domingo gera newsletter → segunda envia
- Monthly loop: review de moat (que indexei? que postei? que monetizei?)
- Stack open source: tudo em Nix flake, reproduzível, no GitHub
- Anti-pattern: tentar fazer tudo manual. Pattern: automatizar geração + manter curadoria humana no loop crítico (edit final, decisão de posting).
- Hand-off: o pipeline está aberto. Fork e adapta. Issue no repo se travar.

**Audience:** Quem leu até aqui e quer rodar o sistema.  
**Demo:** Vídeo de 5min mostrando o pipeline rodando uma quarta-feira inteira.  
**CTA final:** Roda. Não compartilha. Não posta sobre. **Roda.**

---

## Princípios da série

1. **Cada edição é executável.** Plano de ação no fim, não inspiração.
2. **Toda alegação tem evidência.** Número, query, link, snippet.
3. **Anti-pattern + pattern.** Pra cada técnica, o jeito errado e o certo.
4. **Compõe.** #002 assume que leitor fez #001. #003 assume #002. Não se repete.
5. **6 meses de cadência.** Quinzenal. 10 edições em 5 meses. 10ª = capstone.
6. **Tudo gerado pelo próprio sistema.** A newsletter é a demo do produto.

---

## Cadência sugerida

| Edição | Data alvo | Status |
|---|---|---|
| #001 | 2026-05-03 | ✅ Publicado |
| #002 | 2026-05-17 | 🟡 Rascunho |
| #003 | 2026-05-31 | ⬜ |
| #004 | 2026-06-14 | ⬜ |
| #005 | 2026-06-28 | ⬜ |
| #006 | 2026-07-12 | ⬜ |
| #007 | 2026-07-26 | ⬜ |
| #008 | 2026-08-09 | ⬜ |
| #009 | 2026-08-23 | ⬜ |
| #010 | 2026-09-06 | ⬜ |

Quinzenal. Quartas-feiras. 06h BRT.

---

*Esse arco existe pra manter coerência. Nenhuma edição é solta — cada uma adiciona uma peça ao moat. Se em algum momento o leitor decidir parar, está tudo bem: ele já tem o suficiente pra começar. Mas quem ler as 10 sai com **sistema operacional completo de knowledge management** rodando.*
