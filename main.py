from gitfs import Git


folder = Git.setRoot('')
print(Git.getCommit('').changes())
print(folder.history()[0].changes())
print(len(folder.history()), len(folder.get('README.md').history()))
folder.forEachFile(lambda x: print(x.path))
