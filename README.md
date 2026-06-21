# epaper-workday

A focused workday timer for the [Waveshare 3.52" e-Paper HAT](https://www.waveshare.com/3.52inch-e-paper-hat.htm) on a Raspberry Pi.

## What it shows

**During work hours** — the screen is dominated by two numbers: how long you've been at it and how long until you're done.

```
         ELAPSED
         4h 53m
  ──────────────────────────────
         REMAINING
         4h 07m
  ──────────────────────────────
  09:30  [========|======]  18:30
          14:23   Sat 21 Jun
```

**Outside work hours** — current time and a rotating funny quote.

## Hardware

- Raspberry Pi (any model with 40-pin GPIO)
- Waveshare 3.52" e-Paper HAT (black/white, 240×360 px)

## Setup

### 1. Waveshare vendor library

Clone or unzip the [Waveshare e-Paper library](https://github.com/waveshare/e-Paper) and note the path to:

```
e-Paper/RaspberryPi_JetsonNano/python/lib/
e-Paper/RaspberryPi_JetsonNano/python/pic/
```

The script expects those paths relative to `~/waveshare-e-paper-352/e-Paper/` by default.
Update `LIBDIR` / `PICDIR` at the top of `src/time_display.py` if your layout differs.

Enable SPI on the Pi:

```bash
sudo raspi-config   # Interface Options → SPI → Enable
```

### 2. Python dependencies

```bash
pip install pillow RPi.GPIO spidev
```

## Usage

```bash
# Default work window: 09:30 – 18:30
sudo python3 src/time_display.py

# Custom hours
sudo python3 src/time_display.py --start 0800 --end 1700
```

Stop with `Ctrl+C` — the display is cleared and put to sleep cleanly.

### Options

| Flag | Default | Description |
|------|---------|-------------|
| `--start HHMM` | `0930` | Work start time |
| `--end HHMM` | `1830` | Work end time |

The display refreshes once per minute at the minute boundary.
