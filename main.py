from gitfs import Git


folder = Git.setRoot('')
print(folder.history()[0].pr())
print(len(folder.history()), len(folder.get('README.md').history()))
print(folder.get('README.md').status())

