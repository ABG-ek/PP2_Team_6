import numpy as np
import torch
import torchvision.transforms as transforms
from torchvision.models import efficientnet_b0, EfficientNet_B0_Weights
from PIL import Image
from torchvision.models import efficientnet_b2, EfficientNet_B2_Weights

from database import *


class Recognizer:
    def __init__(self, device="cpu"):
        self.device = device
        self.model = self._load_model()
        self.cache = []
        self.load_cache()

    

    def _load_model(self):
        weights = EfficientNet_B2_Weights.IMAGENET1K_V1
        model = efficientnet_b2(weights=weights)
        model.classifier = torch.nn.Identity()
        model.eval()
        return model.to(self.device)

    def extract_embedding(self, image_path: str) -> np.ndarray:
        image = Image.open(image_path).convert('RGB')
        transform = transforms.Compose([
            transforms.Resize(256),
            transforms.CenterCrop(224),
            transforms.ToTensor(),
            transforms.Normalize(
                mean=[0.485, 0.456, 0.406],
                std=[0.229, 0.224, 0.225]
            )
        ])
        tensor = transform(image).unsqueeze(0).to(self.device)
        with torch.no_grad():
            return self.model(tensor).squeeze().cpu().numpy()

    def cosine_similarity(self, a: np.ndarray, b: np.ndarray) -> float:
        if a is None or b is None:
            return -1.0  # минимальная схожесть
        return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))

    def load_cache(self):
        """Полностью перезагружает кэш из базы данных."""
        self.cache.clear()
        for product in Product.select().where(Product.count > 0):
            self.cache.append({
                "id": product.id,
                "title": product.title,
                "plu_code": product.plu_code,
                "price_per_kg": product.price_per_kg,
                "card_image": product.card_image,
                "embedding": product.get_vector()
            })
        print(f"🧠 Загружено товаров в кэш: {len(self.cache)}")
        for p in self.cache:
            print(f"{p['title']} → embedding: {p['embedding'][:5] if p['embedding'] is not None else '❌ Нет эмбеддинга'}")

    def recognize(self, embedding: np.ndarray, top_n=3):
        scores = []
        for prod in self.cache:
            db_vector = prod["embedding"]
            if db_vector is None:
                continue  # Пропускаем товары без вектора

            sim = self.cosine_similarity(embedding, db_vector)
            scores.append((prod, sim))

        return sorted(scores, key=lambda x: x[1], reverse=True)[:top_n]

    def extract_embedding_from_array(self, image_array: np.ndarray) -> np.ndarray:
        """
        Принимает изображение в формате NumPy (HWC, RGB) и возвращает эмбеддинг.
        """
        image = Image.fromarray(image_array).convert('RGB')
        transform = transforms.Compose([
            transforms.Resize(256),
            transforms.CenterCrop(224),
            transforms.ToTensor(),
            transforms.Normalize(
                mean=[0.485, 0.456, 0.406],
                std=[0.229, 0.224, 0.225]
            )
        ])
        tensor = transform(image).unsqueeze(0).to(self.device)
        with torch.no_grad():
            return self.model(tensor).squeeze().cpu().numpy()