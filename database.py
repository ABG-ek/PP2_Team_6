from peewee import *
import numpy as np

db = SqliteDatabase('assets/database.db')


class BaseModel(Model):
    class Meta:
        database = db


class Product(BaseModel):
    title = CharField(unique=True)
    plu_code = IntegerField(unique=True)
    price_per_kg = FloatField()
    card_image = CharField()
    mean_embedding = BlobField()
    count = IntegerField(default=0)

    def get_vector(self) -> np.ndarray:
        if self.mean_embedding:
            return np.frombuffer(self.mean_embedding, dtype=np.float32)
        return None

    def update_with(self, new_vec: np.ndarray, weight: int = 1):
        """
        Обновляет средний эмбеддинг с учётом веса (количества новых векторов).
        """
        if self.count == 0:
            updated = new_vec
            new_count = weight
        else:
            current = self.get_vector()
            total = self.count + weight
            updated = (current * self.count + new_vec * weight) / total
            new_count = total

        self.mean_embedding = updated.astype(np.float32).tobytes()
        self.count = new_count
        self.save()


def initialize_db():
    db.connect()
    db.create_tables([Product])
    print("✔ База и таблицы инициализированы.")
