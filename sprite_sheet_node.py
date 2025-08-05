import os
import torch
import numpy as np
from PIL import Image
import json
import folder_paths

# --- УТИЛИТАРНАЯ ФУНКЦИЯ ---
def tensor_to_pil(tensor):
    """Converts a torch tensor to a list of PIL Images, preserving the alpha channel."""
    images = []
    for i in range(tensor.shape[0]):
        img_tensor = tensor[i]
        img_np = np.clip(img_tensor.cpu().numpy() * 255, 0, 255).astype(np.uint8)
        
        if img_np.shape[2] == 4:
            pil_image = Image.fromarray(img_np, 'RGBA')
        elif img_np.shape[2] == 3:
            pil_image = Image.fromarray(img_np, 'RGB')
        else:
            continue
        
        images.append(pil_image)
    return images


# ========================================================================================
#                                 НОДА №1: СОЗДАНИЕ СПРАЙТ-ЛИСТА
# ========================================================================================
class CreateSpriteSheetImageNode:
    """
    Node 1: Takes a batch of images and arranges them into a sprite sheet image.
    Outputs the image and its structural metadata for other nodes to use.
    """
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "images": ("IMAGE",),
                "column_count": ("INT", {"default": 8, "min": 1, "max": 1024}),
                "row_count": ("INT", {"default": 0, "min": 0, "max": 1024}), 
            }
        }

    RETURN_TYPES = ("IMAGE", "INT", "INT", "INT")
    RETURN_NAMES = ("sprite_sheet_image", "frame_width", "frame_height", "frame_count")
    FUNCTION = "create_sprite_sheet"
    CATEGORY = "SpriteSheet Tools"

    def create_sprite_sheet(self, images, column_count, row_count=0):
        pil_images = tensor_to_pil(images)
        if not pil_images: raise ValueError("Input images are empty.")

        frame_count = len(pil_images)
        if column_count <= 0: column_count = 1
        
        if row_count <= 0:
            row_count = (frame_count + column_count - 1) // column_count
        
        frame_width = max(img.width for img in pil_images)
        frame_height = max(img.height for img in pil_images)

        grid_image = Image.new('RGBA', (frame_width * column_count, frame_height * row_count), (0, 0, 0, 0))
        
        for i, pil_image in enumerate(pil_images):
            if i >= column_count * row_count:
                break
                
            row, col = divmod(i, column_count)
            x, y = col * frame_width, row * frame_height
            
            mask = None
            if pil_image.mode == 'RGBA':
                mask = pil_image.split()[3]
            
            grid_image.paste(pil_image, (x, y), mask)

        output_image = np.array(grid_image).astype(np.float32) / 255.0
        output_image = torch.from_numpy(output_image).unsqueeze(0)

        return (output_image, frame_width, frame_height, frame_count)


# ========================================================================================
#                                 НОДА №2: СОЗДАНИЕ .TRES ФАЙЛА
# ========================================================================================
class CreateGodotTresFileNode:
    """
    Node 2: Takes metadata about a sprite sheet and generates a Godot-native
    .tres file. This node does not process images, only data.
    """
    OUTPUT_NODE = True

    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "frame_width": ("INT", {"default": 256, "min": 1}),
                "frame_height": ("INT", {"default": 256, "min": 1}),
                "frame_count": ("INT", {"default": 12, "min": 1}),
                "column_count": ("INT", {"default": 8, "min": 1}),
                "filename_prefix": ("STRING", {"default": "spritesheet"}),
                "save_directory_path": ("STRING", {"default": "output", "multiline": False}),
                "number_padding": ("INT", {"default": 1, "min": 1, "max": 8}),
            }
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("tres_file_path",)
    FUNCTION = "create_tres_file"
    CATEGORY = "SpriteSheet Tools"

    def generate_godot_tres_content(self, image_filename, frame_width, frame_height, frame_count, column_count):
        """Generates the text content for a Godot .tres file."""
        image_resource_id = f"1_{os.urandom(5).hex()}"
        
        tres_content = f'[gd_resource type="SpriteFrames" load_steps={frame_count + 2} format=3 uid="uid://{os.urandom(12).hex()}"]\n\n'
        tres_content += f'[ext_resource type="Texture2D" uid="uid://{os.urandom(12).hex()}" path="{image_filename}" id="{image_resource_id}"]\n\n'

        sub_resources = ""
        for i in range(frame_count):
            row, col = divmod(i, column_count)
            x, y = col * frame_width, row * frame_height
            sub_resources += f'[sub_resource type="AtlasTexture" id="AtlasTexture_{i+1}"]\n'
            sub_resources += f'atlas = ExtResource("{image_resource_id}")\n'
            sub_resources += f'region = Rect2({x}, {y}, {frame_width}, {frame_height})\n\n'
        
        tres_content += sub_resources
        tres_content += "[resource]\n"
        tres_content += 'animations = [{\n"frames": [ '
        
        frame_list = [f'{{ "duration": 1.0, "texture": SubResource("AtlasTexture_{i+1}") }}' for i in range(frame_count)]
        
        tres_content += ", ".join(frame_list)
        tres_content += ' ],\n"loop": true,\n"name": &"default",\n"speed": 5.0\n}]'
        
        return tres_content

    def create_tres_file(self, frame_width, frame_height, frame_count, column_count, filename_prefix, save_directory_path, number_padding):
        user_path = save_directory_path.strip()
        target_dir = os.path.join(folder_paths.get_base_path(), user_path) if not os.path.isabs(user_path) else user_path
        os.makedirs(target_dir, exist_ok=True)
        
        i = 1
        while True:
            # Формат имени, как у Image Save: prefix_00001.png
            # f-строка {:0{padding}} означает "форматировать число i с ведущими нулями до длины padding"
            base_name = f"{filename_prefix}_{i:0{number_padding}}"
            
            tres_filename = f"{base_name}.tres"
            full_tres_path = os.path.join(target_dir, tres_filename)
            
            if not os.path.exists(full_tres_path):
                break
            i += 1
        
        image_filename = f"{base_name}.png"
        
        tres_content = self.generate_godot_tres_content(image_filename, frame_width, frame_height, frame_count, column_count)
        
        with open(full_tres_path, 'w', encoding='utf-8') as f:
            f.write(tres_content)
        
        print(f"Saved Godot resource to: {full_tres_path}")
        return (full_tres_path,)


# ========================================================================================
#                                 РЕГИСТРАЦИЯ ОБЕИХ НОД
# ========================================================================================
NODE_CLASS_MAPPINGS = {
    "CreateSpriteSheetImageNode": CreateSpriteSheetImageNode,
    "CreateGodotTresFileNode": CreateGodotTresFileNode,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "CreateSpriteSheetImageNode": "Create SpriteSheet Image",
    "CreateGodotTresFileNode": "Create Godot .tres File",
}