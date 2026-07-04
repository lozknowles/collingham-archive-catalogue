import argparse, json, subprocess, time
from pathlib import Path

import torch
from PIL import Image
from transformers import AutoProcessor, Qwen2_5_VLForConditionalGeneration

MODEL_PATH = "/fast/models/huggingface/olmOCR-2-7B-1025"

def run(cmd):
    subprocess.run(cmd, check=True)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("pdf")
    ap.add_argument("--dpi", type=int, default=90)
    ap.add_argument("--max-new-tokens", type=int, default=512)
    ap.add_argument("--outdir", default="/fast/olmocr-poc/output")
    args = ap.parse_args()

    pdf = Path(args.pdf).resolve()
    outdir = Path(args.outdir) / pdf.stem
    pages = outdir / "pages"
    offload = outdir / "offload"
    pages.mkdir(parents=True, exist_ok=True)
    offload.mkdir(parents=True, exist_ok=True)

    run(["pdftoppm", "-png", "-r", str(args.dpi), str(pdf), str(pages / "page")])
    image_paths = sorted(pages.glob("page-*.png"))

    processor = AutoProcessor.from_pretrained(MODEL_PATH, use_fast=False)

    model = Qwen2_5_VLForConditionalGeneration.from_pretrained(
        MODEL_PATH,
        dtype=torch.float32,
        device_map="auto",
        max_memory={0: "14GiB", "cpu": "48GiB"},
        offload_folder=str(offload),
        attn_implementation="eager",
        low_cpu_mem_usage=True,
    )

    all_results = []

    for i, image_path in enumerate(image_paths, 1):
        prompt = (
            "Transcribe this archive catalogue card page. Preserve printed field labels "
            "and handwritten entries. Use plain text. Do not invent missing text."
        )

        messages = [{
            "role": "user",
            "content": [
                {"type": "image", "image": str(image_path)},
                {"type": "text", "text": prompt},
            ],
        }]

        text = processor.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
        image = Image.open(image_path).convert("RGB")
        inputs = processor(text=[text], images=[image], return_tensors="pt").to(model.device)

        start = time.time()
        with torch.inference_mode():
            output = model.generate(
                **inputs,
                max_new_tokens=args.max_new_tokens,
                do_sample=False,
                temperature=None,
                top_p=None,
            )

        decoded = processor.batch_decode(output, skip_special_tokens=True)[0]
        transcription = decoded.split("assistant\n")[-1].strip()
        elapsed = round(time.time() - start, 2)

        print(f"\n--- PAGE {i} / {len(image_paths)} ({elapsed}s) ---\n")
        print(transcription)

        all_results.append({
            "page": i,
            "image": str(image_path),
            "seconds": elapsed,
            "transcription": transcription,
        })

    md = outdir / f"{pdf.stem}.md"
    js = outdir / f"{pdf.stem}.json"

    md.write_text("\n\n".join(
        f"# Page {r['page']}\n\n{r['transcription']}\n\n_Time: {r['seconds']}s_"
        for r in all_results
    ))

    js.write_text(json.dumps({
        "pdf": str(pdf),
        "dpi": args.dpi,
        "max_new_tokens": args.max_new_tokens,
        "pages": all_results,
    }, indent=2))

    print(f"\nSaved:\n{md}\n{js}")

if __name__ == "__main__":
    main()
