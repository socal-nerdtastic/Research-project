#!/usr/bin/env python3

import PIL.Image
import PIL.ImageDraw
import tkinter as tk
import PIL.ImageTk
import csv
from PIL import Image
import yaml
import logging

logger = logging.getLogger()
fhandler = logging.FileHandler(filename='mylog.log', mode='a')
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
fhandler.setFormatter(formatter)
logger.addHandler(fhandler)
logger.setLevel(logging.DEBUG)
logging.basicConfig(filename='test.log', level=logging.DEBUG)
logger.propagate = False
# to prevent multiple prints

MAX_HEIGHT = 500
# height of the window (dimensions of the image)

class App(tk.Frame):
    def __init__(self, imageData, master=None):
        super().__init__(master) # python3 style

        self.clickStatus = tk.StringVar()
        self.loadedImages = dict()
        self.loadedBoxes = dict()                       # this dictionary will keep track of all the boxes drawn on the images
        self.currentDragBox = None                      # currently dragging Box
        self.master.title('Slideshow')
        fram = tk.Frame(self)
        tk.Button(fram, text="Previous Image", command=self.prev).pack(side=tk.LEFT)
        tk.Button(fram, text="  Next Image  ", command=self.next).pack(side=tk.LEFT)
        tk.Button(fram, text="  Next set  ", command=self._load_dataset).pack(side=tk.LEFT)
        tk.Button(fram, text="  Exit  ", command=self.destroy).pack(side=tk.RIGHT)
        tk.Label(fram, textvariable=self.clickStatus, font='Helvetica 18 bold').pack(side=tk.RIGHT)
        # inside or outside
        fram.pack(side=tk.TOP, fill=tk.BOTH)
        self.canvas = tk.Canvas(self)

        self.canvas.bind("<Button-1>", self.clicked_evt)

        # in order to support mouse drag to draw a box
        self.canvas.bind("<ButtonPress-1>", self.mouse_down_evt)
        self.canvas.bind("<ButtonRelease-1>", self.mouse_up_evt)
        self.canvas.bind('<Motion>', self.mouse_move_evt)

        self.dragging = False
        # when you click button, it opens event of clicked_evt
        self.canvas.pack()
        # self.pack() # by tradition this goes in the calling function, not here

        self._load_dataset(imageData)

    def _load_dataset(self, imageData=None):
        if imageData is None:
            "get data from some mystery logic"
            imageData = loadData('otherconfig.yaml')
        # drawing the image on the label
        self.imageData = imageData
        self.currentIndex = 0
        # start from 0th image
        self._load_image()

    def mouse_down_evt(self,evt):
        # record the starting position of the drag and note that dragging started
        self.dragging = True
        # imgName = self.imageData[self.currentIndex]['image_file']
        x, y = evt.x, evt.y
        # self.loadedBoxes[imgName] = [(x,y), None]
        self.currentDragBox = [(x,y), None]

    def mouse_up_evt(self, evt):
        if self.dragging:
            # if the dragging was happening then we note that it ended and log the final
            # box coordinates
            self.dragging = False
            imgName = self.imageData[self.currentIndex]['image_file']
            if imgName in self.loadedBoxes:
                p1, p2 = self.currentDragBox
                if p1 is not None and p2 is not None:
                    logging.debug(f'{imgName} box drawn at {self.loadedBoxes[imgName]}')

    def mouse_move_evt(self, evt):
        if self.dragging:
            # if the mouse is dragging on the canvas we update the ending coordinates
            # and draw the box on teh canvas accordinly
            imgName = self.imageData[self.currentIndex]['image_file']
            x, y = evt.x, evt.y
            self.currentDragBox[1] = (x, y)
            self.loadedBoxes[imgName] = self.currentDragBox
            # self.loadedBoxes[imgName][1] =
            self.show_drag_box()

    def show_drag_box(self):
        # This function will draw a box on the canvas using the saved coordinates
        imgName = self.imageData[self.currentIndex]['image_file']
        if imgName in self.loadedBoxes:
            p1, p2 = self.loadedBoxes[imgName]
            if p1 is not None and p2 is not None:
                self.canvas.delete('drag_box')
                (l, t), (r, b) = p1, p2
                self.canvas.create_rectangle(l, t, r, b, tag='drag_box', outline='red', width=2)
                self.canvas.pack(expand=1)


    def clicked_evt(self, evt):
        x, y = evt.x, evt.y
        print(f"x: {x}, y: {y}")
        imgData = self.loadedImages[self.imageData[self.currentIndex]['image_file']]
        # Loop over all the shapes till we find the one that was clicked in
        message = "Outside"
        self.canvas.delete("box")
        for shape in imgData['shapes']:
            l = int(shape['left'])
            t = int(shape['top'])
            r = int(shape['right'])
            b = int(shape['bottom'])
            if t<=y<=b and l<=x<=r:
                if shape['is_target']:
                    message = "Inside"
                # Draw the bounding box
                self.canvas.create_rectangle(l, t, r, b, tag='box')
                self.canvas.pack(expand=1)
                break # We found the clicked on shape so stop looping
        # print(message)
        logging.debug([evt.x,evt.y])
        logging.debug([message])

    def _load_image(self):
        imgName = self.imageData[self.currentIndex]['image_file']
        if imgName not in self.loadedImages:

          self.im = PIL.Image.open(self.imageData[self.currentIndex]['image_file'])

          ratio = MAX_HEIGHT/self.im.height
        # ratio divided by existing height -> to get constant amount
          height, width = int(self.im.height*ratio), int(self.im.width * ratio)
            # calculate the new h and w and then resize next
          self.canvas.config(width=width, height=height)
          self.im = self.im.resize((width, height))
          if self.im.mode == "1":
              self.img = PIL.ImageTk.BitmapImage(self.im, foreground="white")
          else:
              self.img = PIL.ImageTk.PhotoImage(self.im)
          imgData = self.loadedImages.setdefault(self.imageData[self.currentIndex]['image_file'], dict())
          imgData['image'] = self.img
          imgData['shapes'] = self.imageData[self.currentIndex]['shapes']
        # for next and previous so it loads the same image adn don't do calculations again
        self.img = self.loadedImages[self.imageData[self.currentIndex]['image_file']]['image']
        self.canvas.create_image(0, 0, anchor=tk.NW, image=self.img)
        self.show_drag_box()

    def prev(self):
        self.currentIndex = (self.currentIndex+len(self.imageData) - 1 ) % len(self.imageData)
        self._load_image()
    # here if i go to the first one and press back, goes to last, round robbin

    def next(self):
        self.currentIndex = (self.currentIndex + 1) % len(self.imageData)
        self._load_image()
    # here if i go to the last one and press next, goes to first, round robbin

def loadData(fname):
  with open(fname, mode='r') as f:
    return yaml.load(f.read(), Loader=yaml.SafeLoader)

if __name__ == "__main__":
    data = loadData('config.yaml')
    app = App(data)
    app.pack() # goes here
    app.mainloop()
