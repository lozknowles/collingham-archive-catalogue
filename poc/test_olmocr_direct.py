import torch
from PIL import Image
from transformers import AutoProcessor, Qwen2_5_VLForConditionalGeneration

model_path = "/fast/models/huggingface/olmOCR-2-7B-1025"
image_path = "/fast/olmocr-poc/card-pages-small/page-1.png"

processor = AutoProcessor.from_pretrained(model_path)

model = Qwen2_5_VLForConditionalGeneration.from_pretrained(
    model_path,
    dtype=torch.float32,
    device_map="auto",
    max_memory={0: "14GiB", "cpu": "48GiB"},
    offload_folder="/fast/olmocr-poc/offload",
    attn_implementation="eager",
    low_cpu_mem_usage=True,
)

messages = [{
    "role": "user",
    "content": [
        {"type": "image", "image": image_path},
        {"type": "text", "text": "Transcribe this archive catalogue card. Preserve field labels and handwriting. Return concise plain text."},
    ],
}]

text = processor.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
inputs = processor(text=[text], images=[Image.open(image_path)], return_tensors="pt").to(model.device)

with torch.inference_mode():
    out = model.generate(**inputs, max_new_tokens=128, do_sample=False, temperature=None, top_p=None)

print(processor.batch_decode(out, skip_special_tokens=True)[0])
