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

    def render(self, image, padding, fill=True):
        if self.texture:
            thisimage = Image.open(self.texture)
            w,h = thisimage.size            
            rx = self.rect.x
            ry = self.rect.y
            rh = self.rect.h
            rw = self.rect.w
            image.paste(thisimage, (rx+padding, ry+padding))
            
            if fill:
                #top
                part = thisimage.crop((0,0,w,1))
                part = part.resize((w,padding))
                image.paste(part, (rx+padding,ry))

                #topleft
                part = thisimage.crop((0,0,1,1))
                part = part.resize((padding,padding))
                image.paste(part, (rx,ry))

                #topright
                part = thisimage.crop((w-1,0,w,1))
                part = part.resize((padding,padding))
                image.paste(part, (rx+rw-padding,ry))

                #bottom
                part = thisimage.crop((0,h-1,w,h))
                part = part.resize((w,padding))
                image.paste(part, (rx+padding,ry+rh-padding))

                #left
                part = thisimage.crop((0,0,1,h))
                part = part.resize((padding,h))
                image.paste(part, (rx,ry+padding))

                #bottomleft
                part = thisimage.crop((0,h-1,1,h))
                part = part.resize((padding,padding))
                image.paste(part, (rx,ry+rh-padding))

                #bottomright
                part = thisimage.crop((w-1,h-1,w,h))
                part = part.resize((padding,padding))
                image.paste(part, (rx+rw-padding,ry+rh-padding))
                
                #right
                part = thisimage.crop((w-1,0,w,h))
                part = part.resize((padding,h))
                image.paste(part, (rx+rw-padding,ry+padding))


        
        if self.children:
            self.children[0].render(image, padding, fill)
            self.children[1].render(image, padding, fill)
        
        
    
    

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

                if self._group_by_folder:
                    self._groups[folder if self._group_by_folder else ""] = filenames
                else:
                    if "" not in self._groups:
                        self._groups[""]=[]
                    self._groups[""].extend(filenames)
            
    def _image_sort_func(self, a, b):
        size1 = self._texture_info[a]["size"]
        size2 = self._texture_info[b]["size"]
        val1 = size1[0]*size1[1]
        val2 = size2[0]*size2[1]
        return cmp(val1,val2) if self._sort==1 else cmp(val2,val1)
            
    def create(self, outfolder):
        texSize = self._texture_size
        
        if self._verbose:
            print "Creating texture atlases with size:",texSize        
        atlas_number = 1
        for group, images in self._groups.items():                            
            if self._sort == 0:
                images_scheduled = images
            else:
                images_scheduled = sorted(images, cmp=lambda a,b:self._image_sort_func(a, b))
                
            while True:
                if self._flatten_output or not self._group_by_folder:
                    outpath = os.path.join(outfolder, "atlas%02d.png" % atlas_number)
                else:
                    outpath = os.path.join(outfolder, os.path.relpath(group, self._root_folder), "atlas%02d.png" % atlas_number)
                    
                self._atlas_info[outpath] = dict()
                
                _root = Node(0,0,texSize, texSize)
                next_scheduled = []
                print "group",group
                print "pass:",atlas_number
                for imagepath in images_scheduled:
                    size = self._texture_info[imagepath]["size"]
                    size = [size[0]+self._padding*2, size[1]+self._padding*2]
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
                _root.render(image, self._padding, self._fill)
                
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


    def set_options(self, options):
        self.__options = options
        self._verbose = options.verbose
        self._texture_size = options.texture_size
        self._flatten_output = options.flat
        self._group_by_folder = options.group_by_folder
        self._sort = options.sort
        self._padding = options.padding
        self._fill = options.fill

if __name__ == '__main__':
    import optparse
    parser = optparse.OptionParser(usage="usage: %prog [options] infolder outfolder")
    parser.add_option("-v", "--verbose", dest="verbose", action="store_true", default=False, help="verbose mode")
    parser.add_option("-t", "--texture", dest="texture_size", action="store", default=1024, type=int, help="texture atlas size")
    parser.add_option("-g", "--group_by_folder", dest="group_by_folder", action="store_true", default=False, help="if specified, create texture atlases per folder. output will also get flattened.")    
    parser.add_option("-f", "--flat", dest="flat", action="store_true", default=False, help="if specified, the folder structure will NOT be re-created in the output folder.")    
    parser.add_option("-s", "--sort", dest="sort", action="store", default=-1, type=int, help="sort for size: -1=descending, 1=ascending, 0=no sort. default:-1")    
    parser.add_option("-p", "--padding", dest="padding", action="store", default=0, type=int, help="padding for each sub texture.")    
    parser.add_option("", "--fill", dest="fill", action="store_true", default=False, help="if set, fill padded areas with border of sub texture to reduce texturing artifacts (seams)")    
    options, args = parser.parse_args()
    
    try:
        infolder, outfolder = args
    except:
        parser.print_version()
        sys.exit(-1)

    g = Generator()
    g.set_options(options)
    g.collect(infolder)
    g.create(outfolder)
