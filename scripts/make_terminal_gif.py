"""Renders assets/terminal.gif: a terminal window that types out who I am (ML focus + projects).

Edit SCRIPT below and re-run: python scripts/make_terminal_gif.py
"""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
W, H = 860, 440
BG, BAR, FG, DIM = (13, 17, 23), (33, 38, 45), (201, 209, 217), (110, 118, 129)
PROMPT, CMD = (126, 231, 135), (255, 255, 255)
ACCENT, GREEN, ORANGE, PURPLE = (165, 214, 255), (63, 185, 80), (255, 166, 87), (210, 168, 255)


def load_font(size):
    for f in ("C:/Windows/Fonts/consola.ttf", "DejaVuSansMono.ttf"):
        try:
            return ImageFont.truetype(f, size)
        except OSError:
            pass
    return ImageFont.load_default()


FONT = load_font(17)

# (command, [output lines]); an output line is a string or a list of (text, colour) segments
SCRIPT = [
    ("whoami", [[("Suzain Sayyad", ACCENT), ("  |  ", DIM), ("AI/ML Engineer", ORANGE), (" · NLP & Transformers", ACCENT)]]),
    ("cat focus.txt", [
        "> NLP & text classification with Transformers (DistilRoBERTa)",
        "> Classical ML: XGBoost, CatBoost, scikit-learn pipelines",
        "> Recommender systems, explainable AI, Streamlit deployment",
    ]),
    ("ls ~/ml-projects", [
        [("TextTrace/        ", GREEN), ("AI-text detector       ", FG), ("F1 0.952", ORANGE)],
        [("CarPricePredict/  ", GREEN), ("CatBoost regression    ", FG), ("R2 0.907", ORANGE)],
        [("ProfileMatcher/   ", GREEN), ("hybrid NLP recommender ", FG), ("TF-IDF + MBTI", ORANGE)],
        [("NLP-ProfileRec/   ", GREEN), ("similar-profile search ", FG), ("NLP", ORANGE)],
    ]),
    ("echo $MOTTO", [[("Train. Evaluate. Explain. Ship.", PURPLE)]]),
]

LINE_H, PAD_X, TOP = 26, 22, 56


def frame(lines, cursor=True):
    im = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 0, W - 1, H - 1], 12, fill=BG, outline=BAR)
    d.rounded_rectangle([0, 0, W - 1, 36], 12, fill=BAR)
    d.rectangle([0, 24, W - 1, 36], fill=BAR)
    for i, c in enumerate([(255, 95, 86), (255, 189, 46), (39, 201, 63)]):
        d.ellipse([16 + i * 22, 12, 28 + i * 22, 24], fill=c)
    d.text((W // 2, 18), "suzain@sayyad: ~", font=FONT, fill=DIM, anchor="mm")
    y, last_end = TOP, (PAD_X, TOP)
    for kind, segs in lines:
        x = PAD_X
        if kind == "cmd":
            d.text((x, y), "~ $ ", font=FONT, fill=PROMPT)
            x += d.textlength("~ $ ", font=FONT)
            d.text((x, y), segs, font=FONT, fill=CMD)
            last_end = (x + d.textlength(segs, font=FONT), y)
        else:
            for text, colour in segs:
                d.text((x, y), text, font=FONT, fill=colour)
                x += d.textlength(text, font=FONT)
        y += LINE_H
    if cursor:
        cx, cy = last_end
        d.rectangle([cx + 2, cy + 2, cx + 11, cy + 20], fill=FG)
    return im


def main():
    frames, durations, shown = [], [], []
    for cmd, outs in SCRIPT:
        for i in range(len(cmd) + 1):
            frames.append(frame(shown + [("cmd", cmd[:i])]))
            durations.append(70 if i else 400)
        shown.append(("cmd", cmd))
        for o in outs:
            shown.append(("out", [(o, FG)] if isinstance(o, str) else o))
            frames.append(frame(shown + [("cmd", "")]))
            durations.append(160)
        durations[-1] = 1000
    for on in [False, True, False, True, False, True]:
        frames.append(frame(shown + [("cmd", "")], cursor=on))
        durations.append(450)
    durations[-1] = 3000
    pal = [f.convert("P", palette=Image.ADAPTIVE, colors=64) for f in frames]
    out = ROOT / "assets" / "terminal.gif"
    pal[0].save(out, save_all=True, append_images=pal[1:], duration=durations, loop=0, optimize=True, disposal=1)
    print(out, f"{out.stat().st_size // 1024} KB, {len(frames)} frames, {sum(durations) / 1000:.1f}s")


if __name__ == "__main__":
    main()
