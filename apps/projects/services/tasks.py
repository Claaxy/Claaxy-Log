import logging
import threading

from django.db import close_old_connections
from django.utils import timezone

from apps.projects.models import Project, SummaryStatus, VoiceNote, VoiceNoteStatus
from apps.projects.services import openai_service
from apps.projects.services.financials import merge_voice_note_financials

logger = logging.getLogger(__name__)


def _run_in_thread(target, *args):
    thread = threading.Thread(target=target, args=args, daemon=True)
    thread.start()


def enqueue_voice_note_processing(voice_note_id: int):
    _run_in_thread(process_voice_note, voice_note_id)


def enqueue_project_update(project_id: int, regenerate_voice_note_id: int | None = None):
    _run_in_thread(update_project_from_voice_notes, project_id, regenerate_voice_note_id)


def process_voice_note(voice_note_id: int):
    close_old_connections()
    try:
        note = VoiceNote.objects.select_related('project').get(pk=voice_note_id)
    except VoiceNote.DoesNotExist:
        return

    note.processing_status = VoiceNoteStatus.PROCESSING
    note.error_message = ''
    note.save(update_fields=['processing_status', 'error_message'])

    try:
        transcript = openai_service.transcribe_audio(note.audio_file.path)
        note.transcript = transcript

        if transcript.strip():
            analysis = openai_service.analyze_voice_note_transcript(transcript)
            note.summary = analysis['summary']
            note.financial_extract = analysis['financial_extract']
            if not note.summary_manually_edited:
                note.summary_manually_edited = False
        else:
            note.summary = ''
            note.financial_extract = None

        note.processing_status = VoiceNoteStatus.COMPLETED
        note.save(
            update_fields=[
                'transcript',
                'summary',
                'financial_extract',
                'processing_status',
            ]
        )
        note.project.save(update_fields=['updated_at'])
        update_project_from_voice_notes(note.project_id)
    except Exception as exc:
        logger.exception('Voice note processing failed: %s', voice_note_id)
        note.processing_status = VoiceNoteStatus.FAILED
        note.error_message = str(exc)
        note.save(update_fields=['processing_status', 'error_message'])


def reprocess_voice_note_from_transcript(voice_note_id: int):
    close_old_connections()
    try:
        note = VoiceNote.objects.select_related('project').get(pk=voice_note_id)
    except VoiceNote.DoesNotExist:
        return

    if not note.transcript.strip():
        process_voice_note(voice_note_id)
        return

    note.processing_status = VoiceNoteStatus.PROCESSING
    note.error_message = ''
    note.save(update_fields=['processing_status', 'error_message'])

    try:
        analysis = openai_service.analyze_voice_note_transcript(note.transcript)
        note.summary = analysis['summary']
        note.financial_extract = analysis['financial_extract']
        note.summary_manually_edited = False
        note.processing_status = VoiceNoteStatus.COMPLETED
        note.save(
            update_fields=[
                'summary',
                'financial_extract',
                'summary_manually_edited',
                'processing_status',
            ]
        )
        update_project_from_voice_notes(note.project_id)
    except Exception as exc:
        logger.exception('Voice note regenerate failed: %s', voice_note_id)
        note.processing_status = VoiceNoteStatus.FAILED
        note.error_message = str(exc)
        note.save(update_fields=['processing_status', 'error_message'])


def update_project_from_voice_notes(project_id: int):
    close_old_connections()
    try:
        project = Project.objects.get(pk=project_id)
    except Project.DoesNotExist:
        return

    extracts = list(
        project.voice_notes.filter(processing_status=VoiceNoteStatus.COMPLETED)
        .order_by('created_at')
        .values_list('financial_extract', flat=True)
    )

    if project.financials_manually_edited:
        return

    try:
        project.ai_financials = merge_voice_note_financials(extracts)
        project.project_summary_status = SummaryStatus.COMPLETED
        project.project_summary_error = ''
        project.project_summary_updated_at = timezone.now()
        project.save(
            update_fields=[
                'ai_financials',
                'project_summary_status',
                'project_summary_error',
                'project_summary_updated_at',
            ]
        )
    except Exception as exc:
        logger.exception('Project finances merge failed: %s', project_id)
        project.project_summary_status = SummaryStatus.FAILED
        project.project_summary_error = str(exc)
        project.save(update_fields=['project_summary_status', 'project_summary_error'])
