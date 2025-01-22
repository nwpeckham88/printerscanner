import sys
import requests
import subprocess
from barcode import Code128
from barcode.writer import ImageWriter
import cups
from PIL import Image, ImageDraw, ImageFont

def fetch_upc_data(upc_code: str):
    url = f'https://api.upcitemdb.com/prod/trial/lookup?upc={upc_code}'
    response = requests.get(url)
    
    if response.status_code == 400:
        print(f"Invalid UPC code: {upc_code}")
        return {
            "upc": upc_code,
            "name": "Invalid UPC",
            "price": 0.0,
            "brand": "Unknown Brand",
            "category": "Unknown Category",
            "description": "Invalid UPC code provided",
            "model": "Unknown Model",
            "color": "Unknown Color",
            "size": "Unknown Size",
            "weight": "Unknown Weight",
            "highest_price": 0.0,
            "ean": "Unknown EAN",
            "asin": "Unknown ASIN"
        }
    
    response.raise_for_status()
    upc_data = response.json()
    
    if upc_data and upc_data['items']:
        item = upc_data['items'][0]
        return {
            "upc": upc_code,
            "name": item.get("title", "Unknown Product"),
            "price": item.get("lowest_recorded_price", 0.0),
            "brand": item.get("brand", "Unknown Brand"),
            "category": item.get("category", "Unknown Category"),
            "description": item.get("description", "No description available"),
            "model": item.get("model", "Unknown Model"),
            "color": item.get("color", "Unknown Color"),
            "size": item.get("size", "Unknown Size"),
            "weight": item.get("weight", "Unknown Weight"),
            "highest_price": item.get("highest_recorded_price", 0.0),
            "ean": item.get("ean", "Unknown EAN"),
            "asin": item.get("asin", "Unknown ASIN"),
            "images": item.get("images", [])
        }
    return {
        "upc": upc_code,
        "name": "Unknown Product",
        "price": 0.0,
        "brand": "Unknown Brand",
        "category": "Unknown Category",
        "description": "No description available",
        "model": "Unknown Model",
        "color": "Unknown Color",
        "size": "Unknown Size",
        "weight": "Unknown Weight",
        "highest_price": 0.0,
        "ean": "Unknown EAN",
        "asin": "Unknown ASIN",
        "images": []
    }

def generate_barcode(upc_code: str, file_path: str):
    barcode_obj = Code128(upc_code, writer=ImageWriter())
    barcode_obj.save(file_path.split('.')[0])  # Save without the extension to avoid double extension

def print_label(info: dict, printer_name: str):
    product_name = info.get('name')
    label_text = ""
    
    if info.get('price') != 0.0:
        label_text += f"Price: {info.get('price')}\n"
    if info.get('upc') != "Unknown UPC":
        label_text += f"UPC: {info.get('upc')}\n"
    if info.get('brand') != "Unknown Brand":
        label_text += f"Brand: {info.get('brand')}\n"
    if info.get('model') != "Unknown Model":
        label_text += f"Model: {info.get('model')}\n"
    if info.get('color') != "Unknown Color":
        label_text += f"Color: {info.get('color')}\n"
    if info.get('size') != "Unknown Size":
    # Create an image for the label
    label_image = Image.new('RGB', (400, 800), color='white')
    draw = ImageDraw.Draw(label_image)
    
    # Load fonts
    try:
        font_large = ImageFont.truetype("arial.ttf", 30)  # Larger font for product name
        font = ImageFont.truetype("arial.ttf", 20)  # Regular font for other details
    except IOError:
        font_large = ImageFont.load_default()
        font = ImageFont.load_default()
    
    # Wrap text if it goes off the edge of the label
    def wrap_text(text, font, max_width):
        lines = []
        words = text.split()
        while words:
            line = ''
            while words and draw.textbbox((0, 0), line + words[0], font=font)[2] <= max_width:
                line += (words.pop(0) + ' ')
            lines.append(line)
        return '\n'.join(lines)
    
    wrapped_product_name = wrap_text(product_name, font_large, 380)  # 380 to account for padding
    wrapped_label_text = wrap_text(label_text, font, 380)  # 380 to account for padding
    
    # Calculate text height
    product_name_width, product_name_height = draw.textbbox((0, 0), wrapped_product_name, font=font_large)[2:]
    text_width, text_height = draw.textbbox((0, 0), wrapped_label_text, font=font)[2:]
    
    # Adjust label height based on text height
    label_height = product_name_height + text_height + 415  # Add some padding for the barcode, product image, and margins
    label_image = Image.new('RGB', (400, label_height), color='white')
    draw = ImageDraw.Draw(label_image)
    
    # Draw the product name centered
    product_name_x = (400 - product_name_width) // 2
    draw.multiline_text((product_name_x, 10), wrapped_product_name, fill='black', font=font_large, align="center")
    
    # Draw the text on the image, left justified
    draw.multiline_text((10, product_name_height + 20), wrapped_label_text, fill='black', font=font, align="left")
    
    # Draw product image if available
    if 'images' in info and info['images']:
        try:
            product_image_url = info['images'][0]
            product_image = Image.open(requests.get(product_image_url, stream=True).raw)
            product_image.thumbnail((380, 200), Image.LANCZOS)  # Maintain aspect ratio
            product_image_x = (400 - product_image.width) // 2
            label_image.paste(product_image, (product_image_x, product_name_height + text_height + 30))
        except Exception as e:
            print(f"Error loading product image: {e}")
    
    if info.get('name') == "Unknown Product":
        # Draw a sad face if no information is found
        draw.text((150, label_height - 100), ":(", fill='black', font=font)
    else:
        # Load the barcode image
        barcode_image = Image.open("barcode.png")
        
        # Resize the barcode image to fit the bottom quarter with margin
        barcode_image = barcode_image.resize((390, 190))
        
        # Paste the barcode image onto the label image with margin
        label_image.paste(barcode_image, (5, label_height - 195))
    
    # Save the final label image
    label_image.save("label.png")
    
    # Print the label image
    conn = cups.Connection()
    conn.printFile(printer_name, "label.png", "Label", {})

def main():
    printer_name = "Zebra_Technologies_ZTC_ZD410_203dpi_ZPL_printserver"
    print("Please scan a UPC code:")
    for line in sys.stdin:
        upc_code = line.strip()
        if not upc_code:
            continue
        print("Fetching product information...")
        product_info = fetch_upc_data(upc_code)
        generate_barcode(upc_code, "barcode.png")
        print_label(product_info, printer_name)
        print("Please scan the next UPC code:")

if __name__ == "__main__":
    main()



