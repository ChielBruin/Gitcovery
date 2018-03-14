import matplotlib.pyplot as plt
from gitcovery import Git

'''
Create a graph that shows the number of lines in the README file on each commit it was involved in.
'''

root = Git.set_root('.')
readmeFile = root.get_file('README.md')

# History is new -> old, we need it the other way around. 
# Instead of reversing, you could also sort the list to make it chronological
history = list(reversed(readmeFile.history())) 

# Get the number of newlines in the document at each commit in the history of the file
sizes = list(map(lambda x: readmeFile.count('\n', at=x), history))


# Draw the graph
plt.plot(sizes)
plt.ylim(ymin=0)
plt.legend(['README.md'], loc='upper left')
plt.show()
