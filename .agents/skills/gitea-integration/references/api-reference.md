# Referência da API REST do Gitea (base: `docs.gitea.com/api/`, v1.27.x)

Todos os caminhos abaixo são relativos a `<base_url>/api/v1`. Esta é a lista consolidada das operações **realmente existentes** no Swagger oficial do Gitea, agrupadas por tag, com os endpoints mais úteis no dia a dia. Se precisar de um endpoint que não está aqui, confira o Swagger ao vivo da instância (`<base_url>/api/swagger`) antes de inventar um caminho — a numeração de versão pode ter adicionado ou removido algo.

Convenção: `{owner}`, `{repo}`, `{index}` (número da issue/PR), `{id}` são parâmetros de path.

## repository (a maior categoria — ~200 operações)

Repositórios, conteúdo, branches, tags, releases, pull requests, wiki, Actions do repositório, webhooks.

- CRUD de repositório: `GET/PATCH/DELETE /repos/{owner}/{repo}`, `POST /repos/{owner}/{repo}/generate` (a partir de template), `POST /repo/migrate`
- Busca: `GET /repos/search`
- Conteúdo de arquivos: `GET /repos/{owner}/{repo}/contents/{filepath}` (metadados+conteúdo), `PUT` (criar/atualizar, precisa de `sha` para atualizar), `DELETE`, `POST /repos/{owner}/{repo}/contents` (editar vários arquivos de uma vez)
- Branches: `GET/POST/DELETE /repos/{owner}/{repo}/branches`, proteção de branch em `/branch_protections`
- Tags: `GET/POST/DELETE /repos/{owner}/{repo}/tags`, proteção de tag em `/tag_protections`
- Commits: `GET /repos/{owner}/{repo}/commits`, diff/patch em `/git/commits/{sha}.diff|.patch`, status de commit em `/statuses/{sha}`
- Pull Requests: `GET/POST /repos/{owner}/{repo}/pulls`, `GET/PATCH /pulls/{index}`, merge em `POST /pulls/{index}/merge`, reviews em `/pulls/{index}/reviews`, arquivos alterados em `/pulls/{index}/files`
- Releases: `GET/POST /repos/{owner}/{repo}/releases`, anexos em `/releases/{id}/assets`
- Wiki: `GET/POST/PATCH/DELETE /repos/{owner}/{repo}/wiki/page`, `GET /wiki/pages`, `GET /wiki/revisions/{pageName}`
- Webhooks: `GET/POST /repos/{owner}/{repo}/hooks`, `POST /hooks/{id}/tests`
- **Actions do repositório**: workflows em `GET /repos/{owner}/{repo}/actions/workflows`, disparar (`workflow_dispatch`) em `POST /actions/workflows/{workflow_id}/dispatches`, runs em `GET /actions/runs`, jobs em `/actions/jobs`, artifacts em `/actions/artifacts`, secrets em `/actions/secrets`, variables em `/actions/variables`, runners (registro/registro token) em `/actions/runners`, re-executar job/run com `POST /actions/tasks/{task_id}/rerun` e variantes
- Mirrors: push mirrors em `/push_mirrors`, sync de mirror em `POST /mirror-sync`
- Colaboradores e permissões: `/collaborators`, `GET /repos/{owner}/{repo}/collaborators/{username}/permission`
- Transferência de repositório: `POST /transfer`, `POST /transfer/accept`, `POST /transfer/reject`

## issue (72 operações)

Cobre tanto issues quanto pull requests (PRs em Gitea são "issues" com dados extras).

- CRUD: `GET/POST /repos/{owner}/{repo}/issues`, `GET/PATCH/DELETE /issues/{index}`
- Comentários: `GET/POST /issues/{index}/comments`, `PATCH/DELETE /issues/comments/{id}`
- Labels: `GET/PUT/POST/DELETE /issues/{index}/labels`, CRUD de labels do repo em `/labels`
- Milestones: CRUD em `/repos/{owner}/{repo}/milestones`
- Assignees: `POST/DELETE /issues/{index}/assignees`
- Dependências entre issues (blocking): `GET/POST/DELETE /issues/{index}/blocks` e `/dependencies`
- Reações (emoji): `/issues/{index}/reactions`, `/issues/comments/{id}/reactions`
- Deadlines: `POST /issues/{index}/deadline`
- Stopwatch / tempo rastreado: `POST /issues/{index}/stopwatch/start|stop|delete`, `GET/POST /issues/{index}/times`
- Subscrição/watch de issue: `/issues/{index}/subscriptions`
- Pin de issue: `POST/DELETE /issues/{index}/pin`

## organization (67 operações)

- CRUD de organização: `GET/POST/PATCH/DELETE /orgs`
- Times: `GET/POST /orgs/{org}/teams`, membros e repos do time em `/teams/{id}/members` e `/teams/{id}/repos`
- Repos da org: `GET/POST /orgs/{org}/repos`
- Labels no nível de organização (label sets reutilizáveis): `/orgs/{org}/labels`
- Bloqueio de usuários pela org: `/orgs/{org}/blocks`
- **Actions no nível de organização**: runners, secrets, variables, workflow runs/jobs — mesmos conceitos do nível de repositório, prefixados por `/orgs/{org}/actions/...`
- Permissões de um usuário na org: `GET /orgs/{org}/members/{username}/permissions` (verifique o slug exato no Swagger da versão em uso)

