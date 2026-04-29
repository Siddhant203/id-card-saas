import fitz
from PIL import Image, ImageChops
from docx import Document
from docx.shared import Inches
from docx.enum.table import WD_TABLE_ALIGNMENT
import os
import cv2
import numpy as np
import time

# PDF → Images
def pdf_to_images(pdf_path):
    doc = fitz.open(pdf_path)
    images = []

    for page in doc:
        pix = page.get_pixmap()
        img_path = f"{pdf_path}_{page.number}.png"
        pix.save(img_path)
        images.append(img_path)

    return images


# White space हटाना
def crop_id_card(image_path):
    import cv2
    import os
    from PIL import Image, ImageChops

    image = cv2.imread(image_path)

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    blur = cv2.GaussianBlur(gray, (5, 5), 0)

    thresh = cv2.threshold(
        blur,
        240,
        255,
        cv2.THRESH_BINARY_INV
    )[1]

    contours, _ = cv2.findContours(
        thresh,
        cv2.RETR_EXTERNAL,
        cv2.CHAIN_APPROX_SIMPLE
    )

    boxes = []

    for cnt in contours:

        x, y, w, h = cv2.boundingRect(cnt)

        # Ignore tiny noise
        if w > 300 and h > 150:
            boxes.append((x, y, w, h))

    # Sort top-to-bottom, left-to-right
    boxes = sorted(boxes, key=lambda b: (b[1], b[0]))

    cropped_paths = []

    # ✅ If multiple blocks detected
    if len(boxes) >= 2:

        count = 0

        for (x, y, w, h) in boxes:

            crop = image[y:y+h, x:x+w]

            crop_path = f"crop_{count}_{os.path.basename(image_path)}"

            cv2.imwrite(crop_path, crop)

            cropped_paths.append(crop_path)

            count += 1

    else:
        # ✅ fallback → full page trim

        pil_img = Image.open(image_path).convert("RGB")

        bg = Image.new(pil_img.mode, pil_img.size, (255, 255, 255))

        diff = ImageChops.difference(pil_img, bg)

        bbox = diff.getbbox()

        if bbox:
            cropped = pil_img.crop(bbox)
        else:
            cropped = pil_img

        crop_path = "full_" + os.path.basename(image_path)

        cropped.save(crop_path)

        cropped_paths.append(crop_path)

    return cropped_paths

# Word बनाना (PVC size)
def create_word(images, output_path):
    doc = Document()

    section = doc.sections[0]
    section.top_margin = Inches(0.3)
    section.bottom_margin = Inches(0.3)
    section.left_margin = Inches(0.3)
    section.right_margin = Inches(0.3)

    rows = 4
    cols = 2
    index = 0

    while index < len(images):
        table = doc.add_table(rows=rows, cols=cols)
        table.alignment = WD_TABLE_ALIGNMENT.CENTER

        for r in range(rows):
            for c in range(cols):
                if index >= len(images):
                    break

                cell = table.cell(r, c)
                paragraph = cell.paragraphs[0]
                run = paragraph.add_run()

                run.add_picture(
                    images[index],
                    width=Inches(3.37),
                    height=Inches(2.125)
                )

                index += 1

        doc.add_page_break()

    doc.save(output_path)


# 🔥 MAIN FUNCTION 
def process_pdfs(pdf_paths, output_file):
    cropped_images = []

    temp_files = []

    for pdf in pdf_paths:

        images = pdf_to_images(pdf)

        temp_files.extend(images)

        for img in images:

            crops = crop_id_card(img)

            cropped_images.extend(crops)

            temp_files.extend(crops)

    create_word(cropped_images, output_file)

    # थोड़ा wait
    time.sleep(1)

    # Cleanup
    for file in temp_files:

        try:
            if os.path.exists(file):
                os.remove(file)
        except Exception as e:
            print("Delete failed:", file, e)

    return output_file