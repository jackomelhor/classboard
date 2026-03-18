from __future__ import annotations

from collections import defaultdict
from datetime import date, timedelta

from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from .forms import (
    ChecklistItemForm,
    JoinWorkspaceForm,
    MemberRoleForm,
    RegisterForm,
    TaskForm,
    WorkspaceForm,
)
from .models import ChecklistItem, Membership, Task, Workspace


# ===== Helpers de permissão =====
# Aqui ficam as regras centrais do sistema.
# Se depois você quiser permitir que todo membro edite tarefas, altere a função can_edit_task.
def get_user_workspaces(user):
    memberships = Membership.objects.select_related('workspace').filter(user=user)
    return [membership.workspace for membership in memberships]


def get_selected_workspace(request: HttpRequest, user, fallback_first=True):
    workspaces = get_user_workspaces(user)
    selected_workspace = None
    workspace_id = request.GET.get('workspace') or request.POST.get('workspace_id')

    if workspace_id:
        selected_workspace = get_object_or_404(Workspace, id=workspace_id, memberships__user=user)
    elif workspaces and fallback_first:
        selected_workspace = workspaces[0]

    return workspaces, selected_workspace


def get_membership(user, workspace: Workspace):
    return Membership.objects.filter(user=user, workspace=workspace).first()


def is_workspace_manager(user, workspace: Workspace) -> bool:
    membership = get_membership(user, workspace)
    return bool(membership and membership.role in ['owner', 'admin'])


def is_workspace_owner(user, workspace: Workspace) -> bool:
    membership = get_membership(user, workspace)
    return bool(membership and membership.role == 'owner')


def can_edit_task(user, task: Task) -> bool:
    membership = get_membership(user, task.workspace)
    if not membership:
        return False
    return membership.role in ['owner', 'admin'] or task.author_id == user.id