## user (76 operações)

- Usuário autenticado: `GET /user`
- Tokens de acesso: `GET/POST/DELETE /users/{username}/tokens`
- Chaves SSH e GPG: `/user/keys`, `/user/gpg_keys`
- E-mails: `/user/emails`
- Seguidores/seguindo: `/user/followers`, `/user/following`
- Repos que o usuário possui/estrelou/observa: `/user/repos`, `/user/starred`, `/user/subscriptions`
- Aplicações OAuth2: `/user/applications/oauth2`
- **Actions no nível de usuário** (runners/secrets/variables pessoais): `/user/actions/...`
- Configurações do usuário: `GET/PATCH /user/settings`
- Bloqueio de outros usuários: `/user/blocks`

## admin (32 operações — requer conta admin da instância)

- Gestão de usuários: `POST/PATCH/DELETE /admin/users`, badges de usuário em `/admin/users/{username}/badges`
- Criar repositório em nome de outro usuário: `POST /admin/users/{username}/repos`
- Runners globais da instância: `/admin/actions/runners`, token de registro em `/admin/actions/runners/registration-token`
- Cron jobs da instância: `GET /admin/cron`, `POST /admin/cron/{task}`
- Webhooks do sistema (globais): `/admin/hooks`
- Buscar/listar organizações e emails de toda a instância: `/admin/orgs`, `/admin/emails`

## package (9 operações)

Listar, inspecionar, vincular a um repositório e apagar pacotes publicados (npm, Docker/OCI, Maven, PyPI, NuGet, Cargo, Composer, Conda, Helm, RubyGems, Vagrant, Debian, RPM, Alpine, Chef, CRAN, Pub, Swift, pypi — a lista de formatos suportados cresce por versão, confira `docs.gitea.com/usage/packages` para a lista atual):

- `GET /packages/{owner}` (lista), `GET /packages/{owner}/{type}/{name}` (uma versão específica), `GET /packages/{owner}/{type}/{name}/-/latest`
- `DELETE /packages/{owner}/{type}/{name}/{version}`
- Vincular/desvincular a um repositório: `POST /packages/{owner}/{type}/{name}/{version}/link/{repo_name}` e `/unlink`
- **Nota**: publicar pacotes normalmente é feito com as ferramentas nativas de cada ecossistema (`npm publish`, `docker push`, `twine upload`, etc.) apontando para o registry do Gitea, não por essa API de gestão — a API aqui é para listar/inspecionar/apagar depois de publicado.

## notification (7 operações)

- Listar notificações do usuário autenticado: `GET /notifications` (aceita filtro `?since=`, `?only_unread=`)
- Marcar como lidas: `PUT /notifications`
- Por repositório: `GET/PUT /repos/{owner}/{repo}/notifications`
- Checar se há notificações não lidas: `GET /notifications/new`

## miscellaneous (14 operações)

- Versão da instância: `GET /version`
- Templates de `.gitignore`, labels e licenças: `/gitignore/templates`, `/label/templates`, `/licenses`
- Renderizar Markdown/markup para HTML: `POST /markdown`, `/markdown/raw`, `/markup`
- Chave de assinatura padrão da instância (GPG/SSH): `/signing-key.gpg`, `/signing-key.ssh`
- Token atual: `GET/DELETE /user/applications/oauth2` (revisar no Swagger — token corrente também pode ser consultado via `/user`)

## settings (4 operações)

Configurações globais expostas a clientes (somente leitura): `GET /settings/api`, `/settings/attachment`, `/settings/repository`, `/settings/ui`. Úteis para descobrir limites da instância (tamanho máx. de upload, etc.) antes de tentar uma operação que pode ser rejeitada por configuração do admin.

---

### Coisas que existem no GitHub REST e **não têm equivalente direto** aqui

- Não há endpoint de "Discussions" (nem de time discussions).
- Não há endpoint de Dependabot/code scanning/secret scanning alerts.
- Não há endpoint de Codespaces.
- Não há "Copilot billing/seats" (óbvio, mas é comum pedirem por engano ao migrar scripts).
- Sudo (`SudoParam`/`SudoHeader`) é um recurso *a mais* que o Gitea tem e o GitHub REST clássico não tem da mesma forma — não é limitação, é diferença de modelo.

Quando estiver portando um script feito para a API do GitHub, o exercício é: para cada chamada, procurar a categoria equivalente aqui (`issue`, `repository`, `organization`, `user`) — a maioria dos endpoints de CRUD básico tem um par direto, mas o corpo do JSON de request/response frequentemente tem campos a mais, a menos, ou com nomes diferentes. Sempre confira o schema real via Swagger antes de assumir paridade de campos.
