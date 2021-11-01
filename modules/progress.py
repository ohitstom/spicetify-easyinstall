# Based on https://github.com/kennethreitz-archive/clint/blob/master/clint/textui/progress.py
from __future__ import absolute_import

import sys
import time

STREAM = sys.stderr

BAR_TEMPLATE = "%-4s - %s [%s%s] %-24s\r"
MILL_TEMPLATE = "%s %s %i/%i\r"

DOTS_CHAR = "."
BAR_FILLED_CHAR = "#"
BAR_EMPTY_CHAR = " "

# How long to wait before recalculating the ETA
ETA_INTERVAL = 1
# How many intervals (excluding the current one) to calculate the simple moving
# average
ETA_SMA_WINDOW = 9

# How long to wait before shifting the indeterminate bar
INDETERMINATE_INTERVAL = 0.5

# How long to wait before shifting the scrolling label
LABEL_INTERVAL = 0.25


class Bar(object):
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.done()
        return False  # we're not suppressing exceptions

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
        if len(label) > 24:
            self.scrolling_label = True
            if "." in self.shortlabel:
                ext = self.shortlabel[self.shortlabel.rfind(".") :]
                if "/" in self.shortlabel.replace("\\", "/"):
                    self.shortlabel = self.shortlabel[self.shortlabel.replace("\\", "/").rfind("/")+1:]
                if len(self.shortlabel) > 24:
                    self.shortlabel = self.shortlabel[: 24 - len(ext) - 2] + ".." + ext
            else:
                self.shortlabel = self.shortlabel[:21] + "..."
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
        self.last_progress = 0
        if self.expected_size:
            self.show(0)
        elif self.indeterminate:
            self.indeterminatwidth = int(self.width / 2)
            self.indeterminateoffset = 0
            self.indeterminatedelta = time.time()
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
            labeldisp = self.fulllabel[self.labeloffset:24+self.labeloffset]
            if 24+self.labeloffset > len(self.fulllabel):
                labeldisp += self.fulllabel[:(24+self.labeloffset)-len(self.fulllabel)]
        else:
            labeldisp = self.shortlabel
        if self.indeterminate:
            if (time.time() - self.indeterminatedelta) > INDETERMINATE_INTERVAL:
                self.indeterminatedelta = time.time()
                self.indeterminateoffset += 1
                if self.indeterminateoffset == self.width:
                    self.indeterminateoffset = 0
            if not self.hide:
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
                    BAR_TEMPLATE
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
            self.eta = (
                sum(self.ittimes)
                / float(len(self.ittimes))
                * (self.expected_size - progress)
            )
            self.etadisp = self.format_time(self.eta)
        x = int(self.width * progress / self.expected_size)
        if not self.hide:
            if (progress % self.every) == 0 or (  # True every "every" updates
                progress == self.expected_size  # And when we're done
            ):
                percent = f"{int(progress/self.expected_size*100)}%"
                STREAM.write(
                    BAR_TEMPLATE
                    % (
                        percent,
                        self.etadisp,
                        self.filled_char * x,
                        self.empty_char * (self.width - x),
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
            STREAM.write(
                BAR_TEMPLATE
                % (
                    percent,
                    elapsed_disp,
                    self.filled_char * self.width,
                    self.empty_char * (self.width - self.width),
                    self.shortlabel,
                )
            )
            STREAM.write("\n")
            STREAM.flush()

    def format_time(self, seconds):
        return time.strftime("%M:%S", time.gmtime(seconds))


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
