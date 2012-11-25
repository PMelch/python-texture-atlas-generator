'''
Created on 25.11.2012

@author: peter
'''

class Generator(object):


    def __init__(self):
        pass
    
    def create(self, root_folder):
        self._groups = dict()
        for folder, _, filenames in os.walk(root_folder):
            
             



if __name__ == '__main__':
    pass