"""
Euro Pi Triggers - simple 6 track 16 step trigger sequencer for Euro Pi
author: Thomas Herrmann (github.com/thoherr)
date: 2023-02-14
labels: sequencer, trigger

This script implements a simple trigger sequencer with an easy to use interface to change
the 6 sequences. It makes full use of the limited resources on Euro Pi, esp. the outputs
and screen real estate.

din: clock
ain: not used

k1: select track (1-6
k2: select sequence step (1-16)

b1: toggle step at cursor (on/off)
b2: reset sequence to step 1

cv1: track 1
cv2: track 2
cv3: track 3
cv4: track 4
cv5: track 5
cv6: track 6

"""

from time import sleep
from europi import oled, din, k1, k2, b1, b2, cv1, cv2, cv3, cv4, cv5, cv6, OLED_WIDTH, OLED_HEIGHT, CHAR_HEIGHT
from europi_script import EuroPiScript

VERSION = "0.1"

TRACKS=6
STEPS=16

class Triggers(EuroPiScript):

    initial_state = [ [False] * STEPS for _ in range(TRACKS) ]

    def __init__(self):
        super().__init__()

        # Configure EuroPi options to improve performance ??
        b1.debounce_delay = 200
        b2.debounce_delay = 200
        oled.contrast(0)  # dim the oled
        
        # TODO: load state here and save it on changes
        self.state = self.initial_state

        @b1.handler
        def toggle_step():
            self.state[self.cursor_track][self.cursor_step] ^= 1


    @classmethod
    def display_name(cls):
        return "Triggers"

    def read_cursor(self):
        self.cursor_track = k1.range(TRACKS)
        self.cursor_step = k2.range(STEPS)

    def paint_step(self, track, step, status):
        y = 2 + int((OLED_HEIGHT/TRACKS) * track)
        height = int(OLED_HEIGHT/TRACKS) - 1
        x = 2 + int((OLED_WIDTH/STEPS) * step)
        width = int(OLED_WIDTH/STEPS) - 2
        if status:
            oled.fill_rect(x, y, width, height, 1)
        else:
            oled.rect(x, y, width, height, 1)
        if track == self.cursor_track and step == self.cursor_step:
            oled.rect(x, y, width, height, 0)

    def main(self):
        oled.centre_text(f"EuroPi Triggers\n{VERSION}")
        sleep(1)
        while True:
            oled.fill(0)

            # cursor navigation
            self.read_cursor()

            for i in range(TRACKS):
                for j in range(STEPS):
                    self.paint_step(i, j, self.state[i][j])

            oled.show()

            # self.save_state()

# Main script execution
if __name__ == '__main__':
    script = Triggers()
    script.main()