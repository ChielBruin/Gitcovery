import matplotlib.pyplot as plt
from gitcovery import Git

'''
Create a graph that shows the number of lines in the README file over time.

For this we first get the commits that have changed the file.
For each commit in this history we then get the size of the file.
Lastly, these sizes are displayed in a graph.
'''

#root = Git.set_root('.')
root = Git.clone('/tmp', 'https://github.com/ChielBruin/Gitcovery.git')
readmeFile = root.get_file('README.md')

# History is new -> old, we need it the other way around. 
# Instead of reversing, you could also sort the list to make it chronological
history = list(reversed(readmeFile.history())) 

# Get the number of newlines in the document at each commit in the history of the file
fileSizes = list(map(lambda commit: readmeFile.count('\n', at=commit), history))

# Draw the graph
plt.plot(fileSizes)
plt.ylim(ymin=0)
plt.legend(['README.md'], loc='upper left')
plt.show()
