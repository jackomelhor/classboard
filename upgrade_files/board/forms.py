import secrets
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from .models import ChecklistItem, Membership, Task, Workspace


class RegisterForm(UserCreationForm):
    first_name = forms.CharField(label='Nome', max_length=150)
    email = forms.EmailField(label='Email')

    class Meta:
        model = User
        fields = ('first_name', 'username', 'email', 'password1', 'password2')


class WorkspaceForm(forms.ModelForm):
    class Meta:
        model = Workspace
        fields = ('name', 'school_name', 'description', 'workspace_type')
        labels = {
            'name': 'Nome da turma ou grupo',
            'school_name': 'Escola',
            'description': 'Descrição',
            'workspace_type': 'Tipo de workspace',
        }
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Ex.: turma de matemática do 2º B'}),
        }

    def save(self, commit=True, owner=None):
        workspace = super().save(commit=False)
        # Se quiser código maior, troque token_hex(3) por token_hex(4).
        workspace.invite_code = secrets.token_hex(3).upper()
        if owner is not None:
            workspace.owner = owner
        if commit:
            workspace.save()
            Membership.objects.get_or_create(
                workspace=workspace,
                user=owner,
                defaults={'role': 'owner'},
            )
        return workspace


class TaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = ('title', 'description', 'subject', 'task_type', 'due_date', 'priority', 'status')
        widgets = {
            'due_date': forms.DateInput(attrs={'type': 'date'}),
            'description': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Detalhes da tarefa, orientações, materiais...'}),
        }


class JoinWorkspaceForm(forms.Form):
    invite_code = forms.CharField(
        label='Código de convite',
        max_length=12,
        widget=forms.TextInput(attrs={'placeholder': 'Ex.: A1B2C3', 'style': 'text-transform: uppercase;'}),
    )

    def clean_invite_code(self):
        return self.cleaned_data['invite_code'].strip().upper()


class ChecklistItemForm(forms.ModelForm):
    class Meta:
        model = ChecklistItem
        fields = ('title',)
        labels = {'title': 'Novo item'}
        widgets = {
            'title': forms.TextInput(attrs={'placeholder': 'Ex.: revisar slides'}),
        }


class MemberRoleForm(forms.ModelForm):
    class Meta:
        model = Membership
        fields = ('role',)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # O papel owner não deve ser editado pelo formulário.
        self.fields['role'].choices = [
            choice for choice in Membership.ROLE_CHOICES if choice[0] != 'owner'
        ]
