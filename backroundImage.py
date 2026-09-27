from PIL import Image, ImageDraw

img = Image.new("RGBA", (128, 128), (255, 255, 255, 0)) # Create a new image with RGBA mode and transparent background

draw = ImageDraw.Draw(img) 

draw.rectangle([(14, 8), (112, 80)], fill="Black", outline=None) # Draw a black rectangle on the image

img.save("background.png")
print("saved background.png")
