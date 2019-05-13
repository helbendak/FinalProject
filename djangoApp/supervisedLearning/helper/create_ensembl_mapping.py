import pickle

i = 0
ensembl_to_name = {}
name_to_ensembl = {}
with open('mart_export.txt') as f:
    line = f.readline()
    print(line)
    while line:
        if i > 0:
            line = line.strip('\n')
            pair = line.split(',')
            ensembl_to_name[pair[0]] = pair[1]
            name_to_ensembl[pair[1]] = pair[0]
        line = f.readline()
        i += 1

with open('ensembl_to_name', 'wb') as f:
    pickle.dump(ensembl_to_name, f)

with open('name_to_ensembl', 'wb') as f:
    pickle.dump(name_to_ensembl, f)

print(ensembl_to_name['ENSG00000000003'])
