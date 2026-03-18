from __future__ import annotations

import secrets
from datetime import date

from django.conf import settings
from django.db import models


# Gere códigos curtos e legíveis para convidar membros.
# Você pode trocar o tamanho alterando token_hex(3). token_hex(4) gera um código maior.
def generate_invite_code() -> str:
    return secrets.token_hex(3).upper()


class Workspace(models.Model):
    WORKSPACE_TYPES = [
        ('individual', 'Individual'),
        ('grupo', 'Grupo'),
        ('turma', 'Turma'),
    ]

    name = models.CharField('Nome', max_length=120)
    school_name = models.CharField('Escola', max_length=120, blank=True)
    description = models.TextField('Descrição', blank=True)
    workspace_type = models.CharField('Tipo', max_length=20, choices=WORKSPACE_TYPES, default='turma')
    invite_code = models.CharField('Código de convite', max_length=12, unique=True, default=generate_invite_code)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='owned_workspaces')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Workspace'
        verbose_name_plural = 'Workspaces'
        ordering = ['name']

    def __str__(self):
        return self.name

    def regenerate_invite_code(self):
        self.invite_code = generate_invite_code()
        self.save(update_fields=['invite_code', 'updated_at'])


class Membership(models.Model):
    ROLE_CHOICES = [
        ('owner', 'Owner'),
        ('admin', 'Admin'),
        ('member', 'Member'),
    ]

    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE, related_name='memberships')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='memberships')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='member')
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('workspace', 'user')
        verbose_name = 'Membro'
        verbose_name_plural = 'Membros'
        ordering = ['workspace', 'role', 'user__first_name', 'user__username']

    def __str__(self):
        return f'{self.user} - {self.workspace} ({self.role})'


class Task(models.Model):
    TASK_TYPES = [
        ('prova', 'Prova'),
        ('trabalho', 'Trabalho'),
        ('atividade', 'Atividade'),
        ('apresentacao', 'Apresentação'),
        ('estudo', 'Estudo'),
    ]

    PRIORITY_CHOICES = [
        ('baixa', 'Baixa'),
        ('media', 'Média'),
        ('alta', 'Alta'),
    ]

    STATUS_CHOICES = [
        ('pendente', 'Pendente'),
        ('andamento', 'Em andamento'),
        ('concluido', 'Concluído'),
    ]

    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE, related_name='tasks')
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='tasks')
    title = models.CharField('Título', max_length=150)
    description = models.TextField('Descrição', blank=True)
    subject = models.CharField('Matéria', max_length=80)
    task_type = models.CharField('Tipo', max_length=20, choices=TASK_TYPES)
    due_date = models.DateField('Data')
    priority = models.CharField('Prioridade', max_length=20, choices=PRIORITY_CHOICES, default='media')
    status = models.CharField('Status', max_length=20, choices=STATUS_CHOICES, default='pendente')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['due_date', 'title']
        verbose_name = 'Tarefa'
        verbose_name_plural = 'Tarefas'

    def __str__(self):
        return self.title

    @property
    def is_overdue(self) -> bool:
        return self.due_date < date.today() and self.status != 'concluido'

    @property
    def days_left(self) -> int:
        return (self.due_date - date.today()).days


class ChecklistItem(models.Model):
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='checklist_items')
    title = models.CharField('Item', max_length=180)
    is_done = models.BooleanField('Concluído', default=False)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='created_checklist_items')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Item de checklist'
        verbose_name_plural = 'Itens de checklist'
        ordering = ['is_done', 'created_at']

    def __str__(self):
        return f'{self.task.title} - {self.title}'
