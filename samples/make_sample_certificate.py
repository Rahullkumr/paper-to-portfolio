"""Render a fictional specimen share certificate for demos and tests.

Every name, number and company on it is made up.
Usage: python samples/make_sample_certificate.py
"""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

OUT = Path(__file__).with_name("sample_certificate.png")
W, H = 1400, 900
INK = (40, 32, 24)
PAPER = (242, 232, 208)
BORDER = (120, 70, 30)


def font(size, bold=False):
    names = ["georgiab.ttf", "timesbd.ttf"] if bold else ["georgia.ttf", "times.ttf"]
    for name in names:
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    return ImageFont.load_default(size)


def centered(draw, y, text, f):
    w = draw.textlength(text, font=f)
    draw.text(((W - w) / 2, y), text, font=f, fill=INK)


def main():
    img = Image.new("RGB", (W, H), PAPER)
    d = ImageDraw.Draw(img)
    d.rectangle([20, 20, W - 20, H - 20], outline=BORDER, width=8)
    d.rectangle([40, 40, W - 40, H - 40], outline=BORDER, width=2)

    centered(d, 70, "SAHYADRI SPINNING MILLS LIMITED", font(52, bold=True))
    centered(d, 135, "Registered Office: Hadapsar Industrial Estate, Pune 411013", font(24))
    centered(d, 175, "(Incorporated under the Companies Act, 1956)", font(22))
    centered(d, 230, "SHARE CERTIFICATE", font(44, bold=True))

    body = font(28)
    d.text((110, 320), "Certificate No.: 004417", font=body, fill=INK)
    d.text((820, 320), "Folio No.: S-01923", font=body, fill=INK)
    d.text((110, 370), "Distinctive Nos.: 0441601 to 0441700", font=body, fill=INK)

    lines = [
        "This is to certify that  RAMESH KASHINATH JOSHI",
        "is the Registered Holder of  100 (One Hundred)  Equity Shares",
        "of Rs. 10/- each, fully paid up, in the above-named Company,",
        "subject to the Memorandum and Articles of Association.",
    ]
    for i, line in enumerate(lines):
        d.text((110, 450 + i * 48), line, font=body, fill=INK)

    d.text((110, 690), "Given under the Common Seal of the Company", font=font(24), fill=INK)
    d.text((110, 725), "on this 14th day of March, 1989.", font=font(24), fill=INK)
    d.text((900, 760), "Director          Secretary", font=font(24), fill=INK)
    d.ellipse([560, 640, 760, 840], outline=BORDER, width=4)
    centered(d, 725, "SEAL", font(30, bold=True))

    stamp = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    sd = ImageDraw.Draw(stamp)
    sf = font(64, bold=True)
    text = "SPECIMEN - FICTIONAL SAMPLE"
    sd.text(((W - sd.textlength(text, font=sf)) / 2, 395), text, font=sf, fill=(200, 30, 30, 70))
    img = Image.alpha_composite(img.convert("RGBA"), stamp).convert("RGB")

    img.save(OUT)
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
