a python script that will generate texture atlases out of a set of input textures.

## Usage ##

```
tagen.py [options] infolder outfolder

Options:
  -h, --help            show this help message and exit
  -v, --verbose         verbose mode
  -t TEXTURE_SIZE, --texture=TEXTURE_SIZE 
                        texture atlas size
  -g, --group_by_folder
                        if specified, create texture atlases per folder.
                        output will also get flattened.
  -f, --flat            if specified, the folder structure will NOT be re-
                        created in the output folder.
  -s SORT, --sort=SORT  sort for size: -1=descending, 1=ascending, 0=no sort.
                        default:-1
  -p PADDING, --padding=PADDING
                        padding for each sub texture.
  --fill                if set, fill padded areas with border of sub texture
                        to reduce texturing artifacts (seams)
  -c, --crop            if set, any overhead on the texture will be cropped (
                        will result in non-PO2 textures unless --power_of_two
                        is set
  -2, --power_of_2      output of a power of two texture is enforced
  -o, --optimize        if specified, atlases with a lot of empty space will
                        be re-generated using smaller dimensions
  -i INFO, --info=INFO  output format of the info file (xml, json, csv).
                        default: csv
  -n, --no_rotation     output format of the info file (xml, json, csv).
                        default: csv
```