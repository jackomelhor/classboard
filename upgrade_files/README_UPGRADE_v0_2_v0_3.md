# ClassBoard v0.2 + v0.3

Este pacote sobe a base da v0.1 para uma versão mais completa, sem pagamento.

## O que entrou
- editar tarefa
- excluir tarefa
- detalhe da tarefa
- checklist por tarefa
- lista de tarefas com filtros
- membros do workspace
- entrar com código de convite
- regenerar código de convite
- gestão básica de papéis
- agenda dos próximos 30 dias
- dashboard mais completo

## Arquivos modificados
- board/models.py
- board/forms.py
- board/views.py
- board/urls.py
- board/admin.py
- classboard/settings.py
- templates/base.html
- templates/board/home.html
- templates/board/create_workspace.html
- templates/board/register.html
- templates/board/join_workspace.html
- templates/board/task_form.html
- templates/board/task_list.html
- templates/board/task_detail.html
- templates/board/task_confirm_delete.html
- templates/board/members.html
- templates/board/agenda.html
- templates/board/dashboard.html
- templates/registration/login.html
- static/css/style.css
- static/js/app.js
- board/migrations/0001_initial.py (apenas no projeto completo; para upgrade da sua v0.1 prefira rodar makemigrations localmente)

## Como implantar sobre a v0.1
1. Faça backup da pasta antiga.
2. Substitua os arquivos acima pelos novos.
3. Rode:

```bash
python manage.py makemigrations board
python manage.py migrate
```

4. Inicie o servidor:

```bash
python manage.py runserver
```

## O que você pode alterar com segurança
### Cores
Arquivo: `static/css/style.css`
Troque as variáveis em `:root`.

### Regras de permissão
Arquivo: `board/views.py`
Funções:
- `is_workspace_manager`
- `is_workspace_owner`
- `can_edit_task`

### Tipos e escolhas
Arquivo: `board/models.py`
Você pode ajustar:
- `WORKSPACE_TYPES`
- `TASK_TYPES`
- `PRIORITY_CHOICES`
- `STATUS_CHOICES`

### Código de convite
Arquivo: `board/models.py`
Função: `generate_invite_code`
Se quiser código maior, troque `token_hex(3)` por `token_hex(4)`.

## Observação importante
A tela de membros usa gestão de papel apenas para owner/admin/member. Não existe ainda transferência de ownership. Isso é uma boa próxima melhoria, mas não era prioridade agora.

### ALLOWED_HOSTS
Arquivo: `classboard/settings.py`
Já deixei `127.0.0.1`, `localhost` e `testserver`.
Se publicar, acrescente o domínio real do seu site.
