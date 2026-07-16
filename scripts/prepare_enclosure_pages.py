#!/usr/bin/env python3

from pathlib import Path
import argparse
import cv2
import numpy as np


def find_spine_x(image):
    h, w = image.shape[:2]
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # Search around the middle only
    x1 = int(w * 0.35)
    x2 = int(w * 0.65)
    y1 = int(h * 0.05)
    y2 = int(h * 0.95)

    roi = gray[y1:y2, x1:x2]

    # Dark vertical features score highly
    darkness = 255 - roi
    column_scores = darkness.mean(axis=0)

    # Smooth to avoid picking individual letters
    kernel = np.ones(35) / 35
    smooth = np.convolve(column_scores, kernel, mode="same")

    spine_local_x = int(np.argmax(smooth))
    return x1 + spine_local_x


def enhance_for_ocr(image):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    clahe = cv2.createCLAHE(
        clipLimit=2.0,
        tileGridSize=(8, 8),
    )

    enhanced = clahe.apply(gray)
    return enhanced


def process_image(src, outdir):
    image = cv2.imread(str(src))
    if image is None:
        print(f"FAILED read: {src}")
        return

    h, w = image.shape[:2]
    spine_x = find_spine_x(image)

    page_no = int(src.stem[-4:])

    # Odd photos are right-hand pages, even photos are left-hand pages.
    # Crop from the spine outwards.
    if page_no % 2 == 0:
        side = "left"
        x1 = int(w * 0.03)
        x2 = spine_x - int(w * 0.015)
    else:
        side = "right"
        x1 = spine_x + int(w * 0.015)
        x2 = int(w * 0.97)

    y1 = int(h * 0.035)
    y2 = int(h * 0.97)

    crop = image[y1:y2, x1:x2]

    # If a crop went wrong, fall back to original image.
    if crop.size == 0 or crop.shape[1] < w * 0.2:
        crop = image
        side = "fallback"

    if crop.shape[1] > crop.shape[0]:
        crop = cv2.rotate(crop, cv2.ROTATE_90_CLOCKWISE)

    ocr = enhance_for_ocr(crop)

    crop_file = outdir / "crop" / f"{src.stem}.png"
    ocr_file = outdir / "ocr" / f"{src.stem}.png"

    cv2.imwrite(str(crop_file), crop)
    cv2.imwrite(str(ocr_file), ocr)

    print(f"{src.name}: spine={spine_x}, side={side}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("input_dir")
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    input_dir = Path(args.input_dir)
    outdir = Path(args.out)

    (outdir / "crop").mkdir(parents=True, exist_ok=True)
    (outdir / "ocr").mkdir(parents=True, exist_ok=True)

    images = sorted(input_dir.glob("*.jpg"))

    print(f"Processing {len(images)} pages")

    for image in images:
        process_image(image, outdir)


if __name__ == "__main__":
    main()
