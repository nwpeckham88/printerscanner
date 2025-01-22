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
            "asin": item.get("asin", "Unknown ASIN")
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
        "asin": "Unknown ASIN"
    }

def generate_barcode(upc_code: str, file_path: str):
    barcode_obj = Code128(upc_code, writer=ImageWriter())
    barcode_obj.save(file_path.split('.')[0])  # Save without the extension to avoid double extension

def print_label(info: dict, printer_name: str):
    label_text = (
        f"Product: {info.get('name')}\n"
        f"Price: {info.get('price')}\n"
        f"UPC: {info.get('upc')}\n"
        f"Brand: {info.get('brand')}\n"
        f"Model: {info.get('model')}\n"
        f"Color: {info.get('color')}\n"
        f"Size: {info.get('size')}\n"
        f"Weight: {info.get('weight')}\n"
        f"Highest Price: {info.get('highest_price')}\n"
        f"EAN: {info.get('ean')}\n"
        f"ASIN: {info.get('asin')}\n"
    )
    
    # Create an image for the label
    label_image = Image.new('RGB', (400, 800), color='white')
    draw = ImageDraw.Draw(label_image)
    
    # Load a font
    try:
        font = ImageFont.truetype("arial.ttf", 20)  # Use a larger font size
    except IOError:
        font = ImageFont.load_default()  # Fallback to default font if "arial.ttf" is not available
    
    # Calculate text height
    text_width, text_height = draw.textbbox((0, 0), label_text, font=font)[2:]
    
    # Draw the text on the image, ensuring it is justified
    draw.multiline_text((10, 800 - text_height - 215), label_text, fill='black', font=font)
    
    if info.get('name') == "Unknown Product":
        # Draw a sad face if no information is found
        draw.text((150, 700), ":(", fill='black', font=font)
    else:
        # Load the barcode image
        barcode_image = Image.open("barcode.png")
        
        # Resize the barcode image to fit the bottom quarter
        barcode_image = barcode_image.resize((400, 200))
        
        # Paste the barcode image onto the label image
        label_image.paste(barcode_image, (0, 600))
    
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



