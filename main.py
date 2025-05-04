from fastapi import FastAPI
from PIL import Image
from io import BytesIO
import cv2,numpy as np,time


class asciiImg:
    def __init__(self,img=None):
        #loading the images
        self.ascii = []
        self.img = np.array(img)
        self.img = cv2.cvtColor(self.img,cv2.COLOR_BGR2GRAY)
        self.originalImg = self.img
        

        #defining tiles and shades
        self.shades = " .:-=+*#%@"
        self.tile_height = 6
        self.tile_width = 5

        #resizing the image
        terminal_width, terminal_height = 366,22
        self.aspect_ratio = self.img.shape[0]/self.img.shape[1]
        self.new_width = int(terminal_width*self.tile_width)
        self.new_height = int(self.new_width*self.aspect_ratio*0.4)

        #checking if new height is more than terminal height
        if (self.new_height/self.tile_height)>terminal_height:
            self.new_height = int(self.tile_height*terminal_height)
            self.new_width = int((self.new_height/self.aspect_ratio)*2.5)
        self.img = cv2.resize(self.img,(self.new_width,self.new_height))

        #filtercolor Map
        self.colorBook = {
            None:[255,255,255],
            "neonpink":[255,20,147],
            "neonblue":[0,255,255],
            "deeppurle":[180,0,255],
            "electiccyan":[102,255,255],
            "matrix":[0,255,65],
            "lavender":[230,230,250],
            "softsunset":[255,94,77],
            "warmpeach":[255,165,123],
            "mistyblue":[173,216,230]
        }
        
        self.loadAscii()
    
    def loadAscii(self):
        self.edges = []
        buffer = None
        for i in range(0,self.new_height,self.tile_height):
            for j in range(0,self.new_width,self.tile_width):
                tile = self.img[i:i+self.tile_height,j:j+self.tile_width]
                avg = np.average(np.reshape(tile,(1,-1)))
                index = int((avg/255)*(len(self.shades)-1))
                if buffer is not None:
                    diff = abs(buffer-index)
                    if diff>= int((len(self.shades)/6)):
                        self.edges.append((len(self.ascii)))
                buffer = index
                self.ascii.append(self.shades[index])
            self.ascii.append("\n")
    
    def render(self,filter=None,effect=None):
        #adding filter
        if filter:
            self.filter = filter.lower()
            if self.filter not in self.colorBook:
                self.filter = None
        else:
            self.filter = filter


        if not effect:
            for i in self.ascii:
                print(f"\033[38;2;{self.colorBook[self.filter][0]};{self.colorBook[self.filter][1]};{self.colorBook[self.filter][2]}m{i}\033[0m",end="")
        else:
            self.effect = effect.lower()
            newAscii = self.ascii
            if self.effect == "edges":
                for i in range(len(newAscii)):
                    if i in self.edges:
                        print(f"\033[38;2;255;0;0m{newAscii[i]}\033[0m",end="")
                    else:
                        print(f"\033[38;2;{self.colorBook[self.filter][0]};{self.colorBook[self.filter][1]};{self.colorBook[self.filter][2]}m{newAscii[i]}\033[0m",end="")
            elif self.effect == "onlyedges":
                for i in range(len(newAscii)):
                    if i in self.edges:
                        print(f"\033[38;2;{self.colorBook[self.filter][0]};{self.colorBook[self.filter][1]};{self.colorBook[self.filter][2]}m{newAscii[i]}\033[0m",end="")
                    else:
                        if i == "\n":
                            print(i)
                        else:
                            print(".",end="") 

    def invertRender(self):
        invertedShades = self.shades[::-1]
        for i in range(0,self.new_height,self.tile_height):
            for j in range(0,self.new_width,self.tile_width):
                tile = self.img[i:i+self.tile_height,j:j+self.tile_width]
                avg = np.average(np.reshape(tile,(1,-1)))
                index = int((avg/255)*(len(self.shades)-1))
                print(invertedShades[index],end="")
            print()
    
    def toImg(self,filter=None):
        #resizing the image
        terminal_width, terminal_height = 366,22
        self.aspect_img_ratio = self.originalImg.shape[0]/self.originalImg.shape[1]
        self.new_img_width = int(terminal_width*self.tile_width)
        self.new_img_height = int(self.new_img_width*self.aspect_img_ratio)

        tempImg = cv2.resize(self.originalImg,(self.new_img_width,self.new_img_height))


        exportImg = np.zeros((int(self.new_img_height),int(self.new_img_width),3),dtype=np.uint8)
        for i in range(0,self.new_img_height,self.tile_height):
            for j in range(0,self.new_img_width,self.tile_width):
                tile = tempImg[i:i+self.tile_height,j:j+self.tile_width]
                avg = np.average(np.reshape(tile,(1,-1)))
                index = int((avg/255)*(len(self.shades)-1))
                cv2.putText(exportImg,self.shades[index],(j,i),1,1,self.colorBook[filter],1,cv2.LINE_AA)
        exportImg = Image.fromarray(exportImg)
        buffer = BytesIO()
        exportImg.save(buffer, format="PNG")
        buffer.seek(0)
        return buffer
           
    def __repr__(self):
        self.render()
        return ""




app = FastAPI()

from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from fastapi import UploadFile
from fastapi.responses import StreamingResponse
from typing import Optional

@app.post("/upload")
async def endpoint(uploaded_file:UploadFile,filter: Optional[str] = None):
    if uploaded_file.content_type in ["image/png", "image/jpeg", "image/jpg", "image/webp"]:
        uploaded_file = await uploaded_file.read()
        image = Image.open(BytesIO(uploaded_file))
        img = asciiImg(image)
        return StreamingResponse(img.toImg(filter.lower() if filter else None),media_type="image/png")
        
        


