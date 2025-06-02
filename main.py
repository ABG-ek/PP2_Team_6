from kivy.app import App
from kivy.lang import Builder
from kivy.core.window import Window
from kivy.uix.screenmanager import NoTransition
from database import initialize_db
from UI.screens import *
from UI.widgets import *
from buffer import Buffer
from recognizer import Recognizer


Window.size = (800, 600)


class MainApp(App):
    def build(self):
        Builder.load_file('UI/widgets.kv')
        Builder.load_file('UI/screens.kv')
        root = Builder.load_file('UI/main.kv')
        initialize_db()
        self.buffer = Buffer()
        self.camera = OpenCVCamera()
        self.recognizer = Recognizer()
        root.transition = NoTransition()
        return root
    
if __name__ == '__main__':
    MainApp().run()