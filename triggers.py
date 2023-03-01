"""
Euro Pi Triggers - simple 6 track 8/16/24 step trigger sequencer for Euro Pi
author: Thomas Herrmann (github.com/thoherr)

For user documentation of this script see file triggers.md

"""

from time import sleep
from utime import ticks_diff, ticks_ms
from europi import *
from europi_script import EuroPiScript

VERSION = "0.2"

TRACKS = 6
MAX_STEPS = 24
SEQUENCE_STEPS = [int(MAX_STEPS / 3), int(MAX_STEPS / 3 * 2), MAX_STEPS]

SAVE_STATE_INTERVAL = 5000
SHORT_PRESSED_INTERVAL = 600  # feels about 1 second
LONG_PRESSED_INTERVAL = 2400  # feels about 4 seconds


class Triggers(EuroPiScript):
    initial_state = [[False] * MAX_STEPS for _ in range(TRACKS)]
    state_saved = True
    cvs = [cv1, cv2, cv3, cv4, cv5, cv6]

    def __init__(self):
        super().__init__()

        oled.contrast(0)

        self.sequence_step_index = 1
        self.sequence_steps = SEQUENCE_STEPS[self.sequence_step_index]
        self.looped_steps = self.sequence_steps
        self.state = self.initial_state
        self.current_step = 0

        self.load_state()

        self.display_data_changed = True

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
            self.display_data_changed = True

        @b2.handler_falling
        def handle_falling_b2():
            time_pressed = ticks_diff(ticks_ms(), b2.last_pressed())
            if time_pressed >= LONG_PRESSED_INTERVAL:
                self.iterate_sequence_steps()
                self.state_saved = False
            elif time_pressed >= SHORT_PRESSED_INTERVAL:
                self.set_step_count()
                self.state_saved = False
            else:
                self.jump_to_start()
            self.display_data_changed = True

        @din.handler
        def clock():
            self.current_step = (self.current_step + 1) % self.looped_steps
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
        self.save_state_str(
            "\n".join(
                "".join("1" if i else "0" for i in self.state[j]) for j in range(TRACKS)
            )
            + "\n"
            + str(self.looped_steps)
            + "\n"
            + str(self.sequence_step_index)
        )
        self.state_saved = True

    def load_state(self):
        state = self.load_state_str()
        if state:
            tracks = state.splitlines()
            self.state = [[c == "1" for c in tracks[i]] for i in range(TRACKS)]
            i = TRACKS
            self.looped_steps = int(i)
            i += 1
            self.sequence_step_index = int(i)

    def iterate_sequence_steps(self):
        self.sequence_step_index = (self.sequence_step_index + 1) % len(SEQUENCE_STEPS)
        self.sequence_steps = SEQUENCE_STEPS[self.sequence_step_index]
        if self.looped_steps > self.sequence_steps:
            self.looped_steps = self.sequence_steps
        if self.current_step > self.sequence_steps:
            self.jump_to_start()

    def set_step_count(self):
        self.looped_steps = self.cursor_step + 1
        if self.current_step > self.cursor_step:
            self.jump_to_start()

    def jump_to_start(self):
        self.current_step = 0
        self.update_cvs()

    def update_cvs(self):
        for i in range(TRACKS):
            self.cvs[i].value(self.state[i][self.current_step])
        self.display_data_changed = True

    def clear_all_tracks(self):
        for i in range(TRACKS):
            for j in range(MAX_STEPS):
                self.state[i][j] = False
        self.display_data_changed = True

    def clear_current_track(self):
        for j in range(MAX_STEPS):
            self.state[self.cursor_track][j] = False
        self.display_data_changed = True

    def toggle_step(self):
        self.state[self.cursor_track][self.cursor_step] ^= 1
        self.display_data_changed = True

    def read_cursor(self):
        self.cursor_track = k1.range(TRACKS)
        self.cursor_step = k2.range(self.sequence_steps)

    def paint_single_step_state(self, track, step, status):
        y = 1 + int((OLED_HEIGHT / TRACKS) * track)
        height = int(OLED_HEIGHT / TRACKS) - 1
        x = 2 + int((OLED_WIDTH / self.sequence_steps) * step)
        width = int(OLED_WIDTH / self.sequence_steps) - 2
        if status:
            oled.fill_rect(x, y, width, height, 1)
        else:
            oled.rect(x, y, width, height, 1)
        if track == self.cursor_track and step == self.cursor_step:
            oled.rect(x, y, width, height, 0)

    def paint_current_step_position(self, step):
        x = 1 + int((OLED_WIDTH / self.sequence_steps) * step)
        length = int(OLED_WIDTH / self.sequence_steps)
        oled.hline(x, 0, length, 1)
        oled.hline(x, OLED_HEIGHT - 1, length, 1)

    def paint_end_of_loop(self, step):
        x = int((OLED_WIDTH / self.sequence_steps) * step)
        oled.vline(x, 0, OLED_HEIGHT, 1)

    def update_display(self):
        if self.display_data_changed:
            oled.fill(0)

            for i in range(TRACKS):
                for j in range(self.sequence_steps):
                    self.paint_single_step_state(i, j, self.state[i][j])

            self.paint_current_step_position(self.current_step)

            if self.looped_steps < self.sequence_steps:
                self.paint_end_of_loop(self.looped_steps)

            oled.show()

            self.display_data_changed = False

    def main(self):
        oled.centre_text(f"EuroPi Triggers\n{VERSION}")
        sleep(1)
        while True:
            self.read_cursor()
            self.update_display()
            self.save_state()
            sleep(0.01)


# Main script execution
if __name__ == "__main__":
    script = Triggers()
    script.main()
