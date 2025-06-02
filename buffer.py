import os
import shutil
import numpy as np
from database import Product
from peewee import IntegrityError


class Buffer():
    def __init__(self):
        self.title = None 
        self.plu_code = None
        self.price_per_kg = None 
        self.card_image = None 
        self.mean_embedding = None 
        self.count = None 
        self.catalog_mode = None
        self.base_embedding = None  # Оригинал из БД
        self.session_embeddings = []  # Векторы, добавленные в сессии

        self.result = []
    
    
    def clear(self):
        self.title = None 
        self.plu_code = None
        self.price_per_kg = None 
        self.card_image = None 
        self.mean_embedding = None 
        self.count = None
        self.catalog_mode = None
        self.session_count = 0
        self.base_embedding = None
        self.session_embeddings = []
        self.result = []
        print("Очистка буфера...")

    def update_embedding(self, new_embedding: np.ndarray):
        self.session_embeddings.append(new_embedding)

        if self.base_embedding is not None and self.count:
            total_count = self.count + len(self.session_embeddings)
            weighted_base = self.base_embedding * self.count
            weighted_session = np.sum(self.session_embeddings, axis=0)
            self.mean_embedding = (weighted_base + weighted_session) / total_count
        else:
            self.mean_embedding = np.mean(self.session_embeddings, axis=0)


    def load_from_db_by_plu(self, plu_code):
        product = Product.select().where(Product.plu_code == plu_code).first()
        if not product:
            print(f"❌ Продукт с PLU {plu_code} не найден.")
            return False

        self.title = product.title
        self.plu_code = product.plu_code
        self.price_per_kg = product.price_per_kg
        self.card_image = product.card_image

        self.base_embedding = product.get_vector()
        self.mean_embedding = self.base_embedding.copy()
        self.session_embeddings = []
        self.count = product.count

        print(f"📥 Буфер загружен из БД: {self.title} (PLU: {self.plu_code})")
        return True


    def delete_from_db_by_plu(self, plu_code):
        """Удаляет продукт и его изображение по PLU, при совпадении очищает буфер."""
        product = Product.select().where(Product.plu_code == plu_code).first()
        if not product:
            print(f"❌ Не найден продукт с PLU: {plu_code}")
            return False

        # Попробуем удалить изображение
        image_path = product.card_image
        if image_path and os.path.exists(image_path):
            try:
                os.remove(image_path)
                print(f"🖼 Удалено изображение: {image_path}")
            except Exception as e:
                print(f"⚠️ Ошибка при удалении изображения: {e}")
        else:
            print("⚠️ Изображение не найдено или путь пуст.")

        product.delete_instance()
        print(f"🗑 Продукт удалён: {product.title} (PLU: {plu_code})")

        if self.plu_code == plu_code:
            self.clear()

        return True


    def save_to_db(self):
        if not all([self.title, self.plu_code, self.price_per_kg]):
            print("❌ Буфер не заполнен — сохранение невозможно.")
            return

        # Подготовка путей
        dest_dir = "assets/card_images"
        os.makedirs(dest_dir, exist_ok=True)
        new_filename = f"{self.plu_code}.png"
        dest_path = os.path.join(dest_dir, new_filename)

        # Переименование и перемещение snapshot.png
        if os.path.exists("snapshot.png"):
            try:
                shutil.move("snapshot.png", dest_path)
                self.card_image = dest_path
                print(f"📷 Изображение карточки обновлено: {dest_path}")
            except Exception as e:
                print(f"⚠️ Ошибка при перемещении изображения: {e}")
        else:
            print("⚠️ Файл snapshot.png не найден. Изображение не обновлено.")

        try:
            product = Product.select().where(Product.plu_code == self.plu_code).first()

            if product:
                print(f"📝 Обновляем продукт: {product.title} (PLU: {product.plu_code})")
                product.title = self.title
                product.price_per_kg = self.price_per_kg
                product.card_image = self.card_image

                # Дообучение только если есть новые снимки
                if self.session_embeddings:
                    product.update_with(self.mean_embedding, weight=len(self.session_embeddings))
                    print(f"🧠 Дообучение завершено: добавлено {len(self.session_embeddings)} новых снимков.")
                else:
                    product.save()
                    print("✏️ Обновлены только метаданные без дообучения.")

            else:
                # Проверка на дубликат по title
                if Product.select().where(Product.title == self.title).exists():
                    print(f"❌ Название '{self.title}' уже используется другим товаром.")
                    return

                if not self.session_embeddings:
                    print("❌ Невозможно создать новый продукт без обучающих снимков.")
                    return

                print(f"➕ Создаём новый продукт: {self.title} (PLU: {self.plu_code})")
                Product.create(
                    title=self.title,
                    plu_code=self.plu_code,
                    price_per_kg=self.price_per_kg,
                    card_image=self.card_image,
                    mean_embedding=self.mean_embedding.astype(np.float32).tobytes(),
                    count=len(self.session_embeddings)
                )
                print(f"✅ Новый продукт сохранён. Снимков: {len(self.session_embeddings)}")

            # После сохранения сбрасываем session-данные
            self.base_embedding = self.mean_embedding.copy()
            self.session_embeddings = []

        except IntegrityError as e:
            print(f"❌ Ошибка сохранения в БД (уникальность): {e}")
        except Exception as e:
            print(f"❌ Непредвиденная ошибка: {e}")