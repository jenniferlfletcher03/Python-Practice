numbers = [3, 7, 12, 5, 20]
results = []

for n in numbers:
    if n > 10:
        results.append(n / 2)
    else:
        results.append(n + 3)

print(results)
