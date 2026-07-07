# Based on https://github.com/kennethreitz-archive/clint/blob/master/clint/textui/progress.py
from __future__ import absolute_import

import sys
import time
import os

# Enable ANSI colors on Windows
os.system("")

STREAM = sys.stderr

CYAN = "\033[36m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
DIM = "\033[2m"
RESET = "\033[0m"
BOLD = "\033[1m"

BAR_TEMPLATE_META = f"{CYAN}%4s{RESET} | {YELLOW}%5s{RESET} | {DIM}%-15s{RESET} [{GREEN}%s{RESET}%s] {BOLD}%s{RESET}\033[K\r"
BAR_TEMPLATE_NO_META = f"{CYAN}%4s{RESET} | {YELLOW}%5s{RESET} [{GREEN}%s{RESET}%s] {BOLD}%s{RESET}\033[K\r"
MILL_TEMPLATE = "%s %s %i/%i\r"

DOTS_CHAR = "A"
BAR_FILLED_CHAR = "█"
BAR_EMPTY_CHAR = "░"

# How long to wait before recalculating the ETA
ETA_INTERVAL = 0.2
# How many intervals (excluding the current one) to calculate the simple moving
# average
ETA_SMA_WINDOW = 9

# How long to wait before shifting the indeterminate bar
INDETERMINATE_INTERVAL = 0.05

# How long to wait before shifting the scrolling label
LABEL_INTERVAL = 0.1


