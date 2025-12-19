from textual.app import App, ComposeResult
from textual.widgets import Button, Footer, Header, Static, Digits, Input, Label
from textual.containers import Container, Horizontal
from textual.reactive import reactive
from time import monotonic
from textual import on

# Timer display (counts down)
class TimeDisplay(Digits):
    start_time = reactive(monotonic)
    time = reactive(0.0)  # elapsed time
    total = reactive(0.0)  # accumulated elapsed
    limit = reactive(0.0)  # seconds
    session_type = reactive("study")  # "study" or "break"

    def on_mount(self) -> None:
        self.update_timer = self.set_interval(1/60, self.update_time, pause=True)

    def update_time(self) -> None:
        new_time = self.total + (monotonic() - self.start_time)
        if self.limit > 0 and new_time >= self.limit:
            self.time = self.limit
            self.stop()
            self.on_limit_reached()
        else:
            self.time = new_time

    def watch_time(self, time: float) -> None:
        remaining = max(self.limit - time, 0)
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

    def on_limit_reached(self) -> None:
        self.app.bell()
        self.post_message(SessionEnded())


# Custom message for session end
from textual.message import Message

class SessionEnded(Message):
    pass


# Editable wrapper and Pomodoro
class Pomodoro(Static):
    study_minutes = reactive(25)
    study_seconds = reactive(0)
    break_minutes = reactive(5)
    break_seconds = reactive(0)
    sessions = reactive(4)

    session_type = reactive("study")
    sessions_remaining = reactive(0)

    def compose(self) -> ComposeResult:
        with Container(id="main-container"):
            with Container(id="timer-section"):
                yield TimeDisplay("00:00:00.00", id="timer")
                yield Label(f"Sessions Remaining: {self.sessions}", id="sessions-label")
                
                with Horizontal(id="button-row"):
                    yield Button("Start", id="start")
                    yield Button("Stop", id="stop")
                    yield Button("Reset", id="reset")
                
                with Container(id="input-section"):
                    with Horizontal(classes="input-row"):
                        yield Label("Study:")
                        yield Input(value="25", id="study-min-input", classes="time-input")
                        yield Label("min")
                        yield Input(value="0", id="study-sec-input", classes="time-input")
                        yield Label("sec")
                    
                    with Horizontal(classes="input-row"):
                        yield Label("Break:")
                        yield Input(value="5", id="break-min-input", classes="time-input")
                        yield Label("min")
                        yield Input(value="0", id="break-sec-input", classes="time-input")
                        yield Label("sec")
                    
                    with Horizontal(classes="input-row"):
                        yield Label("Sessions:")
                        yield Input(value="0", id="sessions-input", classes="time-input")

    def get_timer(self) -> TimeDisplay:
        return self.query_one(TimeDisplay)
    
    def watch_sessions_remaining(self, sessions: int) -> None:
        """Update the sessions label when sessions_remaining changes."""
        self.update_sessions_label()
    
    def update_sessions_label(self) -> None:
        """Manually update the sessions label."""
        try:
            label = self.query_one("#sessions-label", Label)
            label.update(f"Sessions Remaining: {self.sessions_remaining}")
        except:
            pass 

    @on(Button.Pressed, "#start")
    def start_clicked(self):
        timer = self.get_timer()
        # Parse inputs
        try:
            self.study_minutes = int(self.query_one("#study-min-input", Input).value or "0")
            self.study_seconds = int(self.query_one("#study-sec-input", Input).value or "0")
            self.break_minutes = int(self.query_one("#break-min-input", Input).value or "0")
            self.break_seconds = int(self.query_one("#break-sec-input", Input).value or "0")
            self.sessions = int(self.query_one("#sessions-input", Input).value or "1")
        except ValueError:
            self.app.bell()
            return

        self.sessions_remaining = self.sessions
        self.start_session("study")

    def start_session(self, session_type: str):
        timer = self.get_timer()
        timer.session_type = session_type
        
        if session_type == "study":
            timer.limit = (self.study_minutes * 60) + self.study_seconds
        else:
            timer.limit = (self.break_minutes * 60) + self.break_seconds
        
        timer.reset()
        timer.start()
        self.session_type = session_type
        # Update color
        timer.styles.background = "green" if session_type == "study" else "red"

    @on(Button.Pressed, "#stop")
    def stop_clicked(self):
        self.get_timer().stop()

    @on(Button.Pressed, "#reset")
    def reset_clicked(self):
        timer = self.get_timer()
        timer.stop()
        self.sessions_remaining = self.sessions
        timer.styles.background = "transparent"
        timer.reset()

    @on(SessionEnded)
    def handle_session_end(self, event: SessionEnded):
        if self.session_type == "study":
            self.start_session("break")
        else:  # break ended
            self.sessions_remaining -= 1
            if self.sessions_remaining > 0:
                self.start_session("study")
            else:
                timer = self.get_timer()
                timer.stop()
                timer.styles.background = "transparent"


# App
class PomodoroApp(App):
    CSS_PATH = "pomodoro.tcss"
    BINDINGS = [
        ("q", "quit", "Quit"),
        ("s", "start", "Start"),
        ("t", "stop", "Stop"),
        ("k", "reset", "Reset")
    ]

    def compose(self):
        yield Header(show_clock=True)
        yield Footer()
        yield Pomodoro()


if __name__ == "__main__":
    PomodoroApp().run()