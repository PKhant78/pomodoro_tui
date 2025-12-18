from textual.app import App, ComposeResult
from textual.widgets import Button, Footer, Header, Static, Digits, Input
from textual.containers import Container
from textual.reactive import reactive
from time import monotonic
from textual import on

# Timer display
class TimeDisplay(Digits):
    """Widget to display remaining time."""

    start_time = reactive(monotonic)
    time = reactive(0.0)  # elapsed time
    total = reactive(0.0)  # accumulated elapsed
    interval = reactive(0.0)  # seconds to count down from
    session_type = reactive("study")

    def on_mount(self) -> None:
        self.update_timer = self.set_interval(1 / 60, self.update_time, pause=True)

    def update_time(self) -> None:
        """Update elapsed time and check interval"""
        new_time = self.total + (monotonic() - self.start_time)
        if self.interval > 0 and new_time >= self.interval:
            self.time = self.interval
            self.stop()
            self.on_interval_reached()
        else:
            self.time = new_time

    def watch_time(self, time: float) -> None:
        """Display remaining time."""
        remaining = max(self.interval - time, 0) if self.interval else time
        minutes, seconds = divmod(remaining, 60)
        hours, minutes = divmod(minutes, 60)
        self.update(f"{int(hours):02}:{int(minutes):02}:{seconds:05.2f}")

    def start(self) -> None:
        self.start_time = monotonic()
        self.update_timer.resume()

    def stop(self):
        self.update_timer.pause()
        self.total += monotonic() - self.start_time
        self.time = self.total

    def reset(self):
        self.total = 0
        self.time = 0

    def on_interval_reached(self) -> None:
        self.app.bell()  # optional alert



# Wrapper for Timer
class EditableTimeDisplay(Static):
    """A TimeDisplay that the user can edit directly."""

    editing = reactive(True)  # start in edit mode

    def compose(self) -> ComposeResult:
        yield Input(placeholder="MM:SS", id="timer-input")
        yield TimeDisplay("00:00", id="timer-display")

    def on_mount(self):
        self.show_input()

    def show_input(self):
        self.query_one("#timer-input").display = True
        self.query_one("#timer-display").display = False
        self.query_one("#timer-input").focus()

    def show_display(self):
        self.query_one("#timer-input").display = False
        self.query_one("#timer-display").display = True

    @on(Input.Submitted)
    def input_submitted(self, event: Input.Submitted):
        value = event.value.strip()
        try:
            # Parse MM:SS or just minutes
            if ":" in value:
                m, s = value.split(":")
                total_seconds = int(m) * 60 + float(s)
            else:
                total_seconds = float(value) * 60
        except ValueError:
            self.app.bell()
            return

        timer = self.query_one(TimeDisplay)
        timer.interval = total_seconds
        timer.update_time() 
        timer.reset()
        self.show_display()



# UI
class Pomodoro(Static):
    study_minutes = reactive(25)
    break_minutes = reactive(5)
    cycles = reactive(4)

    session_type = reactive("study")
    cycles_remaining = reactive(0)


    def compose(self) -> ComposeResult:
        with Container(id="main-container"):
            with Container(id="button-column"):
                yield Button("Start", id="start")
                yield Button("Stop", id="stop")
                yield Button("Reset", id="reset")
                yield Button("Change Interval", id="change-interval")

            with Container(id="timer-container"):
                yield EditableTimeDisplay(id="editable-timer")

    def get_timer(self) -> TimeDisplay:
        return self.query_one("#editable-timer").query_one(TimeDisplay)

    @on(Button.Pressed, "#start")
    def start_clicked(self):
        self.get_timer().start()

    @on(Button.Pressed, "#stop")
    def stop_clicked(self):
        self.get_timer().stop()

    @on(Button.Pressed, "#reset")
    def reset_clicked(self):
        self.get_timer().reset()

    @on(Button.Pressed, "#change-interval")
    def change_interval(self):
        editable = self.query_one("#editable-timer")
        editable.show_input()  # switch back to input



# App
class PomodoroApp(App):
    BINDINGS = [
        ("q", "quit", "Quit the Application"),
        ("s", "start", "Start Timer"),
        ("t", "stop", "Stop Timer"),
        ("k", "reset", "Reset Timer")
    ]

    CSS_PATH = "pomodoro.tcss"

    def compose(self):
        yield Header(show_clock=True)
        yield Footer()
        yield Pomodoro()

    def action_start(self) -> None: 
        """Start the timer.""" 
        self.query_one(TimeDisplay).start() 
        
    def action_stop(self) -> None: 
        """Stop the timer.""" 
        self.query_one(TimeDisplay).stop() 
    
    def action_reset(self) -> None: 
        self.query_one(TimeDisplay).stop() # maybe remove 
        self.query_one(TimeDisplay).reset()


if __name__ == "__main__":
    PomodoroApp().run()
