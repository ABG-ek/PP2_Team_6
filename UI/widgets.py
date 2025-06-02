from kivy.uix.screenmanager import ScreenManager
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.widget import Widget
from kivy.properties import ListProperty, StringProperty, NumericProperty, BooleanProperty
from utils import *
from kivy.uix.button import ButtonBehavior, Button
from kivy.uix.image import Image
from kivy.graphics.texture import Texture
from kivy.graphics import Color, Rectangle, RoundedRectangle, StencilPush, StencilUse, StencilUnUse, StencilPop
from kivy.clock import Clock, mainthread
from kivy.uix.stencilview import StencilView
from kivy.graphics import Color, RoundedRectangle
from kivy.uix.textinput import TextInput


import cv2
import threading
import numpy as np
import time

class BgBox(BoxLayout):
    bg_color = StringProperty('FFFFFF')  # HEX строка
    bg = ListProperty([1, 1, 1, 1])       # RGBA-цвет для canvas

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.update_bg_color()
        self.bind(bg_color=lambda *a: self.update_bg_color())

    def update_bg_color(self):
        try:
            self.bg = hex_to_kivy_color(self.bg_color)
        except Exception as e:
            print("Ошибка преобразования цвета:", e)


class RoundedBgBox(BoxLayout):
    bg_color = StringProperty('FFFFFF')  # HEX строка
    bg = ListProperty([1, 1, 1, 1])       # RGBA-цвет для canvas
    radius = NumericProperty(20)
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.update_bg_color()
        self.bind(bg_color=lambda *a: self.update_bg_color())

    def update_bg_color(self):
        try:
            self.bg = hex_to_kivy_color(self.bg_color)
        except Exception as e:
            print("Ошибка преобразования цвета:", e)



class StrokeBgBox(BoxLayout):
    bg_color = StringProperty('FFFFFF')  # HEX строка
    bg = ListProperty([1, 1, 1, 1])       # RGBA-цвет для canvas

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.update_bg_color()
        self.bind(bg_color=lambda *a: self.update_bg_color())

    def update_bg_color(self):
        try:
            self.bg = hex_to_kivy_color(self.bg_color)
        except Exception as e:
            print("Ошибка преобразования цвета:", e)



class HexRoundedButton(ButtonBehavior, BoxLayout):
    text = StringProperty("Кнопка")
    font_name = StringProperty("Roboto")
    font_size = NumericProperty(16)

    text_color_hex = StringProperty("FFFFFF")
    bg_hex = StringProperty("3498db")
    bg_hex_down = StringProperty("2980b9")

    text_color = ListProperty([1, 1, 1, 1])
    bg_color = ListProperty([0.2, 0.6, 0.86, 1])
    bg_color_down = ListProperty([0.16, 0.5, 0.72, 1])

    radius = NumericProperty(10)
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.update_colors()
        self.bind(bg_hex=lambda *a: self.update_colors(),
                  bg_hex_down=lambda *a: self.update_colors(),
                  text_color_hex=lambda *a: self.update_colors())

    def update_colors(self):
        try:
            self.bg_color = hex_to_kivy_color(self.bg_hex)
            self.bg_color_down = hex_to_kivy_color(self.bg_hex_down)
            self.text_color = hex_to_kivy_color(self.text_color_hex)
        except Exception as e:
            print("Ошибка цвета:", e)


class HexLabel(Label):
    color_hex = StringProperty("000000")  # чёрный по умолчанию
    color_rgba = ListProperty([0, 0, 0, 1])

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.update_color()
        self.bind(color_hex=lambda *a: self.update_color())

    def update_color(self):
        try:
            self.color_rgba = hex_to_kivy_color(self.color_hex)
            self.color = self.color_rgba  # применяем цвет к стандартному Label-свойству
        except Exception as e:
            print("Ошибка цвета в HexLabel:", e)


class PLUTextInput(TextInput):
    def insert_text(self, substring, from_undo=False):
        new_text = self.text + substring
        if new_text.isdigit():
            value = int(new_text)
            if 1 <= value <= 9999:
                super().insert_text(substring, from_undo=from_undo)

class NameTextInput(TextInput):
    def insert_text(self, substring, from_undo=False):
        if len(self.text) + len(substring) <= 50:
            super().insert_text(substring, from_undo=from_undo)

class PriceTextInput(TextInput):
    def insert_text(self, substring, from_undo=False):
        new_text = self.text + substring

        # Ограничим общую длину
        if len(new_text) > 10:
            return

        # Разрешим временный ввод запятой/точки
        if substring in [",", "."]:
            if "," in self.text or "." in self.text:
                return  # Запятая уже есть
            super().insert_text(substring, from_undo=from_undo)
            return

        # Заменим запятую на точку для float
        potential_text = new_text.replace(',', '.')

        try:
            value = float(potential_text)
            if value < 0:
                return  # Только положительные

            # Проверим количество знаков после точки
            if '.' in potential_text:
                decimals = potential_text.split('.')[-1]
                if len(decimals) > 2:
                    return  # Больше двух знаков после точки

            super().insert_text(substring, from_undo=from_undo)
        except ValueError:
            pass



class Card(ButtonBehavior, BoxLayout):
    title = StringProperty()
    plu_code = StringProperty()
    price_per_kg = StringProperty()
    card_image = StringProperty()
    card_size = NumericProperty(14)

    bg_hex = StringProperty("3498db")
    bg_hex_down = StringProperty("2980b9")

    bg_color = ListProperty([0.2, 0.6, 0.86, 1])
    bg_color_down = ListProperty([0.16, 0.5, 0.72, 1])

    radius = NumericProperty(10)
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.update_colors()
        self.bind(bg_hex=lambda *a: self.update_colors(),
                  bg_hex_down=lambda *a: self.update_colors(),)

    def update_colors(self):
        try:
            self.bg_color = hex_to_kivy_color(self.bg_hex)
            self.bg_color_down = hex_to_kivy_color(self.bg_hex_down)
        except Exception as e:
            print("Ошибка цвета:", e)
            

class OpenCVCamera(Widget):
    flip_vertical = BooleanProperty(False)
    corner_radius = NumericProperty(40)
    update_fps = 30

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.texture = None
        self.frame = None
        self.running = True

        self.cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

        if not self.cap.isOpened():
            raise RuntimeError("❌ Не удалось открыть камеру")

        with self.canvas:
            StencilPush()
            self.mask_color = Color(1, 1, 1, 1)
            self.mask = RoundedRectangle(pos=self.pos, size=self.size, radius=[self.corner_radius])
            StencilUse()

            self.image_rect = Rectangle(pos=self.pos, size=self.size)

            StencilUnUse()
            StencilPop()

        self.bind(pos=self._update, size=self._update, corner_radius=self._update)

        self.capture_thread = threading.Thread(target=self._capture_loop)
        self.capture_thread.daemon = True
        self.capture_thread.start()

    def _update(self, *args):
        self.mask.pos = self.pos
        self.mask.size = self.size
        self.mask.radius = [self.corner_radius]
        self.image_rect.pos = self.pos
        self.image_rect.size = self.size

    def _capture_loop(self):
        while self.running:
            ret, frame = self.cap.read()
            if not ret:
                continue

            square = self._crop_center_square(frame)
            if self.flip_vertical:
                square = cv2.flip(square, 0)

            rgb = cv2.cvtColor(square, cv2.COLOR_BGR2RGB)

            self.frame = square
            self._update_texture(rgb)

            # sleep to maintain desired FPS
            time.sleep(1.0 / self.update_fps)

    @mainthread
    def _update_texture(self, rgb):
        if self.texture is None or self.texture.size != (rgb.shape[1], rgb.shape[0]):
            self.texture = Texture.create(size=(rgb.shape[1], rgb.shape[0]), colorfmt='rgb')
            self.texture.flip_vertical()

        self.texture.blit_buffer(rgb.tobytes(), colorfmt='rgb', bufferfmt='ubyte')
        self.image_rect.texture = self.texture

    def capture(self, filename="snapshot.png"):
        if self.frame is not None:
            cv2.imwrite(filename, self.frame)
            print(f"✅ Снимок сохранён: {filename}")


    def stop(self):
        self.running = False
        if self.cap.isOpened():
            self.cap.release()

    def start(self):
        if not self.running:
            self.cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
            self.running = True
            self.capture_thread = threading.Thread(target=self._capture_loop)
            self.capture_thread.daemon = True
            self.capture_thread.start()

    def _crop_center_square(self, img):
        h, w = img.shape[:2]
        min_dim = min(h, w)
        start_x = (w - min_dim) // 2
        start_y = (h - min_dim) // 2
        return img[start_y:start_y + min_dim, start_x:start_x + min_dim]
    
    def get_current_frame(self, rgb=True) -> np.ndarray:
        if self.frame is not None:
            if rgb:
                return cv2.cvtColor(self.frame.copy(), cv2.COLOR_BGR2RGB)
            return self.frame.copy()
        else:
            raise ValueError("❌ Кадр ещё не доступен.")