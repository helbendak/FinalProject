import rpy2.robjects.packages as rpackages
from rpy2.robjects.vectors import StrVector, FactorVector
from rpy2.robjects import r

with open('GSE57945_RPKM') as f:
    words = f.readline().split()

packageNames = ('GEOquery', 'Biobase')

utils = rpackages.importr('utils')
utils.chooseCRANmirror(ind=1)

packnames_to_install = [x for x in packageNames if not rpackages.isinstalled(x)]

if len(packnames_to_install) > 0:
    utils.install_packages(StrVector(packnames_to_install))

GEOquery = rpackages.importr('GEOquery')

Biobase = rpackages.importr('Biobase')


eList = GEOquery.getGEO('GSE57945')#GSE57945

html = Biobase.pData(eList[0])[22]
sample_ids = Biobase.pData(eList[0])[1]
#html = r.names(Biobase.pData(eList[0]))

lst = []
#print(len(html))
#print(len(words[4:]))
for i in range(len(html)):
    #lst.append((html.levels[html[i]-1], sample_ids[i]))
    lst.append(html.levels[html[i] - 1])
#print(lst[0:254])
#print(words[4:])
#print(all(elem in lst for elem in words[4:]))

pData = Biobase.pData(eList[0])
#print(len(pData))
for j in range (len(pData)):
    temp_list = []
    h = Biobase.pData(eList[0])[22]
    for i in range(len(h)):
        if i == 22:
            temp_list.append(h.levels[h[i]-1])
    #if all(elem in temp_list for elem in words[4:]):
        # print(h)

html2 = Biobase.pData(eList[0])[-8]
lst2 = []
for i in range(len(html)):
    lst2.append(html2[i])
lst2 = [x.lower() for x in lst2]
#print(set(lst2))

dict2 = {}
gender = Biobase.pData(eList[0])[-8]
for i in range(len(html)):
    dict2[str(html.levels[html[i] - 1])] = str(gender[i]).lower()

#print(dict2)

tt = r.names(Biobase.pData(eList[0]))
namesList = []
for t in tt:
    namesList.append(t)

##print(namesList[-8])
#print(namesList)
import re
regex = re.compile(":ch1$")
idxs = [i for i, item in enumerate(namesList) if re.search(regex, item)]
#print(idxs)

testing = Biobase.pData(eList[0])
#print(len(testing))

bigList = []
for i in range(len(testing)):
    if(type(testing[i]) == FactorVector):
        bigList.append(list(testing[i].levels))
    else:
        bigList.append(list(testing[i]))
words = words[4:]
for list in bigList:
    if all(elem in list for elem in words):
        print(bigList.index(list))
