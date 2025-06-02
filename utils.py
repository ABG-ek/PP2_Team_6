
from rembg import remove
from PIL import Image


def hex_to_kivy_color(hex_color, alpha=1.0):
    hex_color = hex_color.lstrip('#')
    if len(hex_color) != 6:
        raise ValueError("HEX цвет должен быть в формате RRGGBB")
    
    r = int(hex_color[0:2], 16) / 255.0
    g = int(hex_color[2:4], 16) / 255.0
    b = int(hex_color[4:6], 16) / 255.0
    
    return [r, g, b, alpha]


def crop_center_square(frame):
    h, w = frame.shape[:2]
    min_dim = min(h, w)
    x = (w - min_dim) // 2
    y = (h - min_dim) // 2
    return frame[y:y + min_dim, x:x + min_dim]


def chunk_list(lst, chunk_size=10):
    """Разбивает список lst на подсписки по chunk_size элементов"""
    return [lst[i:i + chunk_size] for i in range(0, len(lst), chunk_size)]


def remove_background(input_path: str, output_path: str):
    try:
        with Image.open(input_path) as img:
            img = img.convert("RGBA")
            result = remove(img)
            result.save(output_path)
        print(f"🖼 Фон успешно удалён: {output_path}")
    except Exception as e:
        print(f"❌ Ошибка при удалении фона: {e}")

