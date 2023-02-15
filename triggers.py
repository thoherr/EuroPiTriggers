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

k1: select track (1-6)
k2: select sequence step (1-16)

b1: toggle step at cursor (on/off),
    clear all steps in current track when pressed for 1-3 seconds,
    clear all steps when pressed for 4 seconds or longer
b2: reset sequence to step 1

cv1: track 1
cv2: track 2
cv3: track 3
cv4: track 4
cv5: track 5
cv6: track 6

"""

from time import sleep
from utime import ticks_diff, ticks_ms
from europi import oled, din, k1, k2, b1, b2, cv1, cv2, cv3, cv4, cv5, cv6, OLED_WIDTH, OLED_HEIGHT, CHAR_HEIGHT
from europi_script import EuroPiScript

VERSION = "0.1"

TRACKS=6
STEPS=16

SAVE_STATE_INTERVAL=5000
SHORT_PRESSED_INTERVAL=600  # feels about 1 second
LONG_PRESSED_INTERVAL=2400 # feels about 4 seconds

class Triggers(EuroPiScript):

    initial_state = [ [False] * STEPS for _ in range(TRACKS) ]
    state_saved = True
    cvs = [ cv1, cv2, cv3, cv4, cv5, cv6 ]

    def __init__(self):
        super().__init__()

        oled.contrast(0)
        
        self.state = self.initial_state
        self.load_state()

        self.steps = STEPS
        self.current_step = 0

        @b1.handler_falling
        def handle_falling_b1():
            time_pressed = ticks_diff(ticks_ms(), b1.last_pressed())
            if time_pressed >= LONG_PRESSED_INTERVAL:
                self.clear_all_tracks()
            elif time_pressed >= SHORT_PRESSED_INTERVAL:
                self.clear_current_track()
            else:
                self.toggle_step()
            self.state_saved = False

        @b2.handler_falling
        def handle_falling_b2():
            time_pressed = ticks_diff(ticks_ms(), b2.last_pressed())
            if time_pressed >= SHORT_PRESSED_INTERVAL:
                self.set_step_count()
            else:
                self.jump_to_start()
            
        @din.handler
        def clock():
            self.current_step = (self.current_step + 1) % self.steps
            self.update_cvs()

        @din.handler_falling
        def reset_cvs():
            for i in range(TRACKS):
                self.cvs[i].value(False)

    @classmethod
    def display_name(cls):
        return "Triggers"

    def save_state(self):
        if self.state_saved or self.last_saved() < SAVE_STATE_INTERVAL:
            return
        self.save_state_str('\n'.join(''.join('1' if i else '0'
                                                for i in self.state[j])
                                        for j in range(TRACKS)))
        self.state_saved = True

    def load_state(self):
        state = self.load_state_str()
        if state:
            tracks = state.splitlines()
            self.state = [ [c == '1' for c in tracks[i] ] for i in range(TRACKS) ]

    def set_step_count(self):
        self.steps = self.cursor_step + 1
        if self.current_step > self.cursor_step:
            self.jump_to_start()

    def jump_to_start(self):
        self.current_step = 0
        self.update_cvs()

    def update_cvs(self):
        for i in range(TRACKS):
            self.cvs[i].value(self.state[i][self.current_step])

    def clear_all_tracks(self):
        for i in range(TRACKS):
            for j in range(STEPS):
                self.state[i][j] = False

    def clear_current_track(self):
        for j in range(STEPS):
            self.state[self.cursor_track][j] = False

    def toggle_step(self):
        self.state[self.cursor_track][self.cursor_step] ^= 1

    def read_cursor(self):
        self.cursor_track = k1.range(TRACKS)
        self.cursor_step = k2.range(STEPS)

    def paint_single_step_state(self, track, step, status):
        y = 1 + int((OLED_HEIGHT/TRACKS) * track)
        height = int(OLED_HEIGHT/TRACKS) - 1
        x = 2 + int((OLED_WIDTH/STEPS) * step)
        width = int(OLED_WIDTH/STEPS) - 2
        if status:
            oled.fill_rect(x, y, width, height, 1)
        else:
            oled.rect(x, y, width, height, 1)
        if track == self.cursor_track and step == self.cursor_step:
            oled.rect(x, y, width, height, 0)

    def paint_current_step_position(self, step):
        x = 1 + int((OLED_WIDTH/STEPS) * step)
        length = int(OLED_WIDTH/STEPS)
        oled.hline(x, 0, length, 1)
        oled.hline(x, OLED_HEIGHT-1, length, 1)

    def paint_end_of_loop(self, step):
        x = int((OLED_WIDTH/STEPS) * step)
        oled.vline(x, 0, OLED_HEIGHT, 1)

    def main(self):
        oled.centre_text(f"EuroPi Triggers\n{VERSION}")
        sleep(1)
        while True:
            oled.fill(0)

            self.read_cursor()

            for i in range(TRACKS):
                for j in range(STEPS):
                    self.paint_single_step_state(i, j, self.state[i][j])

            self.paint_current_step_position(self.current_step)

            if self.steps < STEPS:
                self.paint_end_of_loop(self.steps)

            oled.show()

            self.save_state()

# Main script execution
if __name__ == '__main__':
    script = Triggers()
    script.main()