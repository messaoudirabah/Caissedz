from PIL import Image
import os

def convert_png_to_ico(png_path, ico_path):
    try:
        img = Image.open(png_path)
        img.save(ico_path, format='ICO', sizes=[(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
        print(f"Successfully converted {png_path} to {ico_path}")
    except ImportError:
        print("Pillow is not installed. Please run: pip install Pillow")
    except Exception as e:
        print(f"Error converting icon: {e}")

if __name__ == "__main__":
    base_dir = os.getcwd()
    # Correct path based on user's workspace
    png_file = os.path.join(base_dir, "assets", "logo.png")
    ico_file = os.path.join(base_dir, "assets", "logo.ico")
    
    if os.path.exists(png_file):
        convert_png_to_ico(png_file, ico_file)
    else:
        print(f"File not found: {png_file}")
