import json
import logging

from django.conf import settings
from openai import OpenAI

from apps.projects.services.financials import normalize_financials

logger = logging.getLogger(__name__)

VOICE_NOTE_SYSTEM_PROMPT = """你是承包商 job costing 助手。根据以下语音转写（可能是中文、英文或中英混合），返回 JSON：

{
  "summary": "简洁摘要（进展、工时、待办等）",
  "financial_extract": {
    "income": <number|null>,
    "expenses": [{"label": "<口述原文>", "amount": <number>}],
    "profit": <number|null>
  }
}

规则：
- 收入：如「收入8000」「卖了8000」「this job is 8000」→ income: 8000（必须写入 income，不能放进 expenses）
- 花费：逐项提取，label 保留用户原话（人工费、材料费、吃饭费等）
- 未提及金额则 income 为 null、expenses 为 []
- 数字只用阿拉伯数字，不要货币符号
- 中英文金额都要识别（eight thousand = 8000）
"""

def _normalize_text(value) -> str:
    """GPT JSON may return a list for summary fields; coerce to a single string."""
    if value is None:
        return ''
    if isinstance(value, list):
        lines = []
        for item in value:
            if item is None:
                continue
            text = str(item).strip()
            if text:
                lines.append(text)
        return '\n'.join(lines)
    return str(value).strip()


def _client() -> OpenAI:
    if not settings.OPENAI_API_KEY:
        raise RuntimeError('OPENAI_API_KEY is not configured.')
    return OpenAI(api_key=settings.OPENAI_API_KEY)


def transcribe_audio(file_path: str) -> str:
    client = _client()
    with open(file_path, 'rb') as audio_file:
        response = client.audio.transcriptions.create(
            model=settings.OPENAI_TRANSCRIPTION_MODEL,
            # Explicit ASCII filename — Windows paths in file.name break httpx headers
            file=('recording.webm', audio_file, 'audio/webm'),
        )
    return (response.text or '').strip()


def analyze_voice_note_transcript(transcript: str) -> dict:
    client = _client()
    response = client.chat.completions.create(
        model=settings.OPENAI_SUMMARY_MODEL,
        response_format={'type': 'json_object'},
        messages=[
            {'role': 'system', 'content': VOICE_NOTE_SYSTEM_PROMPT},
            {'role': 'user', 'content': transcript},
        ],
    )
    payload = json.loads(response.choices[0].message.content or '{}')
    financial = normalize_financials(payload.get('financial_extract'))
    return {
        'summary': _normalize_text(payload.get('summary')),
        'financial_extract': financial,
    }

