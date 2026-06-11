"""
RVC 语音生成 — 通过 HuggingFace Space API
申鹤端点: /vc_fn_27 (日语 CV: 川澄綾子)
"""
import uuid
from pathlib import Path
from gradio_client import Client, handle_file

import config

SPACE = "ArkanDash/rvc-models-new"
SHENHE_ENDPOINT = "/vc_fn_27"
SPEAKER = "zh-CN-XiaoxiaoNeural-Female"

_client = None


def _get_client():
    global _client
    if _client is None:
        _client = Client(SPACE)
    return _client


def generate_rvc_voice(text: str) -> str | None:
    """将中文文本通过 HF Space 转为申鹤 RVC 语音。返回本地文件路径。"""
    if not text.strip():
        return None

    try:
        client = _get_client()
        result = client.predict(
            input_voice="TTS Audio",
            input_audio_path="",
            upload_audio_file=handle_file("https://github.com/gradio-app/gradio/raw/main/test/test_files/audio_sample.wav"),
            tts_text=text,
            edgetts_speaker=SPEAKER,
            transpose=0,
            pitch_extraction_algorithm="harvest",
            retrieval_feature_ratio=0.5,
            apply_median_filtering=3,
            resample_the_output_audio=0,
            volume_envelope=1.0,
            voice_protection=0.33,
            api_name=SHENHE_ENDPOINT,
        )

        info, audio_path = result
        print(f"[rvc_api] {info.strip()}")

        if audio_path is None:
            print("[rvc_api] 推理失败，返回 None")
            return None

        # 下载音频到本地
        config.AUDIO_DIR.mkdir(parents=True, exist_ok=True)
        local_path = config.AUDIO_DIR / f"shenhe_rvc_{uuid.uuid4().hex[:8]}.wav"

        import shutil
        shutil.copy(audio_path, str(local_path))

        if local_path.exists():
            return str(local_path)
        return None

    except Exception as e:
        print(f"[rvc_api] 异常: {e}")
        return None
