from django import forms

from apps.projects.models import Project, ProjectStatus


class ProjectForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = ['project_name', 'customer_name', 'status']
        widgets = {
            'project_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Project name'}),
            'customer_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Customer name'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['status'].choices = ProjectStatus.choices


class ProjectStatusForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = ['status']
        widgets = {
            'status': forms.Select(attrs={'class': 'form-select form-select-sm', 'onchange': 'this.form.submit()'}),
        }


class SummaryEditForm(forms.Form):
    summary = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 5}),
        required=True,
    )


class IncomeAmountForm(forms.Form):
    amount = forms.CharField(
        required=False,
        widget=forms.TextInput(
            attrs={'class': 'form-control form-control-sm finances-amount-input', 'inputmode': 'decimal'},
        ),
    )

    def clean_amount(self):
        from apps.projects.services.financials import parse_amount

        raw = (self.cleaned_data.get('amount') or '').strip()
        if not raw or raw == '—':
            return None
        try:
            return parse_amount(raw)
        except (TypeError, ValueError) as exc:
            raise forms.ValidationError('Enter a valid amount.') from exc


class ExpenseRowForm(forms.Form):
    label = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={'class': 'form-control form-control-sm'}),
    )
    amount = forms.CharField(
        widget=forms.TextInput(
            attrs={'class': 'form-control form-control-sm finances-amount-input', 'inputmode': 'decimal'},
        ),
    )

    def clean_amount(self):
        from apps.projects.services.financials import parse_amount

        raw = (self.cleaned_data.get('amount') or '').strip()
        if not raw:
            raise forms.ValidationError('Amount is required.')
        try:
            value = parse_amount(raw)
        except (TypeError, ValueError) as exc:
            raise forms.ValidationError('Enter a valid amount.') from exc
        if value is None or value < 0:
            raise forms.ValidationError('Enter a valid amount.')
        return value
