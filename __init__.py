from flask import Flask
from utils.pdf import PdfReader
import os
app = Flask(__name__)
pdfReader = PdfReader()

pdfDocPath = '{curDir}/upload/{pdfName}'
pdfDocPath = pdfDocPath.format(curDir=os.path.curdir, pdfName='book.pdf')
pdfDocObj = pdfReader.getDocumentByPath(pdfDocPath)
pdfReader.getEnumDocumentPage(pdfDocObj)

if __name__ == '__main__':
    app.run(debug=True)