from gitcovery import Git


folder = Git.setRoot('/home/chiel/Documents/gitcovery')
print(folder.get('README.md').status())
print(folder.get('README.md'))
print(folder.history()[0].changes())
print(len(folder.history()), len(folder.get('README.md').history()))
folder.forEachFile(lambda x: print(x.path))
