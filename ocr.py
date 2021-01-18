import pytesseract
from PIL import Image

def mod(im):
	#im.
	pass

def process(raw_data):
	img = Image.open(raw_data)
	text = pytesseract.image_to_string(img, config ='--psm 10')
	return text

if __name__ == '__main__':
    process("test.png")