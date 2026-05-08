words = ["cat", "elephant", "go", "umbrella", "hi", "python"]
results = []

for word in words:
    if len(word) > 6:
        results.append(word.upper())
    elif len(word) > 3:
        results.append(word + "!")
    else:
        results.append(word * 2)

print(results)

# Before running, try to predict the output:
# - "cat"      → length 3, so...
# - "elephant" → length 8, so...
# - "go"       → length 2, so...
# - "umbrella" → length 8, so...
# - "hi"       → length 2, so...
# - "python"   → length 6, so...
