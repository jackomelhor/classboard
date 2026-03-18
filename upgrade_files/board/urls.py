from django.urls import path

from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('cadastro/', views.register_view, name='register'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('workspace/novo/', views.create_workspace, name='create_workspace'),
    path('workspace/entrar/', views.join_workspace, name='join_workspace'),
    path('workspace/membros/', views.workspace_members, name='workspace_members'),
    path('workspace/<int:workspace_id>/novo-codigo/', views.regenerate_invite_code, name='regenerate_invite_code'),
    path('tarefas/', views.task_list, name='task_list'),
    path('tarefas/nova/', views.create_task, name='create_task'),
    path('tarefas/<int:task_id>/', views.task_detail, name='task_detail'),
    path('tarefas/<int:task_id>/editar/', views.task_edit, name='task_edit'),
    path('tarefas/<int:task_id>/excluir/', views.task_delete, name='task_delete'),
    path('tarefas/<int:task_id>/checklist/adicionar/', views.add_checklist_item, name='add_checklist_item'),
    path('checklist/<int:item_id>/alternar/', views.toggle_checklist_item, name='toggle_checklist_item'),
    path('membros/<int:membership_id>/papel/', views.update_member_role, name='update_member_role'),
    path('membros/<int:membership_id>/remover/', views.remove_member, name='remove_member'),
    path('agenda/', views.agenda_view, name='agenda'),
]
