import asyncio
import re
import uuid
from pathlib import Path

import edge_tts
import requests

import config

IMAGE_TAG = re.compile(r"\[IMAGE:\s*(.+?)\]", re.DOTALL)


def parse_image_request(text: str) -> tuple[str, str | None]:
    """从回复中提取 [IMAGE: ...] 标签。"""
    match = IMAGE_TAG.search(text)
    if match:
        clean = IMAGE_TAG.sub("", text).strip()
        return clean, match.group(1).strip()
    return text, None


def generate_image(prompt: str) -> str | None:
    """生成图片。优先用免费的 Pollinations.ai，如有 Stability key 则用它。"""
    config.IMAGE_DIR.mkdir(parents=True, exist_ok=True)

    # 如果有 Stability API key，用它（质量更高）
    if config.STABILITY_API_KEY:
        return _generate_stability(prompt)

    # 否则用免费的 Pollinations.ai
    return _generate_pollinations(prompt)


def _generate_pollinations(prompt: str) -> str | None:
    """Pollinations.ai — 免费，无需 API key。"""
    try:
        from urllib.parse import quote
        # 简化 prompt，英文效果更好
        short_prompt = prompt[:200] if len(prompt) > 200 else prompt
        url = f"https://image.pollinations.ai/prompt/{quote(short_prompt, safe='')}?width=1024&height=1024&nologo=true"
        response = requests.get(url, timeout=120)
        if response.status_code == 200 and len(response.content) > 5000:
            filepath = config.IMAGE_DIR / f"img_{uuid.uuid4().hex[:8]}.png"
            filepath.write_bytes(response.content)
            return str(filepath)
        # 如果失败，尝试用小尺寸
        if response.status_code == 200:
            url2 = f"https://image.pollinations.ai/prompt/{quote(short_prompt[:100], safe='')}?width=512&height=512&nologo=true"
            r2 = requests.get(url2, timeout=60)
            if r2.status_code == 200 and len(r2.content) > 5000:
                filepath = config.IMAGE_DIR / f"img_{uuid.uuid4().hex[:8]}.png"
                filepath.write_bytes(r2.content)
                return str(filepath)
        print(f"[multimodal] Pollinations 失败: status={response.status_code} size={len(response.content)}")
        return None
    except Exception as e:
        print(f"[multimodal] 图片异常: {e}")
        return None


def _generate_stability(prompt: str) -> str | None:
    """Stability AI API — 质量高但需付费 key。"""
    try:
        response = requests.post(
            "https://api.stability.ai/v2beta/stable-image/generate/core",
            headers={"authorization": f"Bearer {config.STABILITY_API_KEY}"},
            files={"none": ""},
            data={"prompt": prompt, "output_format": "png"},
            timeout=60,
        )
        if response.status_code == 200:
            filepath = config.IMAGE_DIR / f"img_{uuid.uuid4().hex[:8]}.png"
            filepath.write_bytes(response.content)
            return str(filepath)
        print(f"[multimodal] Stability 失败: {response.status_code}")
        return None
    except Exception as e:
        print(f"[multimodal] Stability 异常: {e}")
        return None


async def _tts_async(text: str, output_path: str) -> bool:
    """edge-tts 异步生成。"""
    try:
        communicate = edge_tts.Communicate(text, config.TTS_VOICE, rate=config.TTS_RATE, pitch=config.TTS_PITCH)
        await communicate.save(output_path)
        return True
    except Exception as e:
        print(f"[multimodal] edge-tts 失败: {e}")
        return False


def generate_voice(text: str) -> str | None:
    """生成申鹤语音。优先 RVC API（游戏CV），fallback 到 edge-tts。"""
    # 先试 RVC API（真正的游戏角色声线）
    try:
        from agent.rvc_api import generate_rvc_voice
        result = generate_rvc_voice(text)
        if result:
            return result
    except Exception as e:
        print(f"[multimodal] RVC API 不可用: {e}")

    # Fallback: 本地 edge-tts
    return _generate_edge_tts(text)


def _generate_edge_tts(text: str) -> str | None:
    """edge-tts 备用方案。"""
    # 去除动作描写括号，让语音更干净
    clean = re.sub(r'[（(].*?[）)]', '', text).strip()
    if not clean:
        return None

    config.AUDIO_DIR.mkdir(parents=True, exist_ok=True)
    output_path = str(config.AUDIO_DIR / f"shenhe_{uuid.uuid4().hex[:8]}.mp3")

    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            import concurrent.futures
            future = asyncio.run_coroutine_threadsafe(
                _tts_async(clean, output_path), loop
            )
            future.result(timeout=15)
        else:
            asyncio.run(_tts_async(clean, output_path))
    except RuntimeError:
        asyncio.run(_tts_async(clean, output_path))
    except Exception as e:
        print(f"[multimodal] TTS 异常: {e}")
        return None

    if Path(output_path).exists():
        return output_path
    return None
