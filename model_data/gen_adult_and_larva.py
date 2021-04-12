categories = []
with open("origin.txt", 'r') as f:
    while True:
        line = f.readline()
        if line:
            line = line.replace('\n', '')
            adult = line + '_adult'
            larva = line + '_larva'
            egg = line + '_egg'
            pupa = line + '_pupa'
            categories.append(adult)
            categories.append(larva)
            categories.append(egg)
            categories.append(pupa)
        else:
            break

with open("all_classes.txt", 'wb') as newF:
    for each in categories:
        newF.write(each.encode('utf-8'))
        newF.write('\n'.encode('utf-8'))
