import os 
import glob
import piexif
import shutil
path = os.getcwd()
pathOutput = os.path.join(path,'Output')
listFolder = glob.glob("*[0-9]")
if not os.path.exists(pathOutput):
	os.makedirs(pathOutput)
for fo in listFolder:
	listIMG = glob.glob(os.path.join(path,fo+'/*JPG'))
	for IMG in listIMG:
		exif_dict = piexif.load(IMG)
		flagConf = 0
		if 37510 in exif_dict['Exif']:
			labelRaw = exif_dict['Exif'][37510]
			labelComp = labelRaw.split("#")
			if labelComp[-1]=="DAY" or labelComp[-1]=="NIGHT":
				if len(labelComp) >= 2:
					flagConf = 1
				for comp in labelComp[0:(len(labelComp)-1)]:
					labelCoor = comp.split()
					if len(labelCoor) != 5:
						flagConf = 0
				if flagConf == 1:
					shutil.copy2(IMG,pathOutput)
					print labelRaw
listOutput = os.listdir(pathOutput)
for out in listOutput:
	#print pathOutput
	os.rename(os.path.join(pathOutput,out),os.path.join(pathOutput,'IMG_'+str(listOutput.index(out)).zfill(5)+'.jpg'))
			