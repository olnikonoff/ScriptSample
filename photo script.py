from PIL import Image, ImageChops, ImageFilter, ImageStat, ImageOps
import glob
import numpy
import os
import sys, getopt
from functools import reduce

def simpleTrim(im):
    r, g, b = im.getpixel((0, 0))
    bgcolor = (r, g, b)
    bg = Image.new(im.mode, im.size, (255,255,255))
    offsetAdd = Image.new(im.mode, im.size, (3, 3, 3))
    diff = ImageChops.difference(im.filter(ImageFilter.MaxFilter(5)), bg)
    diff = ImageChops.subtract(diff, offsetAdd).convert("1").filter(ImageFilter.MaxFilter(5))
    bbox = diff.getbbox()
    if bbox:
        im = im.crop(bbox)
    return im
def checkSide(sideIm):
    numpyArray=numpy.asarray(sideIm)
    numpyArray=numpy.reshape(numpyArray,(1,max(numpyArray.shape)))[0]
    return lineTrace(numpyArray)
def lineTrace(binaryArray):
    MaxDashSize=10 #after this val start calculating new line
    MinLineSize=round(len(binaryArray)*0.1) # minimum Line size to saving
    dashSize=0
    lineLen=0
    lines=[]
    for x in binaryArray:
        if x:#start or cont len counter
            dashSize=0
            lineLen+=1
        else:
            dashSize+=1
            if(dashSize>MaxDashSize):
                lines.append(lineLen) if lineLen>0 else False
                lineLen=0
                dashSize = 0
    lines.append(lineLen) if lineLen > 0 else False
    return list(filter(lambda x: x > MinLineSize, lines))
def checkSides(im):
    img=simpleTrim(im)
    bwInvert=ImageChops.invert(img.convert("1").filter(ImageFilter.MinFilter()))
    leftRow=checkSide(bwInvert.crop((0,0,1,img.size[1])))
    rightRow=checkSide(bwInvert.crop((img.size[0]-1,0,img.size[0],img.size[1])))
    topRow=checkSide(bwInvert.crop((0,0,img.size[0],1)))
    bottomRow=checkSide(bwInvert.crop((0,img.size[1]-1,img.size[0],img.size[1])))
    holdMatrix=list(map(lambda x:len(x)>0,[leftRow,topRow,rightRow,bottomRow]))
    return holdMatrix

def checkSide_(sideIm):
    numpyArray=numpy.asarray(sideIm)
    numpyArray=numpy.reshape(numpyArray,(1,max(numpyArray.shape)))[0]
    binary=list(map(lambda x: True if (x > 253) else False, numpyArray))
    return lineTrace_(binary)
def lineTrace_(binaryArray):
    MaxDashSize=10 #after this val start calculating new line
    MinLineSize=5 # minimum Line size to saving
    dashSize=0
    lineLen=0
    lines=[]
    for x in binaryArray:
        if x:#start or cont len counter
            dashSize=0
            lineLen+=1
        else:
            dashSize+=1
            if(dashSize>MaxDashSize):
                lines.append(lineLen) if lineLen>0 else False
                lineLen=0
                dashSize = 0
    lines.append(lineLen) if lineLen > 0 else False
    return list(filter(lambda x: x > MinLineSize, lines))


def trim(im, holdMatrix=[False,False,False,False]):
    borderAddSize = 0.3
    bg=Image.new(im.mode, im.size, (255,255,255))
    offsetAdd = Image.new(im.mode, im.size, (35,35,35))
    diff = ImageChops.difference(im.filter(ImageFilter.MaxFilter(5)), bg)
    diff=ImageChops.subtract(diff,offsetAdd).convert("1").filter(ImageFilter.MaxFilter(5))
    bbox = diff.getbbox()# 10,10, 40 ,40
    if bbox:
        cropped = im.crop(bbox)
    else:
        offsetAdd = Image.new(im.mode, im.size, (0, 0, 0))
        diff = ImageChops.difference(im, bg)
        diff = ImageChops.subtract(diff, offsetAdd).convert("1").filter(ImageFilter.MaxFilter(5))
        bbox = diff.getbbox()
        if bbox:
            cropped = im.crop(bbox)
        else:
            cropped=im
        # 10,10, 40 ,40

    width,height=cropped.size #размер области занимаемой обхектом
    holdedSides=len(list(filter(lambda x: x, holdMatrix)))
    if(holdedSides>0):
        borderAddSize=0.1
    newSize=round(max(width,height)) #квадрат по области занимаемой объектом, с полями
    borderSize = round(max(width, height) * borderAddSize)
    whiteBG=Image.new(im.mode, (newSize+borderSize,newSize+borderSize), (255,255,255))


    XZERO=-(bbox[0])
    YZERO=-(bbox[1])
    XOffset = XZERO
    YOffset = YZERO
    xwork=0
    ywork=0

    deltaW = round((newSize - width) / 2)
    deltaH = round((newSize - height)/2)

    newXpoint=round(XOffset/2)
    newYpoint=round(YOffset/2)

    if(holdMatrix[0]==True):
        newXpoint=XZERO
        xwork += 1
    if(holdMatrix[1]==True):
        newYpoint=YZERO
        ywork += 1
    if (holdMatrix[2] == True):
        newXpoint=XZERO+deltaW*2+borderSize
        xwork += 1
    if (holdMatrix[3] == True):
        newYpoint=YZERO+deltaH*2+borderSize
        ywork += 1
    if(xwork>=2):
        newXpoint=0
        whiteBG = Image.new(im.mode, (width, width), (255, 255, 255))
        whiteBG.paste(im, (XZERO, YZERO))
        return whiteBG
    if(ywork>=2):
        newYpoint=0
        whiteBG = Image.new(im.mode, (height, height), (255, 255, 255))
        whiteBG.paste(im, (XZERO, YZERO))
        return whiteBG
    if ((ywork>=2)and(xwork>=2)):
        newXpoint = XZERO
        newYpoint = YZERO
        whiteBG = Image.new(im.mode, (min(width,height), min(width,height)), (255, 255, 255))

    if(holdedSides==0):# если это просто объект то размещаем его по центру
        newXpoint = XZERO + deltaW+round(borderSize/2)
        newYpoint = YZERO + deltaH+round(borderSize/2)

    whiteBG.paste(im, (newXpoint, newYpoint))
    return whiteBG


def isBgWhite(img):
    img=ImageOps.fit(img,(50,50),Image.BICUBIC,0,(0.5,0.5))
    bwInvert=img.convert('L')
    #bwInvert.show()
    leftRow=checkSide_(bwInvert.crop((0,0,1,img.size[1])))
    rightRow=checkSide_(bwInvert.crop((img.size[0]-1,0,img.size[0],img.size[1])))
    topRow=checkSide_(bwInvert.crop((0,0,img.size[0],1)))
    bottomRow=checkSide_(bwInvert.crop((0,img.size[1]-1,img.size[0],img.size[1])))
    sides=[leftRow, topRow, rightRow, bottomRow]
    whiteSides=0
    for side in sides:
        try:
            if(reduce(lambda x,y: x+y, side)==50):
                whiteSides+=1
        except:
            continue
    return whiteSides>=1

   # r, g, b = im.getpixel((0, 0))

def trimAndQuad():
    return True

def checkSize(size,im):
    if (max(im.size[0], im.size[1]) > size):
        im=ImageOps.fit(im, (size, size), Image.BICUBIC, 0, (0.5, 0.5))
    return im

def saveJPG(img, filename, dirname,folderName="processed"):
    img=img.convert('RGB')
    path=os.path.join(makeDir(os.path.join("/".join(dirname.split("/")[:-1]),folderName)),filename+".jpg")
    img.save(path,"JPEG")
    img.close()

def makeDir(dirname):
    try:
        os.mkdir(dirname)
        return dirname
    except OSError:
        return dirname


def processImage(img,outDir,filename):
    if(isBgWhite(img)):
        holdMatrix = checkSides(img)
        sidesLock=len(list(filter(lambda x: x, holdMatrix)))
        if(sidesLock>3):
            return saveJPG(img,filename,outDir,"Custom") #CustomLook
        else:
            trimmedPhoto=trim(img,holdMatrix)
            sizedPhoto=checkSize(1500,trimmedPhoto)
            if(sidesLock==0):
                return saveJPG(sizedPhoto,filename,outDir,"Good")
            else:
                convertedMatrix=reduce(lambda x,y:"{}{}".format(x,y),list(map(lambda x:1 if x else 0,holdMatrix)))
                return saveJPG(sizedPhoto,filename+"__SIDES"+convertedMatrix,outDir,"Sides") #Save To sides photo with __SIDES0000 matrix

    else:
        return saveJPG(img,filename,outDir,"NotWhiteBackground") #NoWhiteBG



def run(root,outDir):
    files = []
    filesPNG = glob.glob(root+'/*.png')
    filesGIF = glob.glob(root+'/*.gif')
    filesJPG = glob.glob(root+'/*.jpg')

    files.extend(filesJPG)
    files.extend(filesGIF)
    files.extend(filesPNG)

    for file in files:
        img=Image.open(file)
        if (img.mode == "RGBA"):
            whiteBG = Image.new("RGBA", (img.size[0], img.size[1]), (255, 255, 255, 0))
            composite = Image.composite(img, whiteBG, img)
            img = composite.convert("RGB")

        processImage(img.convert('RGB').convert('RGB'),outDir,os.path.basename(file)[:-4])
        try:
            os.remove(file)
        except:
            print("NOTREMOVED: "+file)

def main(argv=["S:/ADVANCEMENT/Дизайн/watched/PhotoSort_IN/","S:/ADVANCEMENT/Дизайн/watched/PhotoSort_OUT/"]):
    rootFolder = argv[0]
    outFolder = argv[1]
    inDir = 'S:/ADVANCEMENT/Дизайн/watched/PhotoProcessing/IN/whiteBgCropToQuad/'
    outRoot = 'S:/ADVANCEMENT/Дизайн/watched/PhotoProcessing/OUT/'
    run(rootFolder,outFolder)
    #processImage(Image.open("PassID_1-01.jpg").convert('RGB'))
if __name__ == "__main__":
   main(sys.argv[1:])
