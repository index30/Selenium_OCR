# Get map info
## Must Check Your Chrome version
import chromedriver_binary
import selenium
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options

## OCR
import pyocr
import pyocr.builders

import cv2
import numpy as np
from pathlib import Path
from PIL import Image
from skimage.io import imread, imsave
import sys
import time


def open_selenium_driver(url_str: str):
    '''Open driver for selenium
    # Argument
    url_str:    The url which you want to access
    
    # Return
    driver:     selenium's driver for Chrome
    '''
    options = Options()
    options.add_argument('--headless')
    driver = webdriver.Chrome(options=options)
    driver.get(url_str)
    return driver

def take_screen_shot(driver, save_ss_path, time_interval=10):
    '''Take screen shot in the operation of selenium
    # Arguments
    driver:         selenium's driver for Chrome
    save_ss_path:   The path you want to save screenshot(Str or Path)
    time_interval:  When you take screen shot, page's trainsition is too late.
                    So we set time interval for the transition. 
    '''
    save_ss_path = Path(save_ss_path)
    time.sleep(time_interval)
    driver.save_screenshot(save_ss_path.as_posix())
    driver.quit()

def crop_img(target_img, crop_ind):
    '''The process of cropping image
    # Arguments
    target_img:     The target image for cropping
    crop_ind:       The pair of index for cropping
    '''
    r_slice = crop_ind[0]
    c_slice = crop_ind[1]
    target_img = target_img[r_slice[0]:r_slice[1],
                            c_slice[0]:c_slice[1]]
    cropped_img_path = Path(target_img_path.parent,
                            "{0}_cropped{1}".format(target_img_path.stem, 
                                                    target_img_path.suffix))
    imsave(target_img_path, target_img)

def awake_pyocr():
    '''Start pyocr
    # Returns
    tool:   OCR tool
    '''
    tools = pyocr.get_available_tools()
    if len(tools) == 0:
        print("No OCR tool found")
        sys.exit(1)
    tool = tools[0]
    return tool

def execute_OCR(OCR_tool, 
                target_img_path,
                OCR_image_rate=2,
                font_size=12,
                margin = 6):
    '''Main Code
    # Arguments
        OCR_tool:           OCR tool(In this code, we use Tesseract)
        target_img_path:    The target image path(Str or Path)
        font_size:          The font size for target sentence
    '''
    target_img_path = Path(target_img_path)
    res = OCR_tool.image_to_string(
        Image.open(target_img_path.as_posix()),
        lang="jpn",
        builder=pyocr.builders.WordBoxBuilder(tesseract_layout=6)
        )

    out = cv2.imread(target_img_path.as_posix())
    out_r, out_c, _ = out.shape
    OCR_image_r_size = 2*margin+font_size
    OCR_image_c_size = int(out_c*(2.3/3))-15

    stock_arr = []
    for d in res:
        diff = np.array(d.position[1]) - np.array(d.position[0])
        if diff[1] > font_size:
            stock_arr.append(d.position[0])

    stock_arr = [sa for sa in stock_arr if sa[0] != 0 and sa[1 != 0]]
    ocr_arr = []
    for (sa_r, sa_c) in stock_arr:
        if not ocr_arr:
            ocr_arr.append((sa_r, sa_c))
        elif abs(ocr_arr[-1][1] - sa_c) > 5:
            ocr_arr.append((sa_r, sa_c))
    for (_, ocr_c) in ocr_arr:
        ocr_save_path = Path(target_img_path.parent,
                             "tmp{}.png".format(ocr_c))
        ocr_img = out[ocr_c-margin:ocr_c-margin+OCR_image_r_size,
                      15:15+OCR_image_c_size]
        imsave(ocr_save_path.as_posix(), 
               ocr_img)
        ocr_img = Image.open(ocr_save_path.as_posix())
        ocr_img = ocr_img.resize((OCR_image_c_size*OCR_image_rate, 
                                  OCR_image_r_size*OCR_image_rate))
        txt_sub = OCR_tool.image_to_string(
            ocr_img,
            lang="jpn",
            builder=pyocr.builders.TextBuilder(tesseract_layout=7)
            )
        ocr_save_path.unlink()
        print(txt_sub)

        cv2.rectangle(out, (0, ocr_c-margin), (out_r, ocr_c+12+margin), (0, 0, 255), 2)
    imsave(target_img_path, out)

if __name__ == "__main__":
    argv = sys.argv[1:]
    if len(argv) > 4:
        input_url = argv[0]
        save_img_path = Path(argv[1])
        OCR_image_rate = arrgv[2]
        font_size = argv[3]
        margin = argv[4]
    elif len(argv) > 0:
        input_url = argv[0]
        save_img_path = Path("./result_OCR.png")
        OCR_image_rate=2,
        font_size=12,
        margin = 6
    else:    
        # Take Screenshot
        input_url = 'https://www.google.com/maps/search/%E3%83%A9%E3%83%BC%E3%83%A1%E3%83%B3%E3%80%80%E8%B1%8A%E6%B4%B2/@35.6522933,139.7818462,15z/data=!3m1!4b1?hl=ja'
        save_img_path = Path("./result_OCR.png")
        OCR_image_rate=2,
        font_size=12,
        margin = 6
        
    driver = open_selenium_driver(input_url)
    take_screen_shot(driver, save_img_path)

    # Crop Image
    target_img_path = Path(save_img_path)
    target_img = imread(save_img_path)
    imsave("result_overall.png", target_img)
    r, c, _ = target_img.shape
    crop_img(target_img, [(50, r), (0, (c//3))])

    ocr_tool = awake_pyocr()
    execute_OCR(ocr_tool, save_img_path)