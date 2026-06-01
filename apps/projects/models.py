from django.conf import settings
from django.db import models


class ProjectStatus(models.TextChoices):
    ACTIVE = 'active', 'Active'
    COMPLETED = 'completed', 'Completed'


class SummaryStatus(models.TextChoices):
    IDLE = 'idle', 'Idle'
    PROCESSING = 'processing', 'Processing'
    COMPLETED = 'completed', 'Completed'
    FAILED = 'failed', 'Failed'


class VoiceNoteStatus(models.TextChoices):
    PENDING = 'pending', 'Pending'
    PROCESSING = 'processing', 'Processing'
    COMPLETED = 'completed', 'Completed'
    FAILED = 'failed', 'Failed'


class Project(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='projects',
    )
    project_name = models.CharField(max_length=200)
    customer_name = models.CharField(max_length=200)
    status = models.CharField(
        max_length=20,
        choices=ProjectStatus.choices,
        default=ProjectStatus.ACTIVE,
    )
    ai_project_summary = models.TextField(blank=True)
    summary_manually_edited = models.BooleanField(default=False)
    ai_financials = models.JSONField(null=True, blank=True)
    financials_manually_edited = models.BooleanField(default=False)
    project_summary_status = models.CharField(
        max_length=20,
        choices=SummaryStatus.choices,
        default=SummaryStatus.IDLE,
    )
    project_summary_error = models.TextField(blank=True)
    project_summary_updated_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']
        indexes = [
            models.Index(fields=['user', 'status']),
        ]

    def __str__(self):
        return self.project_name

    @property
    def voice_note_count(self):
        return self.voice_notes.count()

    @property
    def latest_activity(self):
        note = (
            self.voice_notes.filter(processing_status=VoiceNoteStatus.COMPLETED)
            .exclude(summary='')
            .order_by('-created_at')
            .first()
        )
        if not note or not note.summary:
            return ''
        first_line = note.summary.strip().splitlines()[0]
        return first_line[:120] + ('…' if len(first_line) > 120 else '')

    @property
    def profit_display(self):
        from apps.projects.services.financials import get_profit

        return get_profit(self.ai_financials)


class VoiceNote(models.Model):
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name='voice_notes',
    )
    audio_file = models.FileField(upload_to='voice_notes/%Y/%m/')
    transcript = models.TextField(blank=True)
    summary = models.TextField(blank=True)
    summary_manually_edited = models.BooleanField(default=False)
    financial_extract = models.JSONField(null=True, blank=True)
    processing_status = models.CharField(
        max_length=20,
        choices=VoiceNoteStatus.choices,
        default=VoiceNoteStatus.PENDING,
    )
    error_message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['project', '-created_at']),
            models.Index(fields=['project', 'processing_status']),
        ]

    def __str__(self):
        return f'VoiceNote #{self.pk} — {self.project.project_name}'

    @property
    def financial_preview(self):
        data = self.financial_extract or {}
        income = data.get('income')
        expenses = data.get('expenses') or []
        parts = []
        if income is not None:
            parts.append(f'Income {income}')
        if expenses:
            parts.append(f'{len(expenses)} expense(s)')
        return ' · '.join(parts) if parts else ''
