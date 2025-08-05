-----------------------------------------------------------------------------

init и .py файлы это кастомная нода для сборки спрайтлиста, и экспорта в нативном для godot .tres формате	

.json файл - это workflow для comfyui

-----------------------------------------------------------------------------

для запуска workflow нужно также установить следующие ноды в comfy ui manager:

1.ComfyUI_IPAdapter_plus

2.comfyui_controlnet_aux

3.ComfyUI-AnimateDiff-Evolved

4.ComfyUI Inspire Pack

5.ComfyUI ArtVenture

6.WAS Node Suite (Revised)

-----------------------------------------------------------------------------

Модели с которыми я запускал workflow:

sd_xl_base_1.0.safetensors

comfyanonymous/flux_text_encoders - t5xxl (fp16)

Comfy-Org/clip_l

Comfy-Org/clip_g

SDXL-controlnet: OpenPose (v2)

ViT-B SAM model

mm_sd_v15_v2.ckpt

mm_sdxl_v10_beta.ckpt

ip-adapter-plus_sd15.safetensors

ip-adapter-plus_sdxl_vit-h.safetensors

ip-adapter-plus-face_sdxl_vit-h.safetensors

-----------------------------------------------------------------------------

На вход подаются исходные изображения с покадровой анимацией для извлечение скелетной позы 

Затем модель создает спрайт по промпту, и этот спрайт анимируется по извлечённым скелетным позам

На выходе получается спрайтлист в формате png и .tres файл для импорта в godot.
