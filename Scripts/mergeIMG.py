import os
import glob 
import piexif
import shutil

path = os.getcwd()
pathIMG = os.path.join(path,'image')
pathOut = os.path.join(path,'Output')
if not os.path.exists(pathOut):
	os.makedirs(pathOut)

listOut = glob.glob(os.path.join(pathOut,'*.jpg'))
for IMG in listOut:
	print '----------Image--------------'
	exif_dict = piexif.load(IMG)
	if 37510 in exif_dict['Exif']:
		labelRaw = exif_dict['Exif'][37510]
		labelComp = labelRaw.split("#")
		for comp in labelComp[0:(len(labelComp)-1)]:
			cla = comp.split()[0]
			
			numIMG = len(glob.glob(os.path.join(pathIMG,cla,'*.jpg')))+1
			#print os.path.join(path,cla,'*.jpg')
			nameIMG = cla+'_IMG_'+str(numIMG).zfill(5)+'.jpg'
			print nameIMG
			#print os.path.join(pathIMG,cla,nameIMG)
			shutil.copy2(IMG,os.path.join(pathIMG,cla,nameIMG))
