#!/usr/bin/python3
import sys
import os
import time
import datetime
import logging
import argparse
from PIL import Image, ImageDraw, ImageFont

BASE_DIR = os.path.dirname(os.path.realpath(__file__))
LIBDIR = os.path.join(BASE_DIR, 'e-Paper/RaspberryPi_JetsonNano/python/lib')
PICDIR = os.path.join(BASE_DIR, 'e-Paper/RaspberryPi_JetsonNano/python/pic')
sys.path.append(LIBDIR)

from waveshare_epd import epd3in52

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

FONT_PATH = os.path.join(PICDIR, 'Font.ttc')

QUOTES = [
    "Taking life one day at a time.\nCurrently on chapter: Today.",
    "Rest mode activated.\nEven computers need sleep.",
    "Achievement unlocked:\nSurvived another day.",
    "Off-hours detected.\nProceeding to do nothing. Expertly.",
    "Time to recharge\nyour human batteries.",
    "Even the sun clocks out.\nJoin the club.",
    "Brain.exe has stopped.\nRestart scheduled: tomorrow.",
    "Off duty. Emergency contact:\nyour couch.",
    "Work: complete. Now doing nothing.\nProfessionally.",
    "Secret to productivity?\nKnowing when to stop.",
    "Life is short, to-do list long.\nTake the break.",
    "Currently in:\nNot My Problem mode.",
]


def fmt_duration(seconds):
    seconds = abs(int(seconds))
    h, m = divmod(seconds // 60, 60)
    if h > 0:
        return f"{h}h {m:02d}m"
    return f"{m}m"


def centered(draw, text, font, y, W):
    bb = draw.textbbox((0, 0), text, font=font)
    draw.text(((W - (bb[2] - bb[0])) // 2, y), text, font=font, fill=0)
    return bb[3] - bb[1]


def build_working_image(epd, now, fonts, start_time, end_time):
    # Landscape: W=360, H=240
    W, H = epd.height, epd.width
    image = Image.new('1', (W, H), 255)
    draw = ImageDraw.Draw(image)
    font_big, font_med, font_small = fonts
    margin = 10
    GAP = 12

    # --- Progress calculations ---
    start_dt = datetime.datetime.combine(now.date(), start_time)
    end_dt = datetime.datetime.combine(now.date(), end_time)
    total = (end_dt - start_dt).total_seconds()
    elapsed = (now - start_dt).total_seconds()
    remaining = total - elapsed
    progress = max(0.0, min(1.0, elapsed / total))

    y = GAP

    # --- Section 1: ELAPSED ---
    y += centered(draw, "ELAPSED", font_small, y, W) + 2
    y += centered(draw, fmt_duration(elapsed), font_big, y, W) + GAP

    # --- Divider ---
    draw.line([(margin, y), (W - margin, y)], fill=0, width=1)
    y += GAP + 1

    # --- Section 2: REMAINING ---
    y += centered(draw, "REMAINING", font_small, y, W) + 2
    y += centered(draw, fmt_duration(remaining), font_big, y, W) + GAP

    # --- Divider ---
    draw.line([(margin, y), (W - margin, y)], fill=0, width=1)
    y += GAP + 1

    # --- Progress bar with start/end labels inline ---
    start_str = start_time.strftime("%H:%M")
    end_str = end_time.strftime("%H:%M")

    s_bb = draw.textbbox((0, 0), start_str, font=font_med)
    s_w, s_h = s_bb[2] - s_bb[0], s_bb[3] - s_bb[1]
    e_bb = draw.textbbox((0, 0), end_str, font=font_med)
    e_w = e_bb[2] - e_bb[0]

    bar_h = 12
    bar_x1 = margin + s_w + 5
    bar_x2 = W - e_w - margin - 5
    bar_y1 = y + (s_h - bar_h) // 2
    bar_y2 = bar_y1 + bar_h

    draw.text((margin, y), start_str, font=font_med, fill=0)
    draw.text((W - e_w - margin, y), end_str, font=font_med, fill=0)

    fill_x = int(bar_x1 + progress * (bar_x2 - bar_x1))
    draw.rectangle([bar_x1, bar_y1, bar_x2, bar_y2], outline=0)
    if fill_x > bar_x1 + 1:
        draw.rectangle([bar_x1 + 1, bar_y1 + 1, fill_x, bar_y2 - 1], fill=0)

    y = max(bar_y2, y + s_h) + GAP

    # --- Footer: current time + date ---
    footer = f"{now.strftime('%H:%M')}   {now.strftime('%a %d %b %Y')}"
    centered(draw, footer, font_small, y, W)

    return image


def build_offhours_image(epd, now, fonts):
    W, H = epd.height, epd.width
    image = Image.new('1', (W, H), 255)
    draw = ImageDraw.Draw(image)
    font_big, font_med, font_small = fonts
    margin = 10

    y = 10
    y += centered(draw, now.strftime("%H:%M"), font_big, y, W) + 10

    draw.line([(margin, y), (W - margin, y)], fill=0, width=2)
    y += 14

    # Quote rotates every 10 minutes
    quote_idx = (now.hour * 6 + now.minute // 10) % len(QUOTES)
    for line in QUOTES[quote_idx].split('\n'):
        y += centered(draw, line, font_med, y, W) + 8

    return image


def parse_time(s):
    try:
        return datetime.datetime.strptime(s, "%H%M").time()
    except ValueError:
        raise argparse.ArgumentTypeError(f"Invalid time '{s}' — use HHMM format, e.g. 0930")


def main():
    parser = argparse.ArgumentParser(description="Waveshare 3.52\" e-paper time display")
    parser.add_argument("--start", default="0930", type=parse_time,
                        metavar="HHMM", help="Work start time (default: 0930)")
    parser.add_argument("--end", default="1830", type=parse_time,
                        metavar="HHMM", help="Work end time (default: 1830)")
    args = parser.parse_args()

    start_time = args.start
    end_time = args.end
    logger.info("Work window: %s – %s", start_time.strftime("%H:%M"), end_time.strftime("%H:%M"))

    epd = epd3in52.EPD()
    logger.info("Initializing display")
    epd.init()
    epd.Clear()
    # Match display mode used in Waveshare example for clean text rendering
    epd.send_command(0x50)
    epd.send_data(0x17)

    font_big = ImageFont.truetype(FONT_PATH, 56)   # elapsed / remaining
    font_med = ImageFont.truetype(FONT_PATH, 20)   # start / end times, quote
    font_small = ImageFont.truetype(FONT_PATH, 17) # labels, current time, date
    fonts = (font_big, font_med, font_small)

    try:
        while True:
            now = datetime.datetime.now()
            in_hours = start_time <= now.time() <= end_time

            if in_hours:
                image = build_working_image(epd, now, fonts, start_time, end_time)
            else:
                image = build_offhours_image(epd, now, fonts)

            epd.display(epd.getbuffer(image))
            epd.lut_GC()
            epd.refresh()

            mode = "work" if in_hours else "off"
            logger.info("Updated (%s hours) — next update in ~%ds",
                        mode, 60 - now.second)

            # Sleep until the next minute boundary
            now = datetime.datetime.now()
            sleep_secs = 60 - now.second - now.microsecond / 1e6
            time.sleep(max(1.0, sleep_secs))

    except KeyboardInterrupt:
        logger.info("Stopping — clearing display")
        epd.Clear()
        epd.sleep()
        epd3in52.epdconfig.module_exit(cleanup=True)


if __name__ == '__main__':
    main()