class Bar:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            self.abort()
        else:
            self.done()
        return False  # we're not suppressing exceptions

    def abort(self):
        if not self.hide:
            STREAM.write("\r\033[K")
            STREAM.flush()

    def __init__(
        self,
        label="",
        width=32,
        hide=None,
        empty_char=BAR_EMPTY_CHAR,
        filled_char=BAR_FILLED_CHAR,
        expected_size=None,
        indeterminate=False,
        every=1,
    ):
        self.fulllabel = label
        self.shortlabel = label
        if len(label) > 15:
            self.scrolling_label = True
            if "." in self.shortlabel:
                ext = self.shortlabel[self.shortlabel.rfind(".") :]
                if "/" in self.shortlabel.replace("\\", "/"):
                    self.shortlabel = self.shortlabel[
                        self.shortlabel.replace("\\", "/").rfind("/") + 1 :
                    ]
                if len(self.shortlabel) > 15:
                    self.shortlabel = self.shortlabel[: 15 - len(ext) - 2] + f"..{ext}"
            else:
                self.shortlabel = self.shortlabel[:12] + "..."
            self.fulllabel = self.fulllabel + " " * 6
        else:
            self.scrolling_label = False
        self.labeloffset = 0
        self.labeldelta = time.time()
        self.width = width
        self.hide = hide
        # Only show bar in terminals by default (better for piping, logging etc.)
        if hide is None:
            try:
                self.hide = not STREAM.isatty()
            except AttributeError:  # output does not support isatty()
                self.hide = True
        self.elapsed = 0
        self.empty_char = empty_char
        self.filled_char = filled_char
        self.expected_size = expected_size
        self.indeterminate = indeterminate
        self.every = every
        self.start = time.time()
        self.ittimes = []
        self.eta = 0
        self.etadelta = time.time()
        self.etadisp = self.format_time(self.eta)
        self.speeddisp = "0 B/s"
        self.sizedisp = ""
        self.last_progress = 0
        self._done = 0
        self.last_draw_time = 0
        if self.indeterminate:
            self.indeterminatwidth = int(self.width / 2)
            self.indeterminateoffset = 0
            self.indeterminatedelta = time.time()
        if self.expected_size or self.indeterminate:
            self.show(0)

    def show(self, progress, count=None):
        if count is not None:
            self.expected_size = count
        if self.expected_size is None and self.indeterminate is False:
            raise Exception("expected_size not initialized")
        self.last_progress = progress
        if self.scrolling_label:
            if (time.time() - self.labeldelta) > LABEL_INTERVAL:
                self.labeldelta = time.time()
                self.labeloffset += 1
            if self.labeloffset == len(self.fulllabel):
                self.labeloffset = 0
            labeldisp = self.fulllabel[self.labeloffset : 15 + self.labeloffset]
            if 15 + self.labeloffset > len(self.fulllabel):
                labeldisp += self.fulllabel[
                    : (15 + self.labeloffset) - len(self.fulllabel)
                ]
        else:
            labeldisp = self.shortlabel
        if self.indeterminate:
            if (time.time() - self.indeterminatedelta) > INDETERMINATE_INTERVAL:
                self.indeterminatedelta = time.time()
                self.indeterminateoffset += 1
                if self.indeterminateoffset == self.width:
                    self.indeterminateoffset = 0
            if not self.hide:
                now = time.time()
                if (now - self.last_draw_time) > 0.016:
                    self.last_draw_time = now
                    percent = "N/A%"
                    etadisp = "??:??"
                    bardisp = self.empty_char * self.width
                    offset = self.indeterminateoffset
                    todraw = self.indeterminatwidth
                    bardisp = (
                        bardisp[:offset]
                        + self.filled_char * min(todraw, self.width - offset)
                        + bardisp[offset + todraw :]
                    )
                    todraw = max(0, todraw - (self.width - offset))
                    bardisp = self.filled_char * todraw + bardisp[todraw:]
                    STREAM.write(
                        BAR_TEMPLATE_NO_META
                        % (
                            percent,
                            etadisp,
                            bardisp,
                            "",
                            labeldisp,
                        )
                    )
                    STREAM.flush()
                return
        if (time.time() - self.etadelta) > ETA_INTERVAL:
            self.etadelta = time.time()
            self.ittimes = self.ittimes[-ETA_SMA_WINDOW:] + [
                -(self.start - time.time()) / (progress + 1)
            ]
            avg_time_per_byte = sum(self.ittimes) / float(len(self.ittimes))
            self.eta = avg_time_per_byte * (self.expected_size - progress)
            self.etadisp = self.format_time(self.eta)

            if avg_time_per_byte > 0:
                speed_bps = 1.0 / avg_time_per_byte
                self.speeddisp = f"{self.format_size(speed_bps)}/s"

            prog_size = self.format_size(progress)
            tot_size = self.format_size(self.expected_size)
            self.sizedisp = f"{prog_size} / {tot_size}"
        if not self.hide and (
            (progress % self.every) == 0
            or (  # True every "every" updates
                progress == self.expected_size  # And when we're done
            )
        ):
            now = time.time()
            if (now - self.last_draw_time) > 0.016 or progress == self.expected_size:
                self.last_draw_time = now
                percent = f"{int(progress/self.expected_size*100)}%"
                x = int(self.width * progress / self.expected_size)

                # --- qBittorrent Scattered Download Effect ---
                import random
                seed = sum(ord(c) for c in self.shortlabel)
                rng = random.Random(seed)
                indices = list(range(self.width))
                rng.shuffle(indices)

                filled_indices = set(indices[:x])

                bar_chars = []
                for i in range(self.width):
                    if i in filled_indices:
                        bar_chars.append(self.filled_char)
                    else:
                        bar_chars.append(self.empty_char)
                bardisp = "".join(bar_chars)

                if self.sizedisp:
                    STREAM.write(
                        BAR_TEMPLATE_META
                        % (
                            percent,
                            self.etadisp,
                            f"{self.speeddisp} • {self.sizedisp}",
                            bardisp,
                            "",
                            labeldisp,
                        )
                    )
                else:
                    STREAM.write(
                        BAR_TEMPLATE_NO_META
                        % (
                            percent,
                            self.etadisp,
                            bardisp,
                            "",
                            labeldisp,
                        )
                    )
                STREAM.flush()
            return

    def done(self):
        self.elapsed = time.time() - self.start
        elapsed_disp = self.format_time(self.elapsed)
        if not self.hide:
            # Print completed bar with elapsed time
            percent = "100%"
            if self.sizedisp:
                STREAM.write(
                    BAR_TEMPLATE_META.replace("\r", "\n")
                    % (
                        percent,
                        elapsed_disp,
                        f"Completed • {self.sizedisp}",
                        self.filled_char * self.width,
                        self.empty_char * (self.width - self.width),
                        self.shortlabel,
                    )
                )
            else:
                STREAM.write(
                    BAR_TEMPLATE_NO_META.replace("\r", "\n")
                    % (
                        percent,
                        elapsed_disp,
                        self.filled_char * self.width,
                        self.empty_char * (self.width - self.width),
                        self.shortlabel,
                    )
                )
            STREAM.flush()

    def format_time(self, seconds):
        if seconds < 0:
            seconds = 0
        return time.strftime("%M:%S", time.gmtime(seconds))

    def format_size(self, size):
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} PB"


def bar(
    it,
    label="",
    width=32,
    hide=None,
    empty_char=BAR_EMPTY_CHAR,
    filled_char=BAR_FILLED_CHAR,
    expected_size=None,
    every=1,
):
    """Progress iterator. Wrap your iterables with it."""

    count = len(it) if expected_size is None else expected_size

    with Bar(
        label=label,
        width=width,
        hide=hide,
        empty_char=empty_char,
        filled_char=filled_char,
        expected_size=count,
        every=every,
    ) as bar:
        for i, item in enumerate(it):
            yield item
            bar.show(i + 1)
