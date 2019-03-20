from __future__ import division
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle  
import re

from gitcovery import Git

'''
Create an evolution matrix that shows the evolution of certain files in a git repository.
For each tag in the repository three properties of the source files are calculated.

Currently the following properties are measured:
 - Width:  Number of functions
 - Height: Average length of a function
 - Color:  The number of TODOs per KLOC

A black border is added when a file was changed since the last release.
'''

# Regexes to find functions and todos
FUNCTION_REGEX = re.compile('\s*def\s*.*\(.*\):')
TODO_REGEX = re.compile('#\s?TODO')

# The images to create
images = {
    'evolution_matrix.svg': {
        'tags': None,    # Use all
        'files': ['git.py', 'author.py', 'commit.py', 'diff.py', 'gitfs.py']
    }
}

def toHexColor(value, maxi):
    """
    Convert a value to the range green -> red, where maxi will be red.
    """
    value = value / maxi if value < maxi else 1
    rgb = (value,1-value,0)
    return '#' + "".join("%02X" % round(i*255) for i in rgb)

def getData(gitFile):
    """
    Get the measured data for the given file.
    """
    lines = gitFile.count('\n')
    todo_per_kloc = gitFile.regex_count(TODO_REGEX)/(lines/1000)

    w = gitFile.regex_count(FUNCTION_REGEX) # Number of functions
    h = lines / w if w > 0 else 0           # Lines per function
    c = toHexColor(todo_per_kloc, 5)        # TODO per KLOC
    return (w, h, c)

def addDatapoint(tag, gitFile, DATAPOINTS, FILESIZES, FILECHANGES):
    """
    Add a new datapoint for the given tag and file.
    """
    w, h, c = getData(gitFile)

    fname = gitFile.name
    if fname in FILESIZES:
        FILESIZES[fname] = (max(FILESIZES[fname][0], w), max(FILESIZES[fname][1], h))
        
        # Check if the file is changed since the last version
        if DATAPOINTS[fname]:     # If not the first datapoint
            changed = DATAPOINTS[fname][-1][1] != (w,h,c)
            if changed:
                FILECHANGES[fname].append(tag)

        DATAPOINTS[fname].append( (tag, (w,h,c)) )
    else:
        FILESIZES[fname] = (w,h)
        DATAPOINTS[fname] = [ (tag, (w,h,c)) ]
        FILECHANGES[fname] = []


def plotDataSet(fname, id, DATAPOINTS, FILESIZES, FILECHANGES, ARTISTS):
    """
    Plot the data for the given file.
    """
    dataPoints = DATAPOINTS[fname]
    maxSize = FILESIZES[fname]

    if maxSize[0] is 0 and maxSize[1] is 0:
        print('Skipping %s, as it is empty' % fname)
        return id
   
    fileTags, raw = zip(*dataPoints)
    w, h, c = zip(*raw)

    tagIndices = map(lambda x: tags.index(x), fileTags)
    w = map(lambda x: (x/maxSize[0]) if maxSize[0]>0 else 0, w)
    h = map(lambda y: (y/maxSize[1]) if maxSize[1]>0 else 0, h)
    
    artist = None
    for x, y, c, w, h in zip(tagIndices, [id]*len(fileTags), c, w, h):
        lw = 1 if tags[x] in FILECHANGES[fname] else 0
        artist = Rectangle(xy=(x+1.1-.4*w, y+1.1-.4*h), facecolor=c, width=.8*w, height=.8*h, edgecolor='black', linewidth=lw)
        ax.add_artist(artist)
    ARTISTS.append((artist, fname))
    #ax.text(len(tags) + 3, y+1, '(%dx%d) %s' % (maxSize[0], maxSize[1], fname), fontsize=12)
    ax.text(len(tags) + 3, y+1, fname, fontsize=12)
    return id + 1


print('Cloning repository and setting the root')
Git.clone('tmp', 'https://github.com/ChielBruin/Gitcovery.git')

print('Updating the repository to the latest version')
Git.checkout('master')
#root = Git.update()

for image in images:
    print('Making image %s' % image)
    
    imageData = images[image]
    DATAPOINTS = {}
    FILESIZES = {}
    FILECHANGES = {}
    ARTISTS=[]
    
    print('Getting tags')
    if imageData['tags']:
        tags = imageData['tags']
        history = list(map(lambda x: Git.get_tag(x), tags))
    else:
        history, tags = zip(*sorted(Git.get_tags_by_commit()))
    
    for tag in tags:
        print('-> %s' % tag)
        try:
            tagSourceFolder = Git.checkout(tag).gitcovery
        except IOError:
            print('Folder not present yet')
            continue

        if isinstance(imageData['files'], str):
            folderFiles = tagSourceFolder.get_folder(imageData['files']).files()
            for fname in folderFiles:
                f = folderFiles[fname]
                addDatapoint(tag, f, DATAPOINTS, FILESIZES, FILECHANGES)
        else:
            for fname in imageData['files']:
                f = tagSourceFolder.get_file(fname)
                addDatapoint(tag, f, DATAPOINTS, FILESIZES, FILECHANGES)

    print('Data loaded')
    print('Writing resuts to file')

    # Setup the figure
    fig = plt.figure(figsize=(len(tags)*.4, len(FILESIZES)*.4))
    ax = fig.add_subplot(111)
    ax.axis([0, len(tags)+2, 0, len(FILESIZES)+1])
    ax.set_aspect('equal', 'box')

    # Draw the data
    i = 0
    for fname in FILESIZES:
        i = plotDataSet(fname, i, DATAPOINTS, FILESIZES, FILECHANGES, ARTISTS)

    # Set the axis labels
    ax.set_xticks(range(len(tags)+1))
    ax.set_xticklabels([''] + list(tags), rotation=90)
    ax.set_yticks([])
    
    # Add explanation to legend
    ax.text(len(tags) + 3, i+4, '(WxH) [Filename]', fontsize=12)
    ax.text(len(tags) + 3, i+3, 'W = Number of Functions', fontsize=10)
    ax.text(len(tags) + 3, i+2, 'H = Lines per function', fontsize=10)

    # Save the figure
    fig.savefig(image, bbox_inches='tight')

    print('Done')
