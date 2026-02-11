"""Voice message transcription via Whisper ASR API (OpenAI-compatible or Faster-Whisper)"""

import os
import json
import aiohttp
from config import ASR_URL, ASR_TIMEOUT, ASR_LANGUAGE


def _get_asr_config() -> dict:
    """Get ASR config from shared file or env defaults
    
    Returns:
        dict: Configuration with keys: url, timeout, language, enabled, api_key, api_type
    """
    config = {
        "url": ASR_URL, 
        "timeout": ASR_TIMEOUT, 
        "language": ASR_LANGUAGE, 
        "enabled": bool(ASR_URL),
        "api_key": "",  # Bearer token для авторизации
        "api_type": "openai",  # "openai" (OpenAI-compatible) или "faster-whisper" (legacy)
    }
    try:
        path = "/data/asr_config.json"
        if os.path.exists(path):
            with open(path) as f:
                saved = json.load(f)
                config.update(saved)
    except:
        pass
    return config


async def transcribe_voice(file_url: str, duration: int) -> str:
    """Download voice from Telegram and transcribe via Whisper API
    
    Поддерживает два типа API:
    - OpenAI-compatible (/v1/audio/transcriptions) - для remote whisper серверов
    - Faster-Whisper (/api/v1/transcribe) - legacy для локального faster-whisper
    
    Args:
        file_url: Telegram file URL для скачивания аудио
        duration: Длительность голосового сообщения в секундах
    
    Returns:
        Транскрибированный текст
    
    Raises:
        Exception: При ошибке ASR или если ASR отключен
    """
    cfg = _get_asr_config()
    asr_url = cfg.get("url", "")
    if not asr_url or not cfg.get("enabled", True):
        raise Exception("ASR not configured or disabled")

    asr_timeout = cfg.get("timeout", 60)
    asr_language = cfg.get("language", "ru")
    api_key = cfg.get("api_key", "")
    api_type = cfg.get("api_type", "openai")

    timeout = aiohttp.ClientTimeout(total=asr_timeout)

    async with aiohttp.ClientSession(timeout=timeout) as session:
        # 1. Download OGG from Telegram
        async with session.get(file_url) as resp:
            if resp.status != 200:
                raise Exception(f"Failed to download audio: {resp.status}")
            audio_data = await resp.read()

        print(f"[voice] Downloaded {len(audio_data) / 1024:.1f}KB, duration: {duration}s, api_type: {api_type}")

        # 2. Send to ASR API
        if api_type == "openai":
            # OpenAI-compatible API (remote Whisper servers)
            result = await _transcribe_openai_api(
                session, asr_url, audio_data, asr_language, api_key
            )
        else:
            # Legacy Faster-Whisper API
            result = await _transcribe_faster_whisper_api(
                session, asr_url, audio_data, asr_language
            )

    return result


async def _transcribe_openai_api(
    session: aiohttp.ClientSession,
    asr_url: str,
    audio_data: bytes,
    language: str,
    api_key: str
) -> str:
    """Transcribe via OpenAI-compatible API (/v1/audio/transcriptions)
    
    Формат запроса как у OpenAI Whisper API.
    
    Args:
        session: aiohttp session
        asr_url: Base URL сервера (например http://109.230.162.92:8500)
        audio_data: Аудио данные (OGG)
        language: Язык для транскрипции
        api_key: Bearer token для авторизации
    
    Returns:
        Транскрибированный текст
    """
    headers = {"Accept": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    
    form = aiohttp.FormData()
    form.add_field("file", audio_data, filename="voice.ogg", content_type="audio/ogg")
    form.add_field("model", "whisper-1")
    form.add_field("response_format", "json")
    form.add_field("temperature", "0")
    if language:
        form.add_field("language", language)
    
    endpoint = f"{asr_url.rstrip('/')}/v1/audio/transcriptions"
    
    async with session.post(endpoint, data=form, headers=headers) as resp:
        if resp.status != 200:
            error_text = await resp.text()
            raise Exception(f"ASR error: {resp.status} {error_text[:200]}")
        result = await resp.json()
    
    # OpenAI API returns {"text": "..."}
    text = result.get("text", "")
    if not text:
        raise Exception("Empty ASR response")
    
    # Опционально логируем детали
    duration_sec = result.get("duration", 0)
    lang = result.get("language", "?")
    print(f'[voice] Transcribed (openai, lang={lang}, dur={duration_sec:.1f}s): "{text[:80]}{"..." if len(text) > 80 else ""}"')
    
    return text


async def _transcribe_faster_whisper_api(
    session: aiohttp.ClientSession,
    asr_url: str,
    audio_data: bytes,
    language: str
) -> str:
    """Transcribe via Faster-Whisper API (/api/v1/transcribe) - legacy
    
    Args:
        session: aiohttp session
        asr_url: Base URL сервера
        audio_data: Аудио данные (OGG)
        language: Язык для транскрипции
    
    Returns:
        Транскрибированный текст
    """
    form = aiohttp.FormData()
    form.add_field("file", audio_data, filename="voice.ogg", content_type="audio/ogg")
    if language:
        form.add_field("language", language)

    async with session.post(f"{asr_url}/api/v1/transcribe", data=form) as resp:
        if resp.status != 200:
            error_text = await resp.text()
            raise Exception(f"ASR error: {resp.status} {error_text[:200]}")
        result = await resp.json()

    # Extract text from Faster-Whisper response
    full_text = result.get("full_text", "")
    if not full_text:
        segments = result.get("segments", [])
        full_text = " ".join(s.get("text", "") for s in segments).strip()

    if not full_text:
        raise Exception("Empty ASR response")

    model = result.get("model", "?")
    proc_time = result.get("processing_time", 0)
    print(f'[voice] Transcribed (faster-whisper, model={model}, {proc_time:.1f}s): "{full_text[:80]}{"..." if len(full_text) > 80 else ""}"')

    return full_text


async def check_asr_health() -> dict:
    """Check ASR server health. Returns status dict or error.
    
    Поддерживает оба типа серверов:
    - OpenAI-compatible: проверяет /docs или базовый URL
    - Faster-Whisper: проверяет /health/ready
    
    Returns:
        dict: {status, url, ...} со статусом сервера
    """
    cfg = _get_asr_config()
    asr_url = cfg.get("url", "")
    
    if not asr_url or not cfg.get("enabled", True):
        return {"status": "disabled", "url": ""}
    
    api_type = cfg.get("api_type", "openai")
    api_key = cfg.get("api_key", "")
    
    try:
        timeout = aiohttp.ClientTimeout(total=5)
        headers = {}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
        
        async with aiohttp.ClientSession(timeout=timeout) as session:
            if api_type == "openai":
                # OpenAI-compatible: проверяем базовый URL или /docs
                async with session.get(f"{asr_url}/docs", headers=headers) as resp:
                    if resp.status in (200, 307):
                        return {
                            "status": "ready",
                            "url": asr_url,
                            "api_type": "openai",
                            "note": "OpenAI-compatible API"
                        }
                    return {"status": "error", "url": asr_url, "http_status": resp.status}
            else:
                # Faster-Whisper: проверяем /health/ready
                async with session.get(f"{asr_url}/health/ready") as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        data["url"] = asr_url
                        data["api_type"] = "faster-whisper"
                        return data
                    return {"status": "error", "url": asr_url, "http_status": resp.status}
    except Exception as e:
        return {"status": "error", "url": asr_url, "error": str(e)}
