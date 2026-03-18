from django.contrib import admin

from .models import ChecklistItem, Membership, Task, Workspace


@admin.register(Workspace)
class WorkspaceAdmin(admin.ModelAdmin):
    list_display = ('name', 'workspace_type', 'school_name', 'owner', 'invite_code', 'created_at')
    search_fields = ('name', 'school_name', 'invite_code', 'owner__username', 'owner__first_name')
    list_filter = ('workspace_type', 'created_at')


@admin.register(Membership)
class MembershipAdmin(admin.ModelAdmin):
    list_display = ('workspace', 'user', 'role', 'joined_at')
    search_fields = ('workspace__name', 'user__username', 'user__first_name', 'user__email')
    list_filter = ('role', 'joined_at')


class ChecklistInline(admin.TabularInline):
    model = ChecklistItem
    extra = 0


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ('title', 'workspace', 'subject', 'task_type', 'due_date', 'priority', 'status', 'author')
    search_fields = ('title', 'subject', 'workspace__name', 'author__username', 'author__first_name')
    list_filter = ('task_type', 'priority', 'status', 'due_date')
    inlines = [ChecklistInline]


@admin.register(ChecklistItem)
class ChecklistItemAdmin(admin.ModelAdmin):
    list_display = ('title', 'task', 'is_done', 'created_by', 'created_at')
    search_fields = ('title', 'task__title', 'created_by__username', 'created_by__first_name')
    list_filter = ('is_done', 'created_at')