def home(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    return render(request, 'board/home.html')


def register_view(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Conta criada com sucesso.')
            return redirect('dashboard')
    else:
        form = RegisterForm()
    return render(request, 'board/register.html', {'form': form})


@login_required
def dashboard(request):
    workspaces, selected_workspace = get_selected_workspace(request, request.user)

    today = date.today()
    week_limit = today + timedelta(days=7)

    tasks_today = []
    upcoming_exams = []
    pending_tasks = []
    overdue_tasks = []
    recent_tasks = []
    summary = {
        'concluidas': 0,
        'pendentes': 0,
        'provas_semana': 0,
        'atrasadas': 0,
        'taxa_conclusao': 0,
        'membros': 0,
    }
    selected_membership = None

    if selected_workspace:
        selected_membership = get_membership(request.user, selected_workspace)
        tasks = Task.objects.filter(workspace=selected_workspace).select_related('author')
        tasks_today = tasks.filter(due_date=today).exclude(status='concluido')[:5]
        upcoming_exams = tasks.filter(
            task_type='prova',
            due_date__gte=today,
            due_date__lte=week_limit,
        ).exclude(status='concluido')[:5]
        pending_tasks = tasks.filter(
            Q(task_type='trabalho') | Q(task_type='atividade') | Q(task_type='apresentacao') | Q(task_type='estudo'),
            due_date__gte=today,
        ).exclude(status='concluido')[:5]
        overdue_tasks = tasks.filter(due_date__lt=today).exclude(status='concluido')[:5]
        recent_tasks = tasks.order_by('due_date', '-created_at')[:6]

        weekly_queryset = tasks.filter(due_date__gte=today, due_date__lte=week_limit)
        summary = weekly_queryset.aggregate(
            concluidas=Count('id', filter=Q(status='concluido')),
            pendentes=Count('id', filter=Q(status__in=['pendente', 'andamento'])),
            provas_semana=Count('id', filter=Q(task_type='prova')),
            atrasadas=Count('id', filter=Q(due_date__lt=today) & ~Q(status='concluido')),
        )
        total_week = weekly_queryset.count()
        summary['taxa_conclusao'] = int((summary['concluidas'] / total_week) * 100) if total_week else 0
        summary['membros'] = selected_workspace.memberships.count()

    context = {
        'selected_workspace': selected_workspace,
        'selected_membership': selected_membership,
        'workspaces': workspaces,
        'tasks_today': tasks_today,
        'upcoming_exams': upcoming_exams,
        'pending_tasks': pending_tasks,
        'overdue_tasks': overdue_tasks,
        'recent_tasks': recent_tasks,
        'summary': summary,
    }
    return render(request, 'board/dashboard.html', context)


@login_required
def create_workspace(request):
    if request.method == 'POST':
        form = WorkspaceForm(request.POST)
        if form.is_valid():
            workspace = form.save(owner=request.user)
            messages.success(request, f'Workspace criado com sucesso. Código de convite: {workspace.invite_code}')
            return redirect(f"{reverse('dashboard')}?workspace={workspace.id}")
    else:
        form = WorkspaceForm()
    return render(request, 'board/create_workspace.html', {'form': form})


@login_required
def join_workspace(request):
    if request.method == 'POST':
        form = JoinWorkspaceForm(request.POST)
        if form.is_valid():
            code = form.cleaned_data['invite_code']
            workspace = Workspace.objects.filter(invite_code=code).first()
            if not workspace:
                messages.error(request, 'Código de convite inválido.')
            else:
                membership, created = Membership.objects.get_or_create(
                    workspace=workspace,
                    user=request.user,
                    defaults={'role': 'member'},
                )
                if created:
                    messages.success(request, f'Você entrou em {workspace.name}.')
                else:
                    messages.info(request, 'Você já participa desse workspace.')
                return redirect(f"{reverse('dashboard')}?workspace={workspace.id}")
    else:
        form = JoinWorkspaceForm()
    return render(request, 'board/join_workspace.html', {'form': form})


@login_required
def regenerate_invite_code(request, workspace_id):
    workspace = get_object_or_404(Workspace, id=workspace_id, memberships__user=request.user)
    if not is_workspace_owner(request.user, workspace):
        messages.error(request, 'Apenas o owner pode gerar um novo código de convite.')
        return redirect(f"{reverse('workspace_members')}?workspace={workspace.id}")

    if request.method == 'POST':
        workspace.regenerate_invite_code()
        messages.success(request, 'Novo código de convite gerado com sucesso.')
    return redirect(f"{reverse('workspace_members')}?workspace={workspace.id}")


@login_required
def create_task(request):
    memberships = Membership.objects.select_related('workspace').filter(user=request.user)
    workspace_id = request.GET.get('workspace') or request.POST.get('workspace_id')
    selected_workspace = None

    if workspace_id:
        selected_workspace = get_object_or_404(Workspace, id=workspace_id, memberships__user=request.user)
    elif memberships.exists():
        selected_workspace = memberships.first().workspace

    if not selected_workspace:
        messages.warning(request, 'Crie ou entre em um workspace antes de cadastrar tarefas.')
        return redirect('create_workspace')

    if request.method == 'POST':
        form = TaskForm(request.POST)
        if form.is_valid():
            task = form.save(commit=False)
            task.workspace = selected_workspace
            task.author = request.user
            task.save()
            messages.success(request, 'Tarefa criada com sucesso.')
            return redirect(f"{reverse('task_detail', args=[task.id])}?workspace={selected_workspace.id}")
    else:
        form = TaskForm()

    return render(request, 'board/task_form.html', {
        'form': form,
        'selected_workspace': selected_workspace,
        'page_title': 'Nova tarefa',
        'submit_label': 'Salvar tarefa',
    })


@login_required
def task_list(request):
    workspaces, selected_workspace = get_selected_workspace(request, request.user)
    if not selected_workspace:
        messages.warning(request, 'Crie ou entre em um workspace antes de visualizar tarefas.')
        return redirect('create_workspace')

    tasks = Task.objects.filter(workspace=selected_workspace).select_related('author')

    q = request.GET.get('q', '').strip()
    status = request.GET.get('status', '')
    priority = request.GET.get('priority', '')
    task_type = request.GET.get('task_type', '')
    subject = request.GET.get('subject', '')
    only_overdue = request.GET.get('only_overdue', '')

    if q:
        tasks = tasks.filter(Q(title__icontains=q) | Q(description__icontains=q) | Q(subject__icontains=q))
    if status:
        tasks = tasks.filter(status=status)
    if priority:
        tasks = tasks.filter(priority=priority)
    if task_type:
        tasks = tasks.filter(task_type=task_type)
    if subject:
        tasks = tasks.filter(subject=subject)
    if only_overdue:
        tasks = tasks.filter(due_date__lt=date.today()).exclude(status='concluido')

    subjects = Task.objects.filter(workspace=selected_workspace).order_by('subject').values_list('subject', flat=True).distinct()

    context = {
        'selected_workspace': selected_workspace,
        'workspaces': workspaces,
        'tasks': tasks,
        'subjects': subjects,
        'filters': {
            'q': q,
            'status': status,
            'priority': priority,
            'task_type': task_type,
            'subject': subject,
            'only_overdue': only_overdue,
        },
        'status_choices': Task.STATUS_CHOICES,
        'priority_choices': Task.PRIORITY_CHOICES,
        'task_type_choices': Task.TASK_TYPES,
    }
    return render(request, 'board/task_list.html', context)


@login_required
def task_detail(request, task_id):
    task = get_object_or_404(Task.objects.select_related('workspace', 'author'), id=task_id, workspace__memberships__user=request.user)
    checklist_form = ChecklistItemForm()
    can_manage = can_edit_task(request.user, task)
    checklist_items = task.checklist_items.select_related('created_by').all()
    total_items = checklist_items.count()
    done_items = checklist_items.filter(is_done=True).count()
    checklist_progress = int((done_items / total_items) * 100) if total_items else 0

    context = {
        'task': task,
        'checklist_form': checklist_form,
        'can_manage': can_manage,
        'checklist_items': checklist_items,
        'checklist_progress': checklist_progress,
        'selected_workspace': task.workspace,
    }
    return render(request, 'board/task_detail.html', context)


@login_required
def add_checklist_item(request, task_id):
    task = get_object_or_404(Task, id=task_id, workspace__memberships__user=request.user)
    if not can_edit_task(request.user, task):
        messages.error(request, 'Você não tem permissão para adicionar itens nesta tarefa.')
        return redirect('task_detail', task_id=task.id)

    if request.method == 'POST':
        form = ChecklistItemForm(request.POST)
        if form.is_valid():
            item = form.save(commit=False)
            item.task = task
            item.created_by = request.user
            item.save()
            messages.success(request, 'Item do checklist adicionado.')
    return redirect('task_detail', task_id=task.id)


@login_required
def toggle_checklist_item(request, item_id):
    item = get_object_or_404(ChecklistItem.objects.select_related('task__workspace'), id=item_id, task__workspace__memberships__user=request.user)
    if request.method == 'POST':
        # Regra deliberada: qualquer membro do workspace pode marcar progresso do checklist.
        item.is_done = not item.is_done
        item.save(update_fields=['is_done'])
        messages.success(request, 'Checklist atualizado.')
    return redirect('task_detail', task_id=item.task.id)


@login_required
def task_edit(request, task_id):
    task = get_object_or_404(Task, id=task_id, workspace__memberships__user=request.user)
    if not can_edit_task(request.user, task):
        messages.error(request, 'Você não tem permissão para editar esta tarefa.')
        return redirect('task_detail', task_id=task.id)

    if request.method == 'POST':
        form = TaskForm(request.POST, instance=task)
        if form.is_valid():
            form.save()
            messages.success(request, 'Tarefa atualizada com sucesso.')
            return redirect('task_detail', task_id=task.id)
    else:
        form = TaskForm(instance=task)

    return render(request, 'board/task_form.html', {
        'form': form,
        'selected_workspace': task.workspace,
        'page_title': 'Editar tarefa',
        'submit_label': 'Salvar alterações',
        'task': task,
    })


@login_required
def task_delete(request, task_id):
    task = get_object_or_404(Task, id=task_id, workspace__memberships__user=request.user)
    if not can_edit_task(request.user, task):
        messages.error(request, 'Você não tem permissão para excluir esta tarefa.')
        return redirect('task_detail', task_id=task.id)

    workspace_id = task.workspace.id
    if request.method == 'POST':
        task.delete()
        messages.success(request, 'Tarefa excluída com sucesso.')
        return redirect(f"{reverse('task_list')}?workspace={workspace_id}")

    return render(request, 'board/task_confirm_delete.html', {'task': task, 'selected_workspace': task.workspace})


@login_required
def workspace_members(request):
    workspaces, selected_workspace = get_selected_workspace(request, request.user)
    if not selected_workspace:
        messages.warning(request, 'Crie ou entre em um workspace antes de ver os membros.')
        return redirect('create_workspace')

    selected_membership = get_membership(request.user, selected_workspace)
    memberships = selected_workspace.memberships.select_related('user').order_by('role', 'user__first_name', 'user__username')

    context = {
        'selected_workspace': selected_workspace,
        'workspaces': workspaces,
        'memberships': memberships,
        'selected_membership': selected_membership,
    }
    return render(request, 'board/members.html', context)


@login_required
def update_member_role(request, membership_id):
    membership = get_object_or_404(Membership.objects.select_related('workspace', 'user'), id=membership_id, workspace__memberships__user=request.user)
    workspace = membership.workspace

    if not is_workspace_owner(request.user, workspace):
        messages.error(request, 'Apenas o owner pode alterar papéis.')
        return redirect(f"{reverse('workspace_members')}?workspace={workspace.id}")

    if membership.role == 'owner':
        messages.error(request, 'O papel owner não pode ser alterado por aqui.')
        return redirect(f"{reverse('workspace_members')}?workspace={workspace.id}")

    if request.method == 'POST':
        form = MemberRoleForm(request.POST, instance=membership)
        if form.is_valid():
            form.save()
            messages.success(request, 'Papel do membro atualizado.')
    return redirect(f"{reverse('workspace_members')}?workspace={workspace.id}")


@login_required
def remove_member(request, membership_id):
    membership = get_object_or_404(Membership.objects.select_related('workspace', 'user'), id=membership_id, workspace__memberships__user=request.user)
    workspace = membership.workspace
    requester_membership = get_membership(request.user, workspace)

    if not requester_membership:
        messages.error(request, 'Acesso negado.')
        return redirect('dashboard')

    if membership.role == 'owner':
        messages.error(request, 'O owner não pode ser removido por esta ação.')
        return redirect(f"{reverse('workspace_members')}?workspace={workspace.id}")

    if requester_membership.role == 'owner':
        allowed = True
    elif requester_membership.role == 'admin' and membership.role == 'member':
        allowed = True
    else:
        allowed = False

    if not allowed:
        messages.error(request, 'Você não tem permissão para remover este membro.')
        return redirect(f"{reverse('workspace_members')}?workspace={workspace.id}")

    if request.method == 'POST':
        membership.delete()
        messages.success(request, 'Membro removido com sucesso.')
    return redirect(f"{reverse('workspace_members')}?workspace={workspace.id}")


@login_required
def agenda_view(request):
    workspaces, selected_workspace = get_selected_workspace(request, request.user)
    if not selected_workspace:
        messages.warning(request, 'Crie ou entre em um workspace antes de usar a agenda.')
        return redirect('create_workspace')

    start = date.today()
    end = start + timedelta(days=30)
    tasks = Task.objects.filter(workspace=selected_workspace, due_date__gte=start, due_date__lte=end).select_related('author')

    grouped_tasks = defaultdict(list)
    for task in tasks:
        grouped_tasks[task.due_date].append(task)

    sorted_days = sorted(grouped_tasks.items(), key=lambda item: item[0])

    return render(request, 'board/agenda.html', {
        'selected_workspace': selected_workspace,
        'workspaces': workspaces,
        'sorted_days': sorted_days,
        'start': start,
        'end': end,
    })
