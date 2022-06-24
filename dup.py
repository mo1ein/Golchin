with open("removeWords.txt", "r") as f:
    text = f.readlines()

text = ''.join(text).split()
text = list(dict.fromkeys(text))
text = '\n'.join(text)
print(text)
