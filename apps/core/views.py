from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from apps.projects.models import Project, VoiceNote, VoiceNoteStatus
from apps.projects.services.financials import (
    format_money,
    get_date_range_bounds,
    parse_dashboard_date,
    sum_financials_from_extracts,
)


def home(request):
    if request.user.is_authenticated:
        return redirect('core:dashboard')
    google_configured = bool(settings.SOCIALACCOUNT_PROVIDERS['google']['APP']['client_id'])
    return render(
        request,
        'core/home.html',
        {'google_configured': google_configured},
    )


@login_required
def dashboard(request):
    projects = list(
        Project.objects.filter(user=request.user).order_by('-updated_at')
    )

    selected_project = None
    project_id = request.GET.get('project')
    if project_id and projects:
        selected_project = get_object_or_404(Project, pk=project_id, user=request.user)
    elif projects:
        selected_project = projects[0]

    from_date_str = request.GET.get('from_date', '').strip()
    to_date_str = request.GET.get('to_date', '').strip()
    from_date = parse_dashboard_date(from_date_str)
    to_date = parse_dashboard_date(to_date_str)

    summary_ready = False
    date_range_error = ''
    totals = {'income': None, 'expense_total': 0, 'profit': None}

    if from_date_str or to_date_str:
        if not from_date or not to_date:
            date_range_error = 'Enter valid From and To dates.'
        elif from_date > to_date:
            date_range_error = 'From date must be on or before To date.'
        else:
            summary_ready = True
            range_start, range_end = get_date_range_bounds(from_date, to_date)
            notes_in_range = VoiceNote.objects.filter(
                project__user=request.user,
                processing_status=VoiceNoteStatus.COMPLETED,
                created_at__gte=range_start,
                created_at__lte=range_end,
            )
            extracts = list(notes_in_range.values_list('financial_extract', flat=True))
            totals = sum_financials_from_extracts(extracts)

    return render(
        request,
        'core/dashboard.html',
        {
            'projects': projects,
            'selected_project': selected_project,
            'from_date': from_date_str,
            'to_date': to_date_str,
            'summary_ready': summary_ready,
            'date_range_error': date_range_error,
            'totals': totals,
            'total_income_display': format_money(totals['income']) if summary_ready else '—',
            'total_expense_display': format_money(totals['expense_total']) if summary_ready else '—',
            'total_profit_display': format_money(totals['profit']) if summary_ready else '—',
        },
    )
