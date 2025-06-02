from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.properties import StringProperty, NumericProperty
from kivy.app import App
from kivy.clock import Clock
from recognizer import *
from UI.widgets import *
import time
from threading import Thread
from kivy.metrics import dp

class Manager(ScreenManager):
    pass

class RecognizerScreen(Screen):
    def on_pre_enter(self, *args):
        Clock.schedule_once(self.attach_camera, 0)

    def attach_camera(self, dt=None):  # ✅ dt теперь необязательный
        app = App.get_running_app()
        camera = app.camera
        if camera.parent:
            camera.parent.remove_widget(camera)
        self.ids.camera_box.add_widget(camera)

    def change_to_menu(self):
        app = App.get_running_app()
        app.root.current = 'MenuScreen'
    
    def recognize(self):
        app = App.get_running_app()
        print(app.recognizer.cache)

        try:
            # Проверка: достаточно ли товаров в кэше
            cache_size = len(app.recognizer.cache)
            if cache_size == 0:
                print("❌ В кэше нет товаров. Проверь базу данных.")
                app.buffer.result = []
                return
            elif cache_size < 3:
                print(f"⚠️ В кэше только {cache_size} товар(а). Топ-3 будет усечён.")

            # 1. Кадр с камеры
            frame = app.camera.get_current_frame(rgb=True)

            # 2. Эмбеддинг
            embedding = app.recognizer.extract_embedding_from_array(frame)

            # 3. Получаем top-N (до 3, но может вернуться меньше)
            top_results = app.recognizer.recognize(embedding, top_n=3)

            # 4. Сохраняем в буфер
            app.buffer.result = top_results

            # 5. Выводим
            if top_results:
                print("\n📋 Топ распознанных товара:")
                for i, (product, score) in enumerate(top_results, start=1):
                    title = product.get("title", "—")
                    plu = product.get("plu_code", "—")
                    print(f"{i}. {title} (PLU: {plu}) — score: {score:.4f}")
                    app.root.current = 'ItemPickerScreen'
            else:
                print("❌ Ничего не распознано.")
                app.buffer.result = []

        except Exception as e:
            print(f"❌ Ошибка при распознавании: {e}")

class MenuScreen(Screen):
    def change_to(self, screen, mode=None):
        app = App.get_running_app()
        app.buffer.catalog_mode = mode
        app.root.current = screen

class EditProductScreen(Screen):
    card_image = StringProperty('')
    
    def on_pre_enter(self, *args):
        self.load()
        Clock.schedule_once(self.attach_camera, 0)
        
    def attach_camera(self, dt=None):  # ✅ dt теперь необязательный
        app = App.get_running_app()
        camera = app.camera
        if camera.parent:
            camera.parent.remove_widget(camera)
        self.ids.camera_box.add_widget(camera)
    
    def back_to_menu(self):
        app = App.get_running_app()
        buffer = App.get_running_app().buffer
        buffer.clear()
        app.root.current = 'MenuScreen'
    

    def make_photo_to_card(self):
        app = App.get_running_app()
        app.camera.capture()  # сохраняет snapshot.png

        self.ids.card_image_preview.source = ''
        self.card_image = "snapshot.png"

        def process_image():
            try:
                from rembg import remove
                from PIL import Image
                output_path = "snapshot.png"

                with Image.open("snapshot.png") as img:
                    img = img.convert("RGBA")
                    result = remove(img)
                    result.save(output_path)

                # Обновление UI из главного потока
                def update_preview(dt):
                    self.card_image = output_path
                    self.ids.card_image_preview.source = self.card_image
                    self.ids.card_image_preview.reload()
                    print("✅ Фон удалён, карточка обновлена.")

                Clock.schedule_once(update_preview)

            except Exception as e:
                print(f"❌ Ошибка при вырезании фона: {e}")

        # Запуск в фоне
        Thread(target=process_image).start()

    def go_to_learn_screen(self):
        buffer = App.get_running_app().buffer
        buffer.title = self.ids.title.text if self.ids.title.text else None
        buffer.plu_code = int(self.ids.plu_code.text) if self.ids.plu_code.text else None
        buffer.price_per_kg = float(self.ids.price_per_kg.text) if self.ids.price_per_kg.text else None
        buffer.card_image =  self.card_image
        App.get_running_app().root.current = 'LearnProductScreen'
        print('на экран обучния')
    
    def load(self):
        buffer = App.get_running_app().buffer
        self.ids.title.text = str(buffer.title) if buffer.title else ''
        self.ids.plu_code.text = str(buffer.plu_code) if buffer.plu_code else ''
        self.ids.price_per_kg.text = str(buffer.price_per_kg) if buffer.price_per_kg else ''

        if buffer.card_image == None: 
            self.card_image = 'assets/tomat.png'
        else:
            self.card_image = buffer.card_image


class LearnProductScreen(Screen):
    status = StringProperty('')
    def on_pre_enter(self, *args):
        app = App.get_running_app()
        self.status = f'Кол-во снимков: {app.buffer.count}' if app.buffer.count else f'Кол-во снимков: {0}'
        Clock.schedule_once(self.attach_camera, 0)

    def attach_camera(self, dt=None):  # ✅ dt теперь необязательный
        app = App.get_running_app()
        camera = app.camera
        if camera.parent:
            camera.parent.remove_widget(camera)
        self.ids.camera_box.add_widget(camera)

    def on_leave(self, *args):
        camera = App.get_running_app().camera
        if camera.parent:
            camera.parent.remove_widget(camera)

    def back_to_info_screen(self, dt=None):
        app = App.get_running_app()
        app.root.current = 'EditProductScreen'

        # 💡 Принудительно вызвать attach_camera после смены
        screen = app.root.get_screen('EditProductScreen')
        Clock.schedule_once(lambda dt: screen.attach_camera(), 0)
    
    def make_photo(self):
        app =  App.get_running_app()
        
        try:
            frame = app.camera.get_current_frame(rgb=True)
            embedding = app.recognizer.extract_embedding_from_array(frame)
            app.buffer.update_embedding(embedding)
            self.status = f'Кол-во снимков: {(app.buffer.count or 0) + len(app.buffer.session_embeddings)}'

            print(f"✅ Добавлен кадр. Всего в буфере: {(app.buffer.count or 0) + len(app.buffer.session_embeddings)}")
        except Exception as e:
            print(f"❌ Ошибка при обработке фото: {e}")
        
    def restart_make_photo(self):
        app = App.get_running_app()
        buffer = app.buffer

        try:
            buffer.session_embeddings = []
            if buffer.base_embedding is not None and buffer.count:
                buffer.mean_embedding = buffer.base_embedding.copy()
            else:
                buffer.mean_embedding = None

            self.status = f'Кол-во снимков: 0'
            print("✅ Успешный рестарт: сессионные снимки сброшены.")
        except Exception as e:
            print(f"❌ Ошибка при рестарте: {e}")
    
    def save_product(self):
        app = App.get_running_app()
        buffer = app.buffer
        buffer.save_to_db()
        buffer.clear()
        app.recognizer.load_cache()
        app.root.current = 'MenuScreen'


class CatalogScreen(Screen):
    page = NumericProperty(0)
    page_size = NumericProperty(8)
    work_mode = StringProperty('')

    def on_pre_enter(self, *args):
        self.page = 0
        App.get_running_app().recognizer.load_cache()
        self.update()
        return super().on_pre_enter(*args)

    def update(self):
        self.ids.catalog_grid.clear_widgets()
        App.get_running_app().recognizer.load_cache()
        catalog = App.get_running_app().recognizer.cache
        self.chek_mode()

        start = self.page * self.page_size
        end = start + self.page_size
        current_items = catalog[start:end]

        # Добавление карточек
        for product in current_items:
            card = Card(
                price_per_kg=str(product["price_per_kg"]),
                title=product["title"],
                plu_code=str(product["plu_code"]),
                card_image=product["card_image"]
            )
            card.on_release = lambda instance=card: self.select_position(instance)
            card.ids.image.texture = None
            card.ids.image.source = product['card_image']
            card.ids.image.reload()
            self.ids.catalog_grid.add_widget(card)

        # Заполнение до page_size пустыми виджетами (для выравнивания)
        for _ in range(self.page_size - len(current_items)):
            self.ids.catalog_grid.add_widget(Widget())

    def change_page(self, direction):
        catalog = App.get_running_app().recognizer.cache
        max_page = max(0, (len(catalog) - 1) // self.page_size)

        if direction == 'next' and self.page < max_page:
            self.page += 1
            self.update()
        elif direction == 'prev' and self.page > 0:
            self.page -= 1
            self.update()
        else:
            print("Нет больше страниц.")
    
    def chek_mode(self):
        self.mode = App.get_running_app().buffer.catalog_mode
        if self.mode == 'edit':
            self.ids.catalog_title.text = 'Редактировать товар'
            self.ids.catalog_button.text = 'В меню'
        elif self.mode == 'delete':
            self.ids.catalog_title.text = 'Удалить товар'
            self.ids.catalog_button.text = 'В меню'
        elif self.mode == 'work':
            self.ids.catalog_title.text = 'Выберите правильный товар'
            self.ids.catalog_button.text = 'В меню'

    def select_position(self, instance):
        app = App.get_running_app()
        buffer = app.buffer

        plu = int(instance.plu_code)

        if self.mode == 'delete':
            buffer.delete_from_db_by_plu(plu)
            self.update()

        elif self.mode in ('work', 'edit'):
            if buffer.load_from_db_by_plu(plu):
                app.add_item_data = [
                    buffer.title,
                    buffer.price_per_kg,
                    buffer.plu_code,
                    buffer.card_image
                ]
                app.root.current = 'ResultScreen' if self.mode == 'work' else 'EditProductScreen'



    def go_to_menu(self):
        App.get_running_app().buffer.clear()
        App.get_running_app().root.current = 'MenuScreen'

class ItemPickerScreen(Screen):
    def on_pre_enter(self, *args):
        Clock.schedule_once(lambda dt: self.update(), 0)
        return super().on_pre_enter(*args)


    def go_to_catalog(self, mode):
        app = App.get_running_app()
        app.buffer.catalog_mode = mode
        app.root.current = 'CatalogScreen'

    def go_to_menu(self):
        app = App.get_running_app()
        app.buffer.clear()
        app.root.current = 'MenuScreen'

    def update(self):
        app = App.get_running_app()
        buffer = app.buffer

        # Очистим виджеты, чтобы не дублировались
        self.ids.picker_grid.clear_widgets()
        self.ids.picker_grid.cols = len(buffer.result) + 1

        screen_width = self.width
        screen_height = self.height
        result_count = len(buffer.result)
        if result_count == 1:
            self.ids.picker_grid.padding = [
                0.183 * screen_width,
                0.115 * screen_height,
                0.183 * screen_width,
                0.229 * screen_height
            ]
            self.ids.picker_grid.spacing = 0.025 * screen_width
            card_size = 18

        elif result_count == 2:
            self.ids.picker_grid.padding = [
                0.025 * screen_width,
                0.115 * screen_height,
                0.025 * screen_width,
                0.229 * screen_height
            ]
            self.ids.picker_grid.spacing = 0.025 * screen_width
            card_size = 18

        else:
            self.ids.picker_grid.padding = [
                0.025 * screen_width,
                0.183 * screen_height,
                0.025 * screen_width,
                0.298 * screen_height
            ]
            self.ids.picker_grid.spacing = 0.025 * screen_width
            card_size = 16

        # Создаём кнопку "Далее"
        button = HexRoundedButton(
            text="Полный каталог",
            bg_hex="2B2B2B",
            bg_hex_down="DEDEDE",
            text_color_hex="FFFFFF",
            font_size=16,
            font_name="fonts/Roboto-Bold.ttf",
            on_release=lambda instance: self.go_to_catalog('work') # self, а не root
        )

        # Добавим отступ в начале, если нужно
        

        # Создаём карточки
        for product, _ in buffer.result:
            card = Card(
                price_per_kg=str(product["price_per_kg"]),
                title=product["title"],
                plu_code=str(product["plu_code"]),
                card_image=product["card_image"],
                card_size = card_size
            )
            card.on_release = lambda instance=card: self.select_position(instance)
            card.ids.image.texture = None
            card.ids.image.source = product['card_image']
            card.ids.image.reload()
            self.ids.picker_grid.add_widget(card)

        # Добавляем кнопку "Далее"
        self.ids.picker_grid.add_widget(button)

        # Добавим отступ в конце, если было ровно 1
        
    def select_position(self, instance):
        app = App.get_running_app()
        buffer = app.buffer

        plu = int(instance.plu_code)
        buffer.load_from_db_by_plu(plu)
        app.root.current = 'ResultScreen' 


class ResultScreen(Screen):
    def on_pre_enter(self, *args):
        self.update()
        return super().on_pre_enter(*args)
    
    def update(self):
        app = App.get_running_app()
        buffer = app.buffer

        self.ids.card_place.clear_widgets()

        card = Card(
            price_per_kg=str(buffer.price_per_kg),
            title=buffer.title,
            plu_code=str(buffer.plu_code),
            card_image=buffer.card_image,
            card_size = 16
        )
        self.ids.card_place.add_widget(card)

        value = np.random.uniform(0, 5.5)
        self.ids.weight.text = f"{value:.2f} кг"
        self.ids.price_per_kg.text = f"{buffer.price_per_kg:.2f} руб."
        self.ids.total.text = f'{value * buffer.price_per_kg:.2f} руб.'

        # Планируем переход через 5 секунд
        Clock.schedule_once(self.go_to_recognizer, 8)

    def go_to_recognizer(self, dt):
        app = App.get_running_app()
        app.buffer.clear()
        app.root.current = 'RecognizerScreen'