import os
import shutil
import numpy as np
from PIL import Image
import torch
from torchvision import transforms
from recognizer import Recognizer
from database import Product, initialize_db

TRAIN_DIR = 'train'
TEST_DIR = 'test'
CARD_IMAGES_DIR = 'assets/card_images'
DEFAULT_PRICE = 100.0
AUGMENTATIONS_PER_IMAGE = 0

transform = transforms.Compose([
    transforms.Resize(256),
    transforms.CenterCrop(224),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406],
                         std=[0.229, 0.224, 0.225])
])

augmentation_transform = transforms.Compose([
    transforms.Resize(256),
    transforms.RandomResizedCrop(224, scale=(0.8, 1.0)),
    transforms.RandomHorizontalFlip(),
    transforms.ColorJitter(brightness=0.3, contrast=0.3, saturation=0.3),
    transforms.RandomAffine(degrees=15, translate=(0.1, 0.1)),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406],
                         std=[0.229, 0.224, 0.225])
])

def import_train_data(recognizer: Recognizer):
    print("\n📅 Импорт из train/")
    os.makedirs(CARD_IMAGES_DIR, exist_ok=True)

    existing_titles = {p.title for p in Product.select()}
    existing_plu_codes = [p.plu_code for p in Product.select()]
    next_plu = max(existing_plu_codes, default=1000) + 1

    for class_name in sorted(os.listdir(TRAIN_DIR)):
        class_path = os.path.join(TRAIN_DIR, class_name)
        if not os.path.isdir(class_path):
            continue

        if class_name in existing_titles:
            print(f"⚠️ '{class_name}' уже есть — пропуск.")
            continue

        embeddings = []
        images = [f for f in os.listdir(class_path) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
        images.sort()

        if not images:
            print(f"❌ Нет изображений в: {class_path}")
            continue

        for fname in images:
            image_path = os.path.join(class_path, fname)
            try:
                image = Image.open(image_path).convert('RGB')

                # базовая эмбеддинг без аугментации
                tensor = transform(image).unsqueeze(0).to(recognizer.device)
                with torch.no_grad():
                    emb = recognizer.model(tensor).squeeze().cpu().numpy()
                    embeddings.append(emb)

                # аугментированные эмбеддинги
                for _ in range(AUGMENTATIONS_PER_IMAGE):
                    aug_tensor = augmentation_transform(image).unsqueeze(0).to(recognizer.device)
                    with torch.no_grad():
                        aug_emb = recognizer.model(aug_tensor).squeeze().cpu().numpy()
                        embeddings.append(aug_emb)

            except Exception as e:
                print(f"⚠️ Ошибка при обработке {fname}: {e}")

        if not embeddings:
            continue

        mean_emb = np.mean(embeddings, axis=0)
        plu_code = next_plu
        next_plu += 1

        # Копируем первую картинку как карточку
        first_image = os.path.join(class_path, images[0])
        card_path = os.path.join(CARD_IMAGES_DIR, f"{plu_code}.png")
        shutil.copy(first_image, card_path)

        Product.create(
            title=class_name,
            plu_code=plu_code,
            price_per_kg=DEFAULT_PRICE,
            card_image=card_path,
            mean_embedding=mean_emb.astype(np.float32).tobytes(),
            count=len(embeddings)
        )

        print(f"✅ '{class_name}' (PLU: {plu_code}) — {len(embeddings)} эмбеддингов")

def run_test(recognizer: Recognizer):
    print("\n🧪 Тест из test/")
    recognizer.load_cache()

    total = 0
    correct_top3 = 0

    for class_name in sorted(os.listdir(TEST_DIR)):
        class_path = os.path.join(TEST_DIR, class_name)
        if not os.path.isdir(class_path):
            continue

        for fname in os.listdir(class_path):
            if not fname.lower().endswith(('.jpg', '.jpeg', '.png')):
                continue

            total += 1
            image_path = os.path.join(class_path, fname)

            try:
                image = Image.open(image_path).convert("RGB")
                tensor = transform(image).unsqueeze(0).to(recognizer.device)
                with torch.no_grad():
                    emb = recognizer.model(tensor).squeeze().cpu().numpy()

                results = recognizer.recognize(emb, top_n=3)
                predicted_titles = [res[0]['title'].strip().lower() for res in results]

                if class_name.strip().lower() in predicted_titles:
                    correct_top3 += 1
                    print(f"✅ {fname}: {class_name} в топ-3 {predicted_titles}")
                else:
                    print(f"❌ {fname}: {class_name} НЕ в топ-3 {predicted_titles}")

            except Exception as e:
                print(f"⚠️ Ошибка при тесте {fname}: {e}")

    if total > 0:
        acc = correct_top3 / total * 100
        print(f"\n🎯 Точность (топ-3): {acc:.2f}% ({correct_top3} из {total} верно)")
    else:
        print("❌ Нет тестовых изображений.")

def main():
    initialize_db()
    recognizer = Recognizer()
    import_train_data(recognizer)
    run_test(recognizer)

if __name__ == '__main__':
    main()
