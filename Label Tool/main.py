    #-------------------------------------------------------------------------------
# Name:        Object bounding box label tool
# Purpose:     Label object bboxes for ImageNet Detection data
# Author:      Qiushi
# Created:     06/06/2014

#
#-------------------------------------------------------------------------------
from __future__ import division
from Tkinter import *
import tkMessageBox
from PIL import Image, ImageTk
import ttk
import os
import glob
import random
import shutil
import piexif

# colors for the bboxes
COLORS = ['red', 'blue', 'olive', 'teal', 'cyan', 'green', 'black']
# image sizes for the examples
SIZE = 256, 256

class LabelTool():
    def __init__(self, master):
        # set up the main frame
        self.parent = master
        self.parent.title("LabelTool")
        self.frame = Frame(self.parent)
        self.frame.pack(fill=BOTH, expand=1)
        self.parent.resizable(width = FALSE, height = FALSE)

        # initialize global state
        self.imageDir = ''
        self.imageList= []
        self.signImagePath = ''
        self.signImage = ''
        self.tkSignImage = None

        self.boundingLimit = 30 #minimum pixel 
        self.egDir = ''
        self.egList = []
        self.outDir = ''
        self.cur = 0
        self.total = 0
        self.category = 0
        self.flagEdit = 0
        self.imagename = ''
        self.imagepath = ''
        self.labelfilename = ''
        self.lenLableContent = 5    
        self.tkimg = None
        self.currentLabelclass = ''
        self.cla_can_temp = []
        self.classcandidate_filename = 'class.txt'

        # initialize mouse state
        self.STATE = {}
        self.STATE['click'] = 0
        self.STATE['x'], self.STATE['y'] = 0, 0

        # reference to bbox
        self.bboxIdList = []
        self.bboxId = None
        self.bboxList = []
        self.hl = None
        self.vl = None

        # ----------------- GUI stuff ---------------------
        # dir entry & load
        self.label = Label(self.frame, text = "Image Dir:")
        self.label.grid(row = 0, column = 0, sticky = E)
        self.entry = Entry(self.frame)
        self.entry.grid(row = 0, column = 1, sticky = W+E)
        self.ldBtn = Button(self.frame, text = "Load", command = self.loadDir)
        self.ldBtn.grid(row = 0, column = 2,sticky = W+E)

        # main panel for labeling
        self.mainPanel = Canvas(self.frame, cursor='tcross')
        self.mainPanel.bind("<Button-1>", self.mouseClick)
        self.mainPanel.bind("<Motion>", self.mouseMove)
        self.parent.bind("<Escape>", self.cancelBBox)  # press <Espace> to cancel current bbox
        self.parent.bind("s", self.cancelBBox)
        self.parent.bind("a", self.prevImage) # press 'a' to go backforward
        self.parent.bind("d", self.nextImage) # press 'd' to go forward
        self.mainPanel.grid(row = 1, column = 1, rowspan = 4, sticky = W+N)

        #Check button DAY OR NIGHT 
        self.nightState = StringVar()
        self.btnCheckNight = Checkbutton(self.frame,text="NIGHT",variable=self.nightState,onvalue="NIGHT",offvalue="DAY",command=self.setNightState)
        self.btnCheckNight.deselect()
        self.btnCheckNight.grid(row=2,column=2,sticky = W+E)
        self.currentNightState = self.nightState.get() 


        #show image reference to traffic sign
       

        self.signImagePanel = Canvas(self.frame,width = 100,height = 100,cursor='tcross')
        self.signImagePanel.grid(row = 3, column = 2, rowspan=1 ,sticky = W+N)

        # choose class
        self.classname = StringVar()
        self.classcandidate = ttk.Combobox(self.frame,state='readonly',textvariable=self.classname)
        self.classcandidate.grid(row=1,column=2)
        self.classcandidate.bind("<<ComboboxSelected>>",self.loadSignImage)


        if os.path.exists(self.classcandidate_filename):
        	with open(self.classcandidate_filename) as cf:
        		for line in cf.readlines():
        			# print line
        			self.cla_can_temp.append(line.strip('\n'))
        #print self.cla_can_temp
        self.classcandidate['values'] = self.cla_can_temp
        self.classcandidate.current(0)
        self.currentLabelclass = self.classcandidate.get() #init
        self.loadSignImage()
        #self.btnclass = Button(self.frame, text = 'ComfirmClass', command = self.setClass)
        #self.btnclass.grid(row=2,column=2,sticky = W+E)

        

        # showing bbox info & delete bbox
        self.lb1 = Label(self.frame, text = 'Bounding boxes:')
        # self.lb1.grid(row = 3, column = 2,  sticky = W+N)
        self.listbox = Listbox(self.frame, width = 22, height = 12)
        self.listbox.grid(row = 4, column = 2, sticky = N+S)
        self.btnDel = Button(self.frame, text = 'Delete', command = self.delBBox)
        self.btnDel.grid(row = 5, column = 2, sticky = W+E+N)
        self.btnClear = Button(self.frame, text = 'ClearAll', command = self.clearBBox)
        self.btnClear.grid(row = 6, column = 2, sticky = W+E+N)

        # control panel for image navigation
        self.ctrPanel = Frame(self.frame)
        self.ctrPanel.grid(row = 7, column = 1, columnspan = 2, sticky = W+E)
        self.prevBtn = Button(self.ctrPanel, text='<< Prev', width = 10, command = self.prevImage)
        self.prevBtn.pack(side = LEFT, padx = 5, pady = 3)
        self.nextBtn = Button(self.ctrPanel, text='Next >>', width = 10, command = self.nextImage)
        self.nextBtn.pack(side = LEFT, padx = 5, pady = 3)
        self.progLabel = Label(self.ctrPanel, text = "Progress:     /    ")
        self.progLabel.pack(side = LEFT, padx = 5)
        self.tmpLabel = Label(self.ctrPanel, text = "Go to Image No.")
        self.tmpLabel.pack(side = LEFT, padx = 5)
        self.idxEntry = Entry(self.ctrPanel, width = 5)
        self.idxEntry.pack(side = LEFT)
        self.goBtn = Button(self.ctrPanel, text = 'Go', command = self.gotoImage)
        self.goBtn.pack(side = LEFT)


        # # example pannel for illustration
        # self.egPanel = Frame(self.frame, border = 10)
        # self.egPanel.grid(row = 1, column = 0, rowspan = 5, sticky = N)
        # self.tmpLabel2 = Label(self.egPanel, text = "Examples:")
        # self.tmpLabel2.pack(side = TOP, pady = 5)
        # self.egLabels = []
        # for i in range(3):
        #     self.egLabels.append(Label(self.egPanel))
        #     self.egLabels[-1].pack(side = TOP)

        # display mouse position
        self.disp = Label(self.ctrPanel, text='')
        self.disp.pack(side = RIGHT)

        self.frame.columnconfigure(1, weight = 1)
        self.frame.rowconfigure(4, weight = 1)

        # for debugging
##        self.setImage()
##        self.loadDir()

    def loadDir(self, dbg = False):
        if not dbg:
            s = self.entry.get()
            self.parent.focus()
            self.category = int(s)
        else:
            s = r'D:\workspace\python\labelGUI'
##        if not os.path.isdir(s):
##            tkMessageBox.showerror("Error!", message = "The specified dir doesn't exist!")
##            return
        # get image list
        self.imageDir = os.path.join(r'./Images', '%03d' %(self.category))
        #print self.imageDir 
        #print self.category
        self.imageList = glob.glob(os.path.join(self.imageDir, '*.JPG'))
        #print self.imageList
        if len(self.imageList) == 0:
            print 'No .JPG images found in the specified dir!'
            return

        # default to the 1st image in the collection
        self.cur = 1
        self.total = len(self.imageList)

         # set up output dir
        

        # load example bboxes
        #self.egDir = os.path.join(r'./Examples', '%03d' %(self.category))
        # self.egDir = os.path.join(r'./Examples/demo')
        # print os.path.exists(self.egDir)
        # if not os.path.exists(self.egDir):
        #     return
        # filelist = glob.glob(os.path.join(self.egDir, '*.JPG'))
        # self.tmp = []
        # self.egList = []
        # random.shuffle(filelist)
        # for (i, f) in enumerate(filelist):
        #     if i == 3:
        #         break
        #     im = Image.open(f)
        #     r = min(SIZE[0] / im.size[0], SIZE[1] / im.size[1])
        #     new_size = int(r * im.size[0]), int(r * im.size[1])
        #     self.tmp.append(im.resize(new_size, Image.ANTIALIAS))
        #     self.egList.append(ImageTk.PhotoImage(self.tmp[-1]))
        #     self.egLabels[i].config(image = self.egList[-1], width = SIZE[0], height = SIZE[1])

        self.loadImage()
        print '%d images loaded from %s' %(self.total, s)

    def loadSignImage(self,event=None):
        # load sign image and confirm class
        
        self.setClass()
        pathDir = './Class'
        #print pathDir
        nameSignImage = self.classcandidate.get()+'_ORG_0.jpg'
        print nameSignImage
        self.signImagePath = os.path.join(pathDir,nameSignImage)
        #print self.signImagePath
        if os.path.exists(self.signImagePath):
            self.signImage = Image.open(self.signImagePath)
            self.tkSignImage = ImageTk.PhotoImage(self.signImage.resize((100,100),Image.ANTIALIAS))
            self.signImagePanel.config(width = 100, height = 100)
            self.signImagePanel.create_image(0, 0, image = self.tkSignImage, anchor=NW)
    
    def loadImage(self):
        # load image
        self.imagepath = self.imageList[self.cur - 1]
        self.img = Image.open(self.imagepath)
        self.tkimg = ImageTk.PhotoImage(self.img.resize((960,540),Image.ANTIALIAS))
        self.mainPanel.config(width = 960, height = 540)
        self.mainPanel.create_image(0, 0, image = self.tkimg, anchor=NW)
        self.progLabel.config(text = "%04d/%04d" %(self.cur, self.total))

        # load labels
        self.clearBBox()
        self.imagename = os.path.split(self.imagepath)[-1].split('.')[0]
        labelname = self.imagename + '.txt'
        self.labelfilename = os.path.join(self.outDir, labelname)
        bbox_cnt = 0
        w , h = self.img.size
        #check usercomment in exif data
        exif_dict = piexif.load(self.imagepath)
        if 37510 in exif_dict['Exif']:
            
            labelRaw = exif_dict['Exif'][37510]
            print 'Lable exist: ',labelRaw
            labelList = labelRaw.split('#')
            #print "label list : ",labelList
            for l in labelList:
                if l == "DAY":
                    self.btnCheckNight.deselect()
                    self.setNightState()
                    self.flagEdit = 1
                if l == "NIGHT":
                    self.btnCheckNight.select()
                    self.setNightState()
                    self.flagEdit = 1
                lableContent = l.split()

                # print type(lableContent)
                # print len(lableContent)
                if len(lableContent) == self.lenLableContent :
                    
                    # print 'lableContent: ',lableContent
                    # print 'Tuple l : ',tuple(lableContent)
                    self.bboxList.append(tuple(lableContent))
                    tmpId = self.mainPanel.create_rectangle(int(lableContent[1])*960/w, int(lableContent[2])*540/h, \
                                                                int(lableContent[3])*960/w, int(lableContent[4])*540/h, \
                                                                width = 2, \
                                                                outline = COLORS[(len(self.bboxList)-1) % len(COLORS)])
                    self.bboxIdList.append(tmpId)
                    self.listbox.insert(END, '%s ' %(lableContent[0]))
                    self.listbox.itemconfig(len(self.bboxIdList) - 1, fg = COLORS[(len(self.bboxIdList) - 1) % len(COLORS)])
        else:
            self.btnCheckNight.deselect()
            print '[-Not have label already-]'

        # if os.path.exists(self.labelfilename):
        #     with open(self.labelfilename) as f:
        #         for (i, line) in enumerate(f):
        #             if i == 0:
        #                 bbox_cnt = int(line.strip())
        #                 continue
        #             # tmp = [int(t.strip()) for t in line.split()]
        #             tmp = line.split()
        #             #print tmp
        #             self.bboxList.append(tuple(tmp))
        #             tmpId = self.mainPanel.create_rectangle(int(tmp[0]), int(tmp[1]), \
        #                                                     int(tmp[2]), int(tmp[3]), \
        #                                                     width = 2, \
        #                                                     outline = COLORS[(len(self.bboxList)-1) % len(COLORS)])
        #             # print tmpId
        #             self.bboxIdList.append(tmpId)
        #             self.listbox.insert(END, '%s : (%d, %d) -> (%d, %d)' %(tmp[4],int(tmp[0]), int(tmp[1]), \
        #             												  int(tmp[2]), int(tmp[3])))
        #             self.listbox.itemconfig(len(self.bboxIdList) - 1, fg = COLORS[(len(self.bboxIdList) - 1) % len(COLORS)])
    
    def moveImageToFolder(self):
        for bbox in self.bboxList:
            pathDir = os.path.join('./Images',bbox[0])
            if not os.path.exists(pathDir):
                os.makedirs(pathDir)
            
            labelList = glob.glob(os.path.join(pathDir,"*.JPG"))
            lableNumber = len(labelList)
            lableNumber+=1
            #print len(labelList)
            #print pathDir
            
            shutil.copy2(self.imagepath,pathDir)
            oldImageName = os.path.basename(self.imagepath)
            newImageName = bbox[0]+'_IMG_'+str(lableNumber).zfill(5)+'.JPG'
            #print oldImageName
            #print newImageName
            newImagePath = os.path.join(pathDir,newImageName)
            #print newImagePath
            os.rename(os.path.join(pathDir,oldImageName),os.path.join(pathDir,newImageName))






    def saveImage(self):
        self.flagEdit = 0
	self.addNightState()
        #self.moveImageToFolder()

        exif_dict = piexif.load(self.imagepath)
        labelList = []
        #print self.bboxList
        for bbox in self.bboxList:
            if len(bbox) == self.lenLableContent and type(bbox) != str:
                labelList.append(" ".join(str(x) for x in bbox))
            if bbox == 'NIGHT' or \
                bbox == 'DAY' :
                labelList.append(bbox)
        #print "label list: ",labelList
        label = "#".join(labelList)
        #print 'BBox List : ',self.bboxList    
        print 'Label new : ',label  
        exif_dict['Exif'][37510] = label 
        exif_bytes = piexif.dump(exif_dict)
        piexif.insert(exif_bytes,self.imagepath)
        # with open(self.labelfilename, 'w') as f:
        #     f.write('%d\n' %len(self.bboxList))
        #     for bbox in self.bboxList:
        #         f.write(' '.join(map(str, bbox)) + '\n')
        print 'Image No. %d saved' %(self.cur)

    def mouseClick(self, event):
        w,h = self.img.size
        if self.STATE['click'] == 0:
            self.STATE['x'], self.STATE['y'] = event.x, event.y
        else:
            x1, x2 = min(self.STATE['x'], event.x), max(self.STATE['x'], event.x)
            y1, y2 = min(self.STATE['y'], event.y), max(self.STATE['y'], event.y)
            self.disp.config(text = 'size: %d' %(x2-x1))
            if (x2-x1) >= self.boundingLimit:
                self.bboxList.append((self.currentLabelclass,int(x1*w/960), int(y1*h/540), int(x2*w/960), int(y2*h/540)))
                print self.bboxList
                self.bboxIdList.append(self.bboxId)
                self.bboxId = None
                self.listbox.insert(END,'%s : (%d, %d)->(%d, %d)' %(self.currentLabelclass,int(x1)  *w/960, int(y1)*h/540, int(x2)*w/960, int(y2)*h/540))
                self.listbox.itemconfig(len(self.bboxIdList) - 1, fg = COLORS[(len(self.bboxIdList) - 1) % len(COLORS)])
            else:
                print 'Not enough size for bounding'


        self.STATE['click'] = 1 - self.STATE['click']

    def mouseMove(self, event):
        self.disp.config(text = 'x: %d, y: %d' %(event.x, event.y))
        if self.tkimg:
            if self.hl:
                self.mainPanel.delete(self.hl)
            self.hl = self.mainPanel.create_line(0, event.y, self.tkimg.width(), event.y, width = 2)
            if self.vl:
                self.mainPanel.delete(self.vl)
            self.vl = self.mainPanel.create_line(event.x, 0, event.x, self.tkimg.height(), width = 2)
        if 1 == self.STATE['click']:
            if self.bboxId:
                self.mainPanel.delete(self.bboxId)
            self.bboxId = self.mainPanel.create_rectangle(self.STATE['x'], self.STATE['y'], \
                                                            event.x, event.y, \
                                                            width = 2, \
                                                            outline = COLORS[len(self.bboxList) % len(COLORS)])

    def cancelBBox(self, event):
        if 1 == self.STATE['click']:
            if self.bboxId:
                self.mainPanel.delete(self.bboxId)
                self.bboxId = None
                self.STATE['click'] = 0

    def delBBox(self):
        sel = self.listbox.curselection()
        if len(sel) != 1 :
            return
        idx = int(sel[0])
        self.mainPanel.delete(self.bboxIdList[idx])
        self.bboxIdList.pop(idx)
        self.bboxList.pop(idx)
        self.listbox.delete(idx)

    def clearBBox(self):
        for idx in range(len(self.bboxIdList)):
            self.mainPanel.delete(self.bboxIdList[idx])
        self.listbox.delete(0, len(self.bboxList))
        self.bboxIdList = []
        self.bboxList = []

    def prevImage(self, event = None):
        if len(self.bboxList) == 0 and self.flagEdit == 1:
            self.saveImage()
        if len(self.bboxList) > 0:
            self.saveImage()
        if self.cur > 1:
            self.cur -= 1
            self.loadImage()

    def nextImage(self, event = None):
        if len(self.bboxList) == 0 and self.flagEdit == 1:
            self.saveImage()
        if len(self.bboxList) > 0:
            
            self.saveImage()
        if self.cur < self.total:
            self.cur += 1
            self.loadImage()

    def gotoImage(self):
        idx = int(self.idxEntry.get())
        if 1 <= idx and idx <= self.total:
            self.saveImage()
            self.cur = idx
            self.loadImage()
    def addNightState(self):
        if self.bboxList[-1] != "DAY" and self.bboxList[-1] != "NIGHT":
            self.bboxList.append(self.currentNightState)
    def setNightState(self):
        self.currentNightState = self.nightState.get()
        print '[-Set State of sign: ',self.currentNightState,'-]'

    def setClass(self):
    	self.currentLabelclass = self.classcandidate.get()
    	print '[-Set label class to :',self.currentLabelclass,'-]'

##    def setImage(self, imagepath = r'test2.png'):
##        self.img = Image.open(imagepath)
##        self.tkimg = ImageTk.PhotoImage(self.img)
##        self.mainPanel.config(width = self.tkimg.width())
##        self.mainPanel.config(height = self.tkimg.height())
##        self.mainPanel.create_image(0, 0, image = self.tkimg, anchor=NW)

if __name__ == '__main__':
    root = Tk()
    tool = LabelTool(root)
    root.resizable(width =  True, height = True)
    root.mainloop()
