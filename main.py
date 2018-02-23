from gitfs import Git


folder = Git.setRoot('')
print(folder.a.children is folder.children)
print(folder.a.b.get('c'))
print(folder.history()[0].changes())
print(len(folder.history()), len(folder.get('README.md').history()))
print(folder.get('README.md').status())
folder.forEachFile(lambda x: print(x.path))
