from io import StringIO, BytesIO
import os
from binascii import b2a_hex
from pdfminer.converter import TextConverter
from pdfminer.layout import LAParams
from pdfminer.pdfdocument import PDFDocument
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.pdfpage import PDFPage
from pdfminer.pdfparser import PDFParser
from pdfminer.converter import PDFPageAggregator
from pdfminer.layout import LAParams, LTTextBox, LTTextLine, LTFigure, LTImage
import hashlib
import time
import random
from PIL import Image
from PIL import ImageChops
from pdfminer.pdfcolor import LITERAL_DEVICE_CMYK
import glob

pdfImgPath = '{curDir}/static/images'
pdfImgPath = pdfImgPath.format(curDir=os.path.curdir)

class PdfReader:
    def __init__(self):
        self.pages = []
    def getDocumentByPath (self, filePath):
        fp = open(filePath, 'rb')
        parser = PDFParser(fp)
        document = PDFDocument(parser)
        return document
    def getEnumDocumentPage (self, pdfDoc):
        rsrcmgr = PDFResourceManager()
        laparams = LAParams()
        outputString = StringIO()
        device = PDFPageAggregator(rsrcmgr, laparams=laparams)
        interpreter = PDFPageInterpreter(rsrcmgr, device)
        for i, page in enumerate(PDFPage.create_pages(pdfDoc)):
            interpreter.process_page(page)
            layouts = device.get_result()
            txtData = self.dealWithPages(layouts).replace(' ', '').replace('imgsrc', 'img src').replace('\n\n', '\n')
            bookPath = '{curDir}/static/books/{bookName}'
            srcBookPath = bookPath.format(curDir=os.path.curdir, bookName='book')
            if os.path.isdir(srcBookPath) is not True:
                os.mkdir(srcBookPath)
            bookPath = os.path.join(srcBookPath, str(i + 1) + '.txt')
            self.savePageTxt(bookPath, txtData, 'w')
        self.dealWithTxt(srcBookPath)
    def dealWithPages (self, layouts):
        curPageCtx = []
        for pageLayoutObj in layouts:
            if isinstance(pageLayoutObj, LTTextBox) or isinstance(pageLayoutObj, LTTextLine):
                curPageCtx.append(pageLayoutObj.get_text())
            elif isinstance(pageLayoutObj, LTImage):
                savedFile = self.savePdfImage(pageLayoutObj)
                if savedFile:
                    curPageCtx.append('<img src="'+os.path.join(pdfImgPath, savedFile)+'" />')
            elif isinstance(pageLayoutObj, LTFigure):
                curPageCtx.append(self.dealWithPages(pageLayoutObj))
        return '\n'.join(curPageCtx)
    def savePdfImage (self, imgObj):
        result = None
        if imgObj.stream:
            imgStream = imgObj.stream.get_rawdata()
            fileExt = self.getPdfImageType(imgStream[0:4])
            if fileExt:
                fileName = ''.join([self.md5WithTime(), fileExt])
                isCMYK = (LITERAL_DEVICE_CMYK in imgObj.colorspace)
                if self.saveFile(imgStream, os.path.join(pdfImgPath, fileName), flags='wb', cmyk=isCMYK):
                    result = fileName
        return result
    def getPdfImageType (self, imgStream):
        fileType = None
        imgHex = b2a_hex(imgStream).decode()
        if imgHex.startswith('ffd8'):
            fileType = '.jpeg'
        elif imgHex == '89504e47':
            fileType = ',png'
        elif imgHex == '47494638':
            fileType = '.gif'
        elif imgHex.startswith('424d'):
            fileType = '.bmp'
        return fileType
    def saveFile (self, imgData, imgPath, flags, cmyk):
        result = False
        try:
            fileObj = open(imgPath, flags)
            if cmyk:
                ifp = BytesIO(imgData)
                i = Image.open(ifp)
                i = ImageChops.invert(i)
                i = i.convert('RGB')
                i.save(fileObj, 'JPEG')
            else:
                fileObj.write(imgData)
            fileObj.close()
            result = True
        except Exception as e:
            print(e)
            pass
        return result
    def md5WithTime (self):
        m = hashlib.md5()
        imgPath = str(random.random()) + str(round(time.time() * 1000))
        imgPath = imgPath.encode(encoding='utf-8')
        m.update(imgPath)
        return m.hexdigest()
    def savePageTxt (self, txtPath, txtData, flags):
        result = False
        try:
            fileObj = open(txtPath, flags)
            fileObj.write(txtData)
            fileObj.close()
            result = True
        except Exception as e:
            print(e)
            pass
        return result
    def dealWithTxt (self, bookPath):
        fileList = glob.glob(bookPath + '/*.txt')
        for i in fileList:
            temStrList = []
            temStr = ''
            lastLineLength = 0
            f = open(i, 'r', encoding='utf-8')
            lines = f.readlines()
            for j in range(0, len(lines)):
                item = lines[j]
                if j == 0:
                    temStr = item
                else:
                    if abs(len(item) - lastLineLength) < 6:
                        temStr += item
                    else:
                        temStrList.append(temStr.replace('\n', ''))
                        temStr = item
                lastLineLength = len(item)
                if j == len(lines) - 1:
                    temStrList.append(temStr.replace('\n', ''))
            f.close()
            fileObj = open(i, 'w')
            fileObj.write('\n'.join(temStrList))
            fileObj.close()