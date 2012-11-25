'''
Created on 25.11.2012

implementation of the texture packing algorithm proposed by Jim Scott in 
http://www.blackpawn.com/texts/lightmaps/default.html


Copyright 2012 Peter Melchart

    Licensed under the Apache License, Version 2.0 (the "License");
    you may not use this file except in compliance with the License.
    You may obtain a copy of the License at
    
        http://www.apache.org/licenses/LICENSE-2.0
    
    Unless required by applicable law or agreed to in writing, software
    distributed under the License is distributed on an "AS IS" BASIS,
    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
    See the License for the specific language governing permissions and
    limitations under the License.

'''

import os
import sys
import Image

class Rect(object):
    x,y,w,h=0,0,0,0
    
    def __init__(self, x, y, w, h):
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        
    def matches(self, size):
        if (self.w==size[0] and self.h==size[1] ):# or \
            #(self.w==size[1] and self.h==size[0] ):
            return True
        return False
        
        
    def can_contain(self, size):
        if (self.w>=size[0] and self.h>=size[1] ):# or \
        #    (self.w>=size[1] and self.h>=size[0] ):
            return True
        return False

class Node(object):
    def __init__(self, x,y,w,h):
        self.children = None
        self.rect = Rect(x,y,w,h)
        self.texture = None

    
    def insert(self, size):
        # are we a branch?
        if self.children:
            newnode = self.children[0].insert(size)
            if newnode:
                return newnode
            return self.children[1].insert(size)
        
        # already texture there?
        if self.texture:
            return None

        # this node too small?
        if not self.rect.can_contain(size):
            return None
        
        if self.rect.matches(size):
            return self
        
        
        dw = self.rect.w - size[0]
        dh = self.rect.h - size[1]
        
        r = self.rect
        if dw > dh:
            self.children = [Node(r.x, r.y, size[0], r.h), \
                             Node(r.x+size[0], r.y, r.w-size[0], r.h)]
        else:
            self.children = [Node(r.x, r.y, r.w, size[1]), \
                             Node(r.x, r.y+size[1], r.w, r.h-size[1])]
        
        return self.children[0].insert(size)

    def render(self, image):
        if self.texture:
            thisimage = Image.open(self.texture)
            size = thisimage.size
            image.paste(thisimage, (self.rect.x, self.rect.y))
        
        if self.children:
            self.children[0].render(image)
            self.children[1].render(image)
        
        
    
    

class Generator(object):
    IMAGE_TYPES = [".png", ".jpg", ".jpeg"]


    def __init__(self):
        self._texture_info = dict()
        self._atlas_info = dict()
    
    def collect(self, root_folder):
        self._texture_info = dict()
        self._atlas_info = dict()
        
        self._root_folder = root_folder
        self._groups = dict()
        for folder, _, filenames in os.walk(root_folder):
            filenames = [os.path.join(folder, fn) for fn in filenames if os.path.splitext(os.path.join(folder, fn))[1].lower() in Generator.IMAGE_TYPES]
            if filenames:
                for filename in filenames:
                    image = Image.open(filename)
                    self._texture_info[filename] = dict(size=image.size)                
                self._groups[folder] = filenames
            
    def create(self, texSize, outfolder):
                
        for group, images in self._groups.items():            
            atlas_number = 1
            images_scheduled = images            
            while True:
                outpath = os.path.join(outfolder, os.path.relpath(group, self._root_folder), "atlas%02d.png" % atlas_number)
                self._atlas_info[outpath] = dict()
                
                _root = Node(0,0,texSize, texSize)
                next_scheduled = []
                print "group",group
                print "pass:",atlas_number
                for imagepath in images_scheduled:
                    size = self._texture_info[imagepath]["size"]
                    node = _root.insert(size)
                    if node:
                        node.texture = imagepath                     
                        self._texture_info[imagepath]["atlas"] = outpath
                        self._atlas_info[outpath][imagepath] = dict(rect=node.rect)
                    else:
                        next_scheduled.append(imagepath)
                        
                if images_scheduled == next_scheduled:
                    for imagepath in images_scheduled:
                        print "cannot fit in",imagepath
                    break
                                                
                image = Image.new("RGBA", (texSize, texSize))
                _root.render(image)
                
                try:    os.makedirs(os.path.dirname(outpath))
                except: pass
                image.save(outpath, optimize=True)
                       
                self.write_info_file(self._atlas_info[outpath], os.path.splitext(outpath)[0]+".info")         
                
                images_scheduled = next_scheduled
                atlas_number += 1
                
    def write_info_file(self, info, outpath):
        with open(outpath, "wt") as outfile:
            for path, entry in info.items():
                outfile.write(path)
                outfile.write(";")
                rect = entry["rect"]
                outfile.write("%d;%d;%d;%d;"%(rect.x, rect.y, rect.w, rect.h))
                outfile.write("\n")


if __name__ == '__main__':
    import optparse
    parser = optparse.OptionParser(usage="usage: %prog [options] infolder outfolder")
    parser.add_option("-v", "--verbose", dest="verbose", action="store_true", default=False, help="verbose mode")    
    options, args = parser.parse_args()
    
    try:
        infolder, outfolder = args
    except:
        parser.print_version()
        sys.exit(-1)

    g = Generator()
    g.collect(infolder)
    g.create(1024, outfolder)
