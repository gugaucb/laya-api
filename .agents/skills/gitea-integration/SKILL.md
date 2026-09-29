---
name: gitea-integration
description: Use this skill whenever the user wants to interact with a Gitea instance (self-hosted Git service) via its REST API, the official "tea" CLI, webhooks, or Gitea Actions — creating/listing/editing repos, issues, pull requests, releases, organizations, packages, runners, etc. Always consult this skill before writing any Gitea API call or CLI command, and especially before assuming a GitHub feature (GraphQL API, Discussions, Copilot, Codespaces, Dependabot, code scanning, hosted Actions runners, etc.) exists on Gitea — it frequently does not, or works differently, and this skill documents exactly what is and isn't supported so Claude doesn't attempt or promise nonexistent functionality. Trigger this for phrases like "gitea", "minha instância gitea", "self-hosted git", "migrar do github pro gitea", "gitea actions", "tea cli", or any task that names a Gitea URL/host.
---

# Integração com Gitea

Gitea (https://docs.gitea.com) é um serviço Git leve e auto-hospedado, escrito em Go, que reimplementa boa parte do fluxo de trabalho do GitHub (repositórios, issues, pull requests, releases, webhooks, Actions) mas **não é um clone 1:1 do GitHub**. Sua API é "inspirada" na API v3 do GitHub, não idêntica — vários endpoints, campos e funcionalidades simplesmente não existem, têm nomes diferentes, ou funcionam com limitações importantes.

**Regra de ouro: antes de gerar qualquer chamada de API, comando `tea`, ou workflow de Actions para Gitea, verifique nas referências abaixo se aquilo realmente existe em Gitea.** Não extrapole a partir do conhecimento sobre a API/CLI/Actions do GitHub — assuma que qualquer coisa não listada aqui precisa ser confirmada (busca na doc oficial ou no Swagger da instância) antes de prometer que funciona.

## Descobrir a instância antes de tudo

Gitea é auto-hospedado, então a primeira coisa a checar é **qual instância e qual versão**:
- Peça ou confirme a URL base (ex.: `https://git.empresa.com`).
- A versão da instância importa: recursos como Actions, `blocking issues`, badges de usuário, ou certos campos da API só existem a partir de certas versões (1.19+ para Actions, 1.21+ para Actions habilitado por padrão, etc.). Quando em dúvida, chame `GET /api/v1/version` (ver referência de Miscellaneous) ou olhe o Swagger publicado em `<base_url>/api/swagger`.
- Instâncias podem ter Actions, Packages, ou registro de novos usuários desabilitados pelo administrador — um 404/403 nem sempre significa "recurso não existe no Gitea", pode significar "desabilitado nesta instância".

## Autenticação

- Header recomendado (versões atuais): `Authorization: token <TOKEN>` — **não** use os parâmetros de query `token=` ou `access_token=`, ambos deprecated desde 1.23 e alvo de remoção.
- Alternativa: Basic Auth (usuário/senha ou usuário/token). Se 2FA estiver ativo, é preciso também o header `X-GITEA-OTP`.
- `Sudo` (header `Sudo: <username>` ou query `sudo=`) permite que um admin execute a chamada "como" outro usuário — requer privilégios de admin.
- Tokens são criados em `Configurações > Aplicativos` na UI, ou via `POST /api/v1/users/{username}/tokens` (rota de admin) ou `tea login add`.

## Chamando a API REST

Toda a API vive sob `<base_url>/api/v1/...` e é só REST — **não existe API GraphQL em Gitea** (diferente do GitHub, que tem tanto REST quanto GraphQL). Se alguém pedir uma query GraphQL para Gitea, explique que não existe e ofereça o endpoint REST equivalente.

Padrão básico:

```bash
curl -H "Authorization: token $GITEA_TOKEN" \
  "https://git.example.com/api/v1/repos/{owner}/{repo}/issues"
```

Criar um recurso (POST) sempre com `Content-Type: application/json`:

```bash
curl -X POST -H "Authorization: token $GITEA_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"title":"Bug no login","body":"Descrição..."}' \
  "https://git.example.com/api/v1/repos/{owner}/{repo}/issues"
```

Paginação: a maioria dos endpoints de listagem aceita `?page=` e `?limit=`, e retorna os headers `X-Total-Count`, `Link`. Não existe cursor/offset estilo GraphQL — é paginação por página, como no GitHub REST clássico.

**Antes de montar uma chamada, confira `references/api-reference.md`**, que lista as categorias de operações da API (admin, issue, organization, package, repository, settings, user, notification, miscellaneous) com os endpoints mais usados de cada uma e exemplos. Ele reflete o Swagger oficial (`docs.gitea.com/api/`) — se o endpoint que você precisa não aparecer lá nem no Swagger da instância, não invente o caminho: diga ao usuário que não encontrou e ofereça alternativas (webhook, script local, etc.).

## CLI oficial: `tea`

Gitea tem uma CLI oficial chamada `tea` (repositório `gitea.com/gitea/tea`), **diferente do `gh` do GitHub** — não confunda os dois nem tente usar sintaxe do `gh` em `tea`. Comandos principais:

```
tea login add --url https://git.example.com --token $GITEA_TOKEN   # configura instância
tea issues [list|create|close]                # gerenciar issues
tea pulls [list|create|checkout]              # gerenciar e fazer checkout de PRs
tea labels                                    # gerenciar labels
tea milestones                                # gerenciar milestones
tea releases                                  # gerenciar releases
tea times                                     # tempo rastreado em issues/PRs
tea organizations                             # organizações
tea repos                                     # detalhes de repositório
tea open <recurso>                            # abre a UI web para o recurso
```

`tea` não cobre 100% da API (por exemplo, não gerencia Actions/runners nem packages) — para essas áreas, use a API REST diretamente. Se o usuário pedir algo em `tea` que não está na lista acima, confirme antes de inventar uma subcomando.

## Gitea Actions (CI/CD)

Gitea Actions reusa a sintaxe de workflow do GitHub Actions (YAML em `.gitea/workflows/` ou `.github/workflows/`), mas roda sobre um executor próprio, o `act_runner`, **não** sobre a infraestrutura do GitHub. Isso implica limitações importantes — leia `references/github-comparison.md#actions` antes de prometer paridade total. Resumo rápido:

- **Não existem "GitHub-hosted runners"**: todo runner precisa ser registrado e hospedado pelo próprio usuário/organização (`act_runner`, um binário separado). Não há como pedir "me dê um runner gerenciado pelo Gitea" — isso não existe fora do plano Gitea Cloud.
- **Actions não vêm habilitadas por padrão em instâncias antigas** (antes da 1.21) e podem estar desabilitadas pelo admin da instância.
- **Compatibilidade parcial com o Marketplace do GitHub**: muitas actions de `uses: owner/repo@version` funcionam, mas nem todas — em especial, ações Docker que dependem de recursos específicos do GitHub, ou ações que chamam a API do GitHub diretamente (ex.: `actions/github-script` tem suporte limitado), podem falhar. Ações que usam a sintaxe `uses: https://github.com/...` (URL absoluta) só funcionam em runners baseados em `act`, não em todos.
- **Sem GitHub Apps / OIDC nativo do GitHub**: fluxos de autenticação que dependem do OIDC do GitHub para nuvens (AWS/GCP/Azure) não têm equivalente pronto.
- A API de Actions em Gitea (runners, secrets, variables, workflow runs/jobs, artifacts) existe e é rica — está documentada na categoria `repository`/`organization`/`admin`/`user` em `references/api-reference.md`. Use-a normalmente, só não assuma paridade de comportamento com a nuvem do GitHub.

## O que o Gitea NÃO tem (não tente usar)

Antes de sugerir qualquer funcionalidade "porque no GitHub tem", confira esta lista rápida (detalhes e alternativas em `references/github-comparison.md`):

- **API GraphQL** — só REST.
- **GitHub Discussions** (fórum por repositório) — não existe; o padrão é usar Issues.
- **GitHub Copilot / Copilot Chat** — não existe integração nativa.
- **Codespaces** (ambiente de dev na nuvem) — não existe.
- **Dependabot** — não existe; a alternativa da comunidade é configurar o Renovate Bot.
- **Code scanning / secret scanning nativos (CodeQL etc.)** — não existem na edição Community; recursos de segurança mais avançados aparecem apenas na oferta Enterprise da Gitea, e mesmo assim não são idênticos aos do GitHub.
- **GitHub Sponsors** — não existe.
- **GitHub Pages** como produto dedicado — não existe um "Pages" nativo; publicação de site estático precisa ser montada via Actions + servidor próprio.
- **Runners hospedados na nuvem** (fora do Gitea Cloud pago) — sempre self-hosted via `act_runner`.
- **Environments com regras de proteção avançadas** (approval gates completos) — suporte é bem mais limitado que no GitHub.

Isso não é uma lista exaustiva — quando o usuário pedir algo e você não tiver certeza se existe, prefira checar `references/github-comparison.md`, buscar em docs.gitea.com, ou dizer explicitamente "não tenho certeza, vou confirmar" em vez de assumir que existe.

## O que o Gitea TEM e costuma ser subestimado

Para não pecar pro lado oposto (assumir que Gitea só faz o básico): ele tem Projects (kanban, em nível de repositório e de organização), wikis, pacotes (npm, Docker/OCI, Maven, PyPI, NuGet, Cargo, Composer, Conda, etc. — ver `references/api-reference.md#package`), proteção de branch e de tag, mirrors (push e pull), migração automática de repositórios do GitHub/GitLab/Gogs/Bitbucket com issues/PRs/releases/wiki, webhooks para Slack/Discord/Mattermost/genéricos, OAuth2 como provedor (SSO), 2FA, e uma API de Actions bem completa (runners, secrets, variables, artifacts, reruns de jobs/workflows).

## Fluxo recomendado ao atender um pedido

1. Identificar a instância, versão (se possível) e o tipo de credencial disponível.
2. Consultar `references/api-reference.md` para achar o endpoint/categoria certa, ou `references/github-comparison.md` se a dúvida for "isso existe em Gitea?".
3. Montar a chamada REST (ou comando `tea`) exata, com autenticação correta.
4. Se o recurso pedido estiver na lista de "não tem", explicar isso ao usuário e oferecer a alternativa mais próxima (webhook, Renovate, Issues em vez de Discussions, etc.) em vez de tentar simular a funcionalidade como se existisse.
