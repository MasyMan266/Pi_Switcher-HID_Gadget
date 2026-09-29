import Pi_Gadget.LCD_1in44 as LCD_1in44
import time

from PIL import Image,ImageDraw,ImageFont,ImageColor


def main():
    LCD = LCD_1in44.LCD()


    Lcd_ScanDir = LCD_1in44.SCAN_DIR_DFT  #SCAN_DIR_DFT = D2U_L2R
    LCD.LCD_Init(Lcd_ScanDir)
    LCD.LCD_Clear()

    image = Image.new("RGB", (LCD.width, LCD.height), "WHITE")
    draw = ImageDraw.Draw(image)
    #font = ImageFont.truetype('/usr/share/fonts/truetype/freefont/FreeMonoBold.ttf', 16)

    draw.line([(0,0),(127,0)], fill = "BLUE",width = 5)
    draw.line([(127,0),(127,127)], fill = "BLUE",width = 5)
    draw.line([(127,127),(0,127)], fill = "BLUE",width = 5)
    draw.line([(0,127),(0,0)], fill = "BLUE",width = 5)

    draw.rectangle([(18,10),(110,20)],fill = "RED")


    draw.text((33, 22), 'WaveShare ', fill = "BLUE")
    draw.text((32, 36), 'Electronic ', fill = "BLUE")
    draw.text((28, 48), '1.44inch LCD ', fill = "BLUE")

    LCD.LCD_ShowImage(image,0,0)
    time.sleep(3)

    image = Image.open('/home/masyman266/1.44inch-LCD-HAT-Code/RaspberryPi/python/sky.bmp')
    LCD.LCD_ShowImage(image,0,0)
    time.sleep(3)
	#while (True):
	
#if __name__ == '__main__':
main()

#except:
#	print("except")
#	GPIO.cleanup()
