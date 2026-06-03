from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_GET, require_POST

from apps.projects.forms import ExpenseRowForm, IncomeAmountForm, ProjectForm, ProjectStatusForm, SummaryEditForm
from apps.projects.models import Project, VoiceNote, VoiceNoteStatus
from apps.projects.services.financials import (
    clone_financials,
    format_money,
    get_profit,
    save_manual_financials,
)
from apps.projects.services.tasks import (
    enqueue_project_update,
    enqueue_voice_note_processing,
    reprocess_voice_note_from_transcript,
)

def get_user_project(user, pk):
    return get_object_or_404(Project, pk=pk, user=user)


@login_required
def project_create(request):
    if request.method == 'POST':
        form = ProjectForm(request.POST)
        if form.is_valid():
            project = form.save(commit=False)
            project.user = request.user
            project.save()
            return redirect('projects:detail', pk=project.pk)
    else:
        form = ProjectForm()
    return render(request, 'projects/project_form.html', {'form': form, 'title': 'New Project'})


@login_required
def project_detail(request, pk):
    project = get_user_project(request.user, pk)
    voice_notes = project.voice_notes.all()
    status_form = ProjectStatusForm(instance=project)
    needs_poll = voice_notes.filter(
        processing_status__in=[VoiceNoteStatus.PENDING, VoiceNoteStatus.PROCESSING]
    ).exists()
    return render(
        request,
        'projects/project_detail.html',
        {
            'project': project,
            'voice_notes': voice_notes,
            'status_form': status_form,
            'needs_poll': needs_poll,
            'financials': project.ai_financials or {'income': None, 'expenses': []},
            'profit': get_profit(project.ai_financials),
        },
    )


@login_required
@require_POST
def project_status_update(request, pk):
    project = get_user_project(request.user, pk)
    form = ProjectStatusForm(request.POST, instance=project)
    if form.is_valid():
        form.save()
    return redirect('projects:detail', pk=project.pk)


@login_required
@require_POST
def project_delete(request, pk):
    from django.contrib import messages

    project = get_user_project(request.user, pk)
    project_name = project.project_name
    for note in project.voice_notes.all():
        if note.audio_file:
            note.audio_file.delete(save=False)
    project.delete()
    messages.success(request, f'Project "{project_name}" deleted.')
    return redirect('core:dashboard')


@login_required
@require_GET
def project_status_api(request, pk):
    project = get_user_project(request.user, pk)
    voice_notes = [
        {
            'id': note.id,
            'processing_status': note.processing_status,
            'summary': note.summary,
            'financial_preview': note.financial_preview,
        }
        for note in project.voice_notes.all().order_by('-created_at')
    ]
    return JsonResponse(
        {
            'voice_notes': voice_notes,
            'ai_financials': project.ai_financials,
            'latest_activity': project.latest_activity,
            'voice_note_count': project.voice_note_count,
            'profit_display': format_money(get_profit(project.ai_financials)),
        }
    )


@login_required
@require_POST
def voice_note_upload(request, pk):
    from django.conf import settings
    from django.contrib import messages

    project = get_user_project(request.user, pk)
    audio = request.FILES.get('audio')
    if not audio:
        return redirect('projects:detail', pk=project.pk)

    if audio.size > settings.VOICE_NOTE_MAX_BYTES:
        messages.error(request, 'Audio file is too large (max 25MB).')
        return redirect('projects:detail', pk=project.pk)

    content_type = getattr(audio, 'content_type', '') or ''
    if content_type and content_type not in settings.ALLOWED_AUDIO_CONTENT_TYPES:
        messages.error(request, f'Unsupported audio type: {content_type}')
        return redirect('projects:detail', pk=project.pk)

    note = VoiceNote.objects.create(
        project=project,
        audio_file=audio,
        processing_status=VoiceNoteStatus.PENDING,
    )
    project.save(update_fields=['updated_at'])
    enqueue_voice_note_processing(note.pk)
    messages.success(request, 'Uploaded — processing in background…')
    return redirect('projects:detail', pk=project.pk)


@login_required
@require_POST
def voice_note_regenerate(request, pk, note_id):
    project = get_user_project(request.user, pk)
    note = get_object_or_404(VoiceNote, pk=note_id, project=project)
    note.summary_manually_edited = False
    note.save(update_fields=['summary_manually_edited'])
    if note.transcript.strip():
        reprocess_voice_note_from_transcript(note.pk)
    else:
        enqueue_voice_note_processing(note.pk)
    return redirect('projects:detail', pk=project.pk)


@login_required
@require_POST
def voice_note_edit_summary(request, pk, note_id):
    project = get_user_project(request.user, pk)
    note = get_object_or_404(VoiceNote, pk=note_id, project=project)
    form = SummaryEditForm(request.POST)
    if form.is_valid():
        note.summary = form.cleaned_data['summary']
        note.summary_manually_edited = True
        note.save(update_fields=['summary', 'summary_manually_edited'])
    return redirect('projects:detail', pk=project.pk)


@login_required
@require_POST
def voice_note_delete(request, pk, note_id):
    project = get_user_project(request.user, pk)
    note = get_object_or_404(VoiceNote, pk=note_id, project=project)
    if note.audio_file:
        note.audio_file.delete(save=False)
    note.delete()
    enqueue_project_update(project.pk)
    return redirect('projects:detail', pk=project.pk)


@login_required
@require_POST
def voice_note_retry(request, pk, note_id):
    project = get_user_project(request.user, pk)
    note = get_object_or_404(VoiceNote, pk=note_id, project=project)
    enqueue_voice_note_processing(note.pk)
    return redirect('projects:detail', pk=project.pk)


@login_required
@require_POST
def finances_income_update(request, pk):
    project = get_user_project(request.user, pk)
    form = IncomeAmountForm(request.POST)
    if form.is_valid():
        data = clone_financials(project.ai_financials)
        amount = form.cleaned_data['amount']
        data['income'] = float(amount) if amount is not None else None
        save_manual_financials(project, data)
    return redirect('projects:detail', pk=project.pk)


@login_required
@require_POST
def finances_income_clear(request, pk):
    project = get_user_project(request.user, pk)
    data = clone_financials(project.ai_financials)
    data['income'] = None
    save_manual_financials(project, data)
    return redirect('projects:detail', pk=project.pk)


@login_required
@require_POST
def finances_expense_add(request, pk):
    from django.contrib import messages

    project = get_user_project(request.user, pk)
    form = ExpenseRowForm(request.POST)
    if not form.is_valid():
        err = next(iter(form.errors.values()), [None])[0]
        messages.error(request, err or 'Could not add expense. Check the item name and amount.')
        return redirect('projects:detail', pk=project.pk)

    data = clone_financials(project.ai_financials)
    expenses = data.get('expenses') or []
    expenses.append({
        'label': form.cleaned_data['label'].strip() or 'Expense',
        'amount': float(form.cleaned_data['amount']),
    })
    data['expenses'] = expenses
    save_manual_financials(project, data)
    return redirect('projects:detail', pk=project.pk)


@login_required
@require_POST
def finances_expense_update(request, pk, index):
    project = get_user_project(request.user, pk)
    form = ExpenseRowForm(request.POST)
    if not form.is_valid():
        return redirect('projects:detail', pk=project.pk)

    data = clone_financials(project.ai_financials)
    expenses = data.get('expenses') or []
    if index < 0 or index >= len(expenses):
        return redirect('projects:detail', pk=project.pk)

    expenses[index] = {
        'label': form.cleaned_data['label'].strip() or 'Expense',
        'amount': float(form.cleaned_data['amount']),
    }
    data['expenses'] = expenses
    save_manual_financials(project, data)
    return redirect('projects:detail', pk=project.pk)


@login_required
@require_POST
def finances_expense_delete(request, pk, index):
    project = get_user_project(request.user, pk)
    data = clone_financials(project.ai_financials)
    expenses = data.get('expenses') or []
    if 0 <= index < len(expenses):
        expenses.pop(index)
        data['expenses'] = expenses
        save_manual_financials(project, data)
    return redirect('projects:detail', pk=project.pk)
