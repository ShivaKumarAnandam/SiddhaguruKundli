import os
from PIL import Image, ImageOps

source_path = r'D:\gocharaUPDATED\SiddhaguruKundliUI\Water mark logo_NEW (1).png'
res_path = r'D:\gocharaUPDATED\SiddhaguruKundliUI\android\app\src\main\res'

densities = {
    'mdpi': 1.0,
    'hdpi': 1.5,
    'xhdpi': 2.0,
    'xxhdpi': 3.0,
    'xxxhdpi': 4.0
}

def create_icon_with_background(source_img, target_size, logo_size, background_color=(255, 255, 255, 255), is_round=False):
    # Resize the logo to fit the target logo size
    logo = source_img.copy()
    logo.thumbnail((logo_size, logo_size), Image.LANCZOS)
    
    # Create the background canvas
    # Use RGBA for transparency if needed, but for legacy icons, we usually want filled white
    canvas = Image.new('RGBA', (target_size, target_size), background_color)
    
    # Center the logo
    pos = ( (target_size - logo.width) // 2, (target_size - logo.height) // 2 )
    canvas.paste(logo, pos, logo)
    
    if is_round:
        # Create a circular mask
        mask = Image.new('L', (target_size, target_size), 0)
        from PIL import ImageDraw
        draw = ImageDraw.Draw(mask)
        draw.ellipse((0, 0, target_size - 1, target_size - 1), fill=255)
        # Apply mask
        output = Image.new('RGBA', (target_size, target_size), (255, 255, 255, 0))
        output.paste(canvas, (0, 0), mask)
        return output
    
    return canvas

def create_adaptive_foreground(source_img, target_size, logo_size):
    # Adaptive foreground is just the logo centered on a transparent canvas of 108dp size
    logo = source_img.copy()
    logo.thumbnail((logo_size, logo_size), Image.LANCZOS)
    
    canvas = Image.new('RGBA', (target_size, target_size), (255, 255, 255, 0))
    pos = ( (target_size - logo.width) // 2, (target_size - logo.height) // 2 )
    canvas.paste(logo, pos, logo)
    return canvas

def process():
    if not os.path.exists(source_path):
        print(f"Error: Source file not found at {source_path}")
        return

    source_img = Image.open(source_path).convert("RGBA")
    
    for density, scale in densities.items():
        dir_name = f'mipmap-{density}'
        target_dir = os.path.join(res_path, dir_name)
        if not os.path.exists(target_dir):
            os.makedirs(target_dir)
            print(f"Created directory {target_dir}")

        # Legacy Icon (48dp base)
        target_48 = int(48 * scale)
        logo_48 = int(36 * scale) # 75% for legacy
        
        # Round Icon (48dp base)
        
        # Adaptive Foreground (108dp base)
        target_108 = int(108 * scale)
        logo_108 = int(72 * scale) # 66.6% safe zone

        # 1. ic_launcher.png (centered on white background)
        ic_launcher = create_icon_with_background(source_img, target_48, logo_48, background_color=(255, 255, 255, 255))
        ic_launcher.save(os.path.join(target_dir, 'ic_launcher.png'))

        # 2. ic_launcher_round.png (centered on white circle)
        ic_round = create_icon_with_background(source_img, target_48, logo_48, background_color=(255, 255, 255, 255), is_round=True)
        ic_round.save(os.path.join(target_dir, 'ic_launcher_round.png'))

        # 3. ic_launcher_foreground.png (transparent background)
        ic_foreground = create_adaptive_foreground(source_img, target_108, logo_108)
        ic_foreground.save(os.path.join(target_dir, 'ic_launcher_foreground.png'))
        
        print(f"Generated icons for {density}")

if __name__ == "__main__":
    process()
