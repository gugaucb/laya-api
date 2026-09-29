# Gitea vs GitHub: o que existe, o que não existe, e onde a paridade é só parcial

Objetivo deste arquivo: evitar que Claude tente usar/documentar/prometer uma funcionalidade do GitHub como se ela existisse em Gitea (ou vice-versa) e evitar tentativas de acesso a endpoints, CLIs ou sintaxes que simplesmente não existem no Gitea.

Legenda: ✅ existe e é equivalente | 🟡 existe mas com limitações relevantes | ❌ não existe

## Plataforma / API

| Recurso GitHub | Status em Gitea | Observação |
|---|---|---|
| REST API v3-style | ✅ | API própria do Gitea, "inspirada" na do GitHub, não idêntica campo a campo. |
| GraphQL API | ❌ | Gitea só expõe REST. Não peça/gera queries GraphQL para Gitea. |
| Webhooks | ✅ | Suporta Slack, Discord, Mattermost, Feishu/Lark, Telegram, Matrix, webhook genérico, etc. |
| OAuth2 provider (SSO) | ✅ | Gitea pode atuar como provedor OAuth2 para outras apps. |
| GitHub Apps (apps instaláveis com permissões granulares) | ❌ | Não existe o conceito de "GitHub App" instalável com permissões por recurso. O que existe são tokens de usuário/organização e OAuth2 apps clássicos. |
| Fine-grained personal access tokens com escopos por recurso | 🟡 | Gitea tem escopos de token, mas o modelo é mais simples que o do GitHub (não há granularidade por repositório individual do mesmo jeito). |
| Rate limiting documentado publicamente | 🟡 | Depende de configuração do administrador da instância; não há um limite universal "5000 req/hora" como no GitHub.com — pergunte ao admin da instância se necessário. |

## CLI

| GitHub | Gitea | Observação |
|---|---|---|
| `gh` (CLI oficial) | `tea` (CLI oficial) | Sintaxe totalmente diferente. `tea` não tem paridade de comandos com `gh` (ex.: sem `tea copilot`, sem `tea codespace`). |
| `gh actions` / `gh run` | Não existe em `tea` | Gerenciar Actions/runners via `tea` não é suportado; use a API REST diretamente. |
| `gh api` (chamada genérica à API) | Não existe equivalente direto em `tea` | Para chamadas ad-hoc use `curl`/`httpie` contra `/api/v1`. |

## Colaboração

| Recurso GitHub | Status em Gitea | Observação |
|---|---|---|
| Issues | ✅ | Praticamente equivalente: labels, milestones, assignees, reações, dependências entre issues, deadlines. |
| Pull Requests | ✅ | Equivalente, incluindo reviews, review requests, resolver comentários de review. |
| Discussions (fórum por repositório/org) | ❌ | Não existe. A recomendação da própria comunidade Gitea é usar Issues para esse fim. |
| Projects (kanban) | ✅ | Existe em nível de repositório e de organização desde a v1.20/1.21 (foi adicionado depois de muito debate — não confunda com o "Projects clássico" do GitHub, o modelo de dados é mais simples). |
| Wiki | ✅ | Baseado em um repositório git próprio para o wiki, como no GitHub. |
| Releases + assets | ✅ | Equivalente. |
| Code owners (`CODEOWNERS`) | 🟡 | Suportado, mas com cobertura de regras mais simples que a do GitHub em versões antigas — confira a versão da instância. |
| Sponsors / Funding | ❌ | Não existe um equivalente de GitHub Sponsors. `.github/FUNDING.yml` não tem efeito. |
| Star/Watch/Fork | ✅ | Equivalente. |
| Badges de usuário/organização | 🟡 | Existe um sistema de badges simples administrado por admins da instância, bem mais limitado que conquistas do GitHub. |

## CI/CD (Gitea Actions vs GitHub Actions)

| Recurso GitHub | Status em Gitea | Observação |
|---|---|---|
| Sintaxe de workflow YAML | ✅ | Reaproveita a sintaxe do GitHub Actions quase integralmente. |
| Runners hospedados pela plataforma | ❌ (fora do Gitea Cloud pago) | Em instância self-hosted, **todo** runner é `act_runner` que você mesmo hospeda e registra. Não existe "runner gerenciado" gratuito. |
| Marketplace de actions completo | 🟡 | Muitas actions de `owner/repo@ref` do GitHub funcionam via download de tarball/zip, mas não há garantia de 100%: actions que dependem de APIs internas do GitHub, de Docker de formas específicas, ou de recursos não replicados (ex.: alguns cenários de `actions/github-script`, actions "go actions" nativas) podem falhar. Composite actions que usam `uses: https://github.com/...` (URL absoluta) só funcionam com certos runners baseados em `act`. |
| Environments com aprovação manual (protection rules completas) | 🟡 | Suporte bem mais limitado que no GitHub; não assuma paridade de "required reviewers" antes de checar a versão. |
| OIDC nativo para nuvens (AWS/GCP/Azure) | ❌ / 🟡 | Sem equivalente pronto de "OIDC subject claims" do GitHub Actions; qualquer integração assim precisa ser montada manualmente. |
| Secrets e variables (repo/org/user) | ✅ | Existem nos três níveis, com API própria. |
| Artifacts | ✅ | Suportado, com API compatível o bastante para a maioria dos usos. |
| Cache de dependências (`actions/cache`) | 🟡 | Funciona de forma mais limitada — depende da versão do `act_runner` e requer infraestrutura extra em alguns setups. |
| Re-executar job/run, cancelar, disparar `workflow_dispatch` | ✅ | Todos existem na API de Actions do repositório/organização. |

## Segurança e automação de dependências

| Recurso GitHub | Status em Gitea | Observação |
|---|---|---|
| Dependabot (alerts + PRs automáticos) | ❌ | Não existe nativamente. Alternativa usada pela comunidade: configurar o **Renovate Bot** (self-hosted ou via Actions) apontando pro Gitea. |
| Code scanning (CodeQL) | ❌ na Community; 🟡 parcial em Enterprise | A oferta paga Gitea Enterprise adiciona alguns recursos de segurança, mas não é um substituto direto do CodeQL. |
| Secret scanning nativo | ❌ | Não existe scanner de segredos nativo na Community edition. |
| Dependency graph / SBOM | ❌ | Não existe endpoint equivalente. |

## Dev environments

| Recurso GitHub | Status em Gitea | Observação |
|---|---|---|
| Codespaces (ambiente de dev na nuvem) | ❌ | Não existe. Se o usuário quiser algo parecido, precisa de uma solução externa (ex.: Gitpod apontando pro Gitea via API aberta, mas sem integração oficial). |
| GitHub Pages | ❌ | Não há produto "Pages" dedicado. Para publicar site estático a partir de um repo, é preciso montar isso manualmente com Gitea Actions + um servidor de arquivos estáticos (ou usar Gitea Cloud, que oferece algo similar comercialmente). |
| Copilot / Copilot Chat | ❌ | Nenhuma integração nativa de assistente de código com IA. |

## Migração

| Recurso | Status em Gitea | Observação |
|---|---|---|
| Importar repositório do GitHub/GitLab/Gogs/Bitbucket | ✅ | `POST /repo/migrate` (ou pela UI) importa repositório, issues, PRs, labels, milestones, releases e wiki na mesma operação. |
| Importar Discussions do GitHub | ❌ | Como não há Discussions em Gitea, esse conteúdo não é migrado — o dado é perdido ou precisa ser convertido manualmente em issues. |

---

## Como usar esta tabela na prática

Quando o pedido do usuário mencionar uma funcionalidade específica do GitHub (ex.: "cria um Dependabot pra esse repo Gitea" ou "usa GraphQL pra buscar os PRs"), primeiro confira esta tabela:
- Se **❌**: explique que não existe, cite a alternativa da linha (quando houver), e não tente simular a funcionalidade com outra coisa disfarçada de "quase igual" sem deixar claro que é uma alternativa e não o recurso original.
- Se **🟡**: explique a limitação específica antes de prosseguir, para o usuário decidir se aceita a diferença.
- Se **✅**: prossiga normalmente, mas ainda assim confira `references/api-reference.md` para pegar o endpoint/campo certo, já que nomes e formatos de campo variam em relação ao GitHub mesmo quando o recurso existe.
