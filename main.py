from gitfs import Git


folder = Git.setRoot('/home/chiel/Documents/gitcover')
print(folder.history()[0].pr())
print(len(folder.history()), len(folder.get('README.md').history()))
print(folder.get('README.md').status())

