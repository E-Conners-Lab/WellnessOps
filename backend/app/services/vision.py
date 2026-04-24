"""
Vision analysis service.
Sends photos to Ollama's multimodal model (llama3.2-vision)
and gets text descriptions for use in observations and scoring.
"""

import base64

import httpx
import structlog

from app.core.config import settings

logger = structlog.stdlib.get_logger()


async def analyze_image(image_bytes: bytes, prompt: str | None = None) -> str:
    """Send an image to the vision model and get a text description.

    Args:
        image_bytes: Raw image bytes (JPEG, PNG).
        prompt: Optional prompt to guide the analysis. Defaults to a wellness audit prompt.

    Returns:
        Text description of what the model sees.
    """
    if prompt is None:
        prompt = (
            "You are assisting a wellness home auditor. Describe what you see in this photo "
            "from a home wellness audit perspective. Focus on: organization, cleanliness, "
            "natural light, plants, ergonomics, sensory elements, hidden clutter, food systems, "
            "sleep environment quality, and any wellness-relevant observations. "
            "Be specific and observational, not judgmental. 2-4 sentences."
        )

    image_b64 = base64.b64encode(image_bytes).decode("ascii")

    model = getattr(settings, "ollama_vision_model", "llama3.2")

    url = f"{settings.ollama_base_url}/api/chat"
    payload = {
        "model": model,
        "messages": [
            {
                "role": "user",
                "content": prompt,
                "images": [image_b64],
            }
        ],
        "stream": False,
        "options": {
            "num_predict": 300,
        },
    }

    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(url, json=payload)
        response.raise_for_status()
        data = response.json()

    description = data["message"]["content"].strip()

    logger.info(
        "vision_analysis_complete",
        model=model,
        description_length=len(description),
        eval_count=data.get("eval_count"),
    )

    return description
