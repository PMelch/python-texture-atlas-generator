'''
Created on 25.11.2012

@author: peter
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
        
    def matches(self, image):
        size = image.size
        if (self.w==size[0] and self.h==size[1] ):# or \
            #(self.w==size[1] and self.h==size[0] ):
            return True
        return False
        
        
    def can_contain(self, image):
        size = image.size
        if (self.w>=size[0] and self.h>=size[1] ):# or \
        #    (self.w>=size[1] and self.h>=size[0] ):
            return True
        return False

class Node(object):
    def __init__(self, x,y,w,h):
        self.children = None
        self.rect = Rect(x,y,w,h)
        self.texture = None

    
    def insert(self, image):
        # are we a branch?
        if self.children:
            newnode = self.children[0].insert(image)
            if newnode:
                return newnode
            return self.children[1].insert(image)
        
        # already texture there?
        if self.texture:
            return None

        # this node too small?
        if not self.rect.can_contain(image):
            return None
        
        if self.rect.matches(image):
            return self
        
        
        dw = self.rect.w - image.size[0]
        dh = self.rect.h - image.size[1]
        
        r = self.rect
        if dw > dh:
            self.children = [Node(r.x, r.y, image.size[0], r.h), \
                             Node(r.x+image.size[0], r.y, r.w-image.size[0], r.h)]
        else:
            self.children = [Node(r.x, r.y, r.w, image.size[1]), \
                             Node(r.x, r.y+image.size[1], r.w, r.h-image.size[1])]
        
        return self.children[0].insert(image)

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
        pass
    
    def collect(self, root_folder):
        self._root_folder = root_folder
        self._groups = dict()
        for folder, _, filenames in os.walk(root_folder):
            filenames = [os.path.join(os.path.relpath(folder, self._root_folder), fn) for fn in filenames if os.path.splitext(os.path.join(folder, fn))[1].lower() in Generator.IMAGE_TYPES]
            if filenames:
                self._groups[folder] = filenames
            
    def create(self, texSize, outfolder):
        
        for group, images in self._groups.items():            
            atlas_number = 0
            images_scheduled = images            
            while True:
                self._root = Node(0,0,texSize, texSize)
                next_scheduled = []
                print "group",group
                print "pass:",(atlas_number+1)
                for imagepath in images_scheduled:
                    image = Image.open(os.path.join(self._root_folder, imagepath))
                    size = image.size
                    node = self._root.insert(image)
                    if node:
                        node.texture = os.path.join(self._root_folder, imagepath)
                    else:
                        next_scheduled.append(imagepath)
                        
                if images_scheduled == next_scheduled:
                    for imagepath in images_scheduled:
                        print "cannot fit in",imagepath
                    break
                                                
                image = Image.new("RGBA", (texSize, texSize))
                self._root.render(image)
                outpath = os.path.join(outfolder, group, "atlas%02d.png" % atlas_number)
                try:    os.makedirs(os.path.dirname(outpath))
                except: pass
                image.save(outpath, optimize=True)
                
                images_scheduled = next_scheduled
                atlas_number += 1
                

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
    g.create(2048, outfolder)
