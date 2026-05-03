# 🧠 voidnxlabs intel #001
## Você não precisa de mais cursos. Precisa de um knowledge moat.

> A indústria de tutorial é teatro. Quem trabalha de verdade não consome conhecimento — **indexa**, compõe, transforma em ativo. Esta é a primeira edição. Sem fluff.

---

## A mentira do consumo

Você abriu o LinkedIn hoje. Viu o quê?

- "10 hábitos do dev sênior"
- "Aprendi Rust em 30 dias (thread)"
- "Por que toda startup deveria usar X"

Tudo isso é **content de quem fala sobre tech**. Quem **constrói** tech está em outro lugar — escrevendo postmortem de incidente, fazendo benchmark com flame graph, brigando em RFC.

A diferença entre os dois grupos não é talento. É **knowledge moat**: um network privado de fontes de alto sinal que cada um cultivou ao longo de anos. Você não compra, não copia em uma tarde. Mas pode começar hoje.

Esse é o ponto desta newsletter. Cada edição te dá:
1. Quem seguir (gente que constrói, não influencer)
2. Como extrair valor (queries, indexação, plays concretos)
3. Como compor o moat ao longo do tempo

Sem motivacional. Sem "10 dicas". Apenas o que funciona.

---

## O Inner Circle

15 pessoas. Se você seguir essas 15 e ler o que elas escrevem por 6 meses, vai estar acima de 95% dos devs. Sério.

### Systems & Performance
- **Brendan Gregg** — `brendangregg.com` — Inventou flame graphs. Trabalha na Intel. Tudo o que você precisa saber sobre performance em produção.
- **Dan Luu** — `danluu.com` — Ex-Google/MSFT. Escreve sobre o que importa: latência, custo, falha real. Sem hype.
- **Marc Brooker** — `brooker.co.za/blog` — VP da AWS. Arquiteto do Lambda. Posts curtos, densos, sobre decisões reais de distributed systems.

### Rust & Systems
- **Jon Gjengset (jonhoo)** — Crust of Rust no YouTube. Mostra código, não slides.
- **Amos (fasterthanlime)** — `fasterthanli.me` — Deep dives insanos. Quando você quer entender de verdade.

### Distributed Systems
- **Martin Kleppmann** — `martin.kleppmann.com` — DDIA é o livro. Os papers dele também.
- **Kyle Kingsbury (Aphyr)** — `aphyr.com` — Jepsen series. Quebra databases ao vivo. Mostra que MongoDB mente, Postgres mente, todo mundo mente sob certas condições.

### Databases
- **Alex Petrov** — Autor de "Database Internals". Storage engines até o nível do disco.

### Cloud & Infra
- **Charity Majors** — `charity.wtf` — Honeycomb. Observability é sobre perguntas que você ainda não fez.
- **Kelsey Hightower** — Kubernetes OG. Twitter dele é curso grátis.
- **Jessie Frazelle** — `blog.jessfraz.com` — Containers, security, kernel.

### Curators (essas pessoas filtram pra você)
- **Simon Willison** — `simonwillison.net` — AI, SQLite, web. Curates insanamente bem.
- **Julia Evans (b0rk)** — `jvns.ca` — Faz o complexo virar simples. Honesta.
- **Hillel Wayne** — `hillelwayne.com` — Formal methods, testing, perspectivas únicas.
- **Gergely Orosz** — `Pragmatic Engineer` newsletter — Inside info de Big Tech. Único que assino pago.

**Como usar:** RSS feed (Feedly, Inoreader). Não Twitter. Twitter é noise. Blog é signal.

---

## Os 3 plays que compõem

Conhecimento composto não é magia. É math: você indexa uma vez, consulta N vezes, gera produto N×K vezes.

### Play 1 — Personal MIT (custo: R$20–100)

Pega UMA tech que você quer dominar. Indexa toda a documentação oficial + 5 livros canônicos + 10 codebases de produção. Gera 200 queries progressivas via RAG. Em duas semanas você tem um curso customizado pro **seu** ponto de partida — não o de iniciante genérico.

**Por que funciona:** cursos são lineares e generalistas. Seu RAG é não-linear e personalizado. Você pula o que já sabe, aprofunda no que precisa, e cada resposta cita fontes — então tem caminho pra ir mais fundo quando quiser.

**Stack que recomendo:** Cerebro (este projeto) + qualquer LLM via Discovery Engine. R$20–100 em queries dá curso premium completo.

### Play 2 — GitHub Intelligence (custo: R$50–200)

Cursos te ensinam *padrões*. Códigos de produção te ensinam *trade-offs*. Indexa 10 repos estratégicos da sua área:

- Web infra → `vercel/next.js`, `vercel/turbo`
- Distributed → `cockroachdb/cockroach`, `etcd-io/etcd`
- Async/Rust → `tokio-rs/tokio`
- DB internals → `dgraph-io/badger`, `timescale/timescaledb`

Faz query do tipo *"como `cockroach` resolve consenso sob particionamento?"*. A resposta vem com referência a arquivo + linha + commit. Você está fazendo **reverse engineering de decisões arquiteturais de empresas bilionárias** por R$0.04 por query.

Isso não tem em curso. Não tem em livro. Está só no código.

### Play 3 — Content Arbitrage (custo: R$20–50, retorno: incalculável)

Cada 100 queries que você processa → 1 post público (LinkedIn, blog, Twitter).

Conta:
- 100 queries ≈ R$2 de custo
- 1 post ≈ 1k–10k impressões
- CPM equivalente: R$0.0002–0.002
- Google Ads cobra R$0.50–5.00 por 1k impressões — **2.500x mais caro**

Você está pagando **0.04% do que uma empresa pagaria** pelas mesmas impressões. E como você está postando deep-dives (não memes), o público é técnico. Recrutadores leem. Engenheiros sêniores leem. CTOs leem.

Em 3 meses postando 1×/dia: **inbound de recrutador todo dia útil**. Nenhuma daquelas vagas você teria visto ativamente procurando.

---

## A matemática do moat

Por que isso funciona em escala:

| Mecanismo | Você sozinho | Você com knowledge moat |
|---|---|---|
| Aprendizado | Linear (tutoriais) | Não-linear (RAG queries) |
| Consulta | Stack Overflow | Sua KB privada com fontes |
| Conteúdo | Zero a uma vez por mês | 1 post/dia, automatizado |
| Network | Quem te conhece | Quem **te procura** |
| Salário | Mercado aberto | Você dita |

Os números do retorno (conservador):

```
Investimento:   R$  10.000  (créditos GCP, 6 meses)
Output:
  - Personal MIT em 2 techs        R$  10.000 equivalente em curso
  - 100 posts técnicos publicados  R$ 100.000 equivalente em ads
  - 1 niche moat (NixOS+Rust+SEC)  Inestimável (1 oferta = R$ 500k+)
  - Newsletter (10k subs em 12m)   R$  10–50k/mês recorrente

ROI conservador:                   50–100x
ROI realista:                      Faz dump no salary stack
```

**O detalhe que ninguém fala:** 90% das pessoas que tentam isso **param na semana 2**. Por isso compõe. A barreira é disciplina, não inteligência.

---

## Quality signals (como saber que uma fonte vale)

Antes de adicionar alguém ao seu inner circle, checa:

✅ **Skin in the game** — constrói algo, não só fala  
✅ **Mostra trade-offs** — não escreve "X é melhor", escreve "X é melhor *quando*"  
✅ **Cita números** — não "muito rápido", "1.2ms p99 com 50k QPS em 4 cores"  
✅ **Explica falha** — postmortem honesto, não case study de marketing  
✅ **Código que roda** — exemplo executável, não pseudocódigo

❌ **Cuidado com:** tutorial mills, "top 10 X", clickbait title, autor anônimo, listicle de "tools you should know"

A regra simples: **se a pessoa nunca foi paged às 3am por causa do que escreve sobre, ignora.**

---

## Plano da semana (executa)

Não pra você ler — pra você **fazer**. 

**Hoje (2h):**
- [ ] Cria conta no Feedly. Adiciona os 15 RSS feeds do Inner Circle acima.
- [ ] Instala Cerebro local: `nix develop && cerebro setup`
- [ ] Indexa o livro/PDF mais denso que você tem na estante.

**Esta semana (4h, espalhadas):**
- [ ] Ler 3 posts dos 15. Anota uma decisão técnica que aprendeu de cada.
- [ ] Roda 50 queries no Cerebro sobre a tech que você quer dominar este trimestre.
- [ ] Escolhe 1 query cuja resposta foi excelente. Transforma em rascunho de post.

**Este mês:**
- [ ] Posta 4× no LinkedIn (1×/semana). Cada post nasce de uma query.
- [ ] Indexa 3 codebases de produção da sua área.
- [ ] Estabelece um nicho: a *interseção* de 3 techs que pouca gente domina junto. Esse vai ser seu moat.

---

## Próxima edição

**#002 — Como extrair conhecimento de codebase de 1M+ linhas em 1 hora.** Vou abrir o Cerebro contra os repos canônicos do Tier 1 e mostrar 5 perguntas que cortam direto pro coração da arquitetura. Inclui as queries exatas.

---

**Você acabou de ler ~1.500 palavras sobre como parar de consumir e começar a indexar.**  
**Se gostou, a única ação certa é executar o plano da semana acima.**  
**Salvar pra depois é teatro.**

— *voidnxlabs*

---

*Esta newsletter é gerada com Cerebro (RAG hermético, Nix-native) + spider-nix (intel discovery + content automation). Toda edição é o output de um sistema, não um post à mão. O knowledge moat é literal — está rodando no meu servidor. Você pode ter um.*
