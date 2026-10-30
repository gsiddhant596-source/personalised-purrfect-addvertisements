import torch
from diffusers import AutoPipelineForText2Image
from pathlib import Path
import uuid

# Setup static directory to save generated ads
STATIC_DIR = Path(__file__).parent / "static" / "ads"
STATIC_DIR.mkdir(parents=True, exist_ok=True)

# Select GPU device
device = "cuda" if torch.cuda.is_available() else "cpu"
torch_dtype = torch.float16 if device == "cuda" else torch.float32

print(f"[Stable Diffusion] Loading SD-Turbo on {device} (VRAM-optimized for 6GB)...")

pipe = AutoPipelineForText2Image.from_pretrained(
    "stabilityai/sd-turbo",
    torch_dtype=torch_dtype,
    variant="fp16" if device == "cuda" else None
)
pipe.to(device)

if device == "cuda":
    pipe.enable_attention_slicing()

print("[Stable Diffusion] Model ready for real-time generation.")


def generate_local_sd_banner(product_name: str, category: str, description: str, context: str = "") -> str:
    """
    Synthesizes a commercial ad creative using both product specifications 
    and the user's active browsing context on an RTX 4050 GPU.
    """
    context_str = f"lifestyle setting related to {context}, " if context else ""
    
    prompt = (
        f"commercial product photography for {product_name}, {category}, {description}, "
        f"{context_str}award-winning product advertising visual, studio lighting, "
        f"clean modern aesthetic, photorealistic, 8k, sharp focus, no watermarks"
    )

    # 1-step distilled inference (~0.4s on RTX 4050)
    image = pipe(
        prompt=prompt,
        num_inference_steps=1,
        guidance_scale=0.0,
        width=512,
        height=320
    ).images[0]

    filename = f"ad_{uuid.uuid4().hex[:8]}.png"
    filepath = STATIC_DIR / filename
    image.save(filepath)

    return f"http://127.0.0.1:8000/static/ads/{filename}"