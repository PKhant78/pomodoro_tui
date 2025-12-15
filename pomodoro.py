from textual.app import App
from textual.widgets import Button, Footer, Header

class PomodoroApp(App):
    BINDINGS = [("q", "quit", "Quit the Application")]
    def compose(self):
        yield Header(show_clock=True)
        yield Footer()
        yield Button("Start")
        yield Button("Stop")
    
if __name__ == "__main__":
    PomodoroApp().run()