from django.shortcuts import render
from diseases.models import Sample, Gene, AttributeName, AttributeTerm
import pandas as pd
from sklearn.decomposition import PCA
import matplotlib.pyplot as plt
import io
import urllib
import base64
import numpy as np


def plotPCA(request):
    if request.method == "POST":
        selected_feature = request.POST.get('selected_feature', None)
        gse = request.session['gse']
        term_chosen = request.POST.get('selected_value', None)
        term_chosen = term_chosen.split("-")
        samples = Sample.objects.filter(gse_id=gse)
        sample_to_geneCount = {}
        sample_to_selectedFeature = {}
        featureValues = []
        for sample in samples:
            sample_to_geneCount[sample.sample_id] = sample.count
            sample_to_selectedFeature[sample.sample_id] = str(sample.attributevalue_set.filter(name=selected_feature)[0])
            featureValues.append(str(sample.attributevalue_set.filter(name=selected_feature)[0]))
        featureValues = list(set(featureValues))  # TODO: Is there a better way to get these from the database?

        sample_to_geneCount_df = pd.DataFrame.from_dict(sample_to_geneCount, orient='index')
        print(sample_to_geneCount_df)
        print(sample_to_geneCount_df.columns.values)
        new_cols = []
        allgenes = Gene.objects.filter(gse_id=gse).order_by('position')

        for gene in allgenes:
            new_cols.append(gene.gene_name)
        sample_to_geneCount_df.columns = new_cols
        print(sample_to_geneCount_df)

        dfValues = sample_to_geneCount_df.iloc[:, :].values
        selectedFeaturesdf = pd.DataFrame.from_dict(sample_to_selectedFeature, orient='index')
        selectedFeaturesdf.columns = [str(selected_feature)] #['disease status']
        pca = PCA(n_components=2)
        principalComponents = pca.fit_transform(dfValues)
        principalDf = pd.DataFrame(data=principalComponents,
                               columns=['principal component 1', 'principal component 2'], index=selectedFeaturesdf.index)
        finalDf = pd.concat([principalDf, selectedFeaturesdf], axis=1)
        fig = plt.figure(figsize=(8, 8))
        ax = fig.add_subplot(1, 1, 1)
        ax.set_xlabel('PC1 {0:0.1f}%'''.format(pca.explained_variance_ratio_[0] * 100), fontsize=15)
        ax.set_ylabel('PC2 {0:0.1f}%'''.format(pca.explained_variance_ratio_[1] * 100), fontsize=15)
        ax.set_title('PCA by ' + selected_feature, fontsize=20)
        targets = featureValues
        for target in targets:
            indicesToKeep = finalDf[str(selected_feature)] == target#['disease status'] == target  # TODO: Should not be hardcoded as 'disease status'
            ax.scatter(finalDf.loc[indicesToKeep, 'principal component 1']
                       , finalDf.loc[indicesToKeep, 'principal component 2']
                       , s=50)
        ax.legend(targets)
        ax.set_xticks([0], minor=True)
        ax.xaxis.grid(True, which='minor', linestyle='--', linewidth=2)
        # fig.show()
        buf = io.BytesIO()
        fig.savefig(buf, format='png')
        buf.seek(0)
        string = base64.b64encode(buf.read())
        uri = 'data:image/png;base64,' + urllib.parse.quote(string)
        features = request.session['features1']
        term_list = []
        for feature in features:
            feature_object = AttributeName.objects.get(canonical_name=feature).id
            terms = request.session[feature]
            for term in terms:
                term_object = AttributeTerm.objects.get(canonical_term=term, attribute_name_id=feature_object)
                term_list.append(term_object)
        context = {'image': uri, 'features': features, 'terms': term_list}
        if 'submit' in request.POST:
            threshold = request.POST.get('threshold', None)
            pc = request.POST.get('pc', None)

            data = []
            indexList = []
            cols = sample_to_geneCount_df.columns.values
            cols = np.append(cols, "subtype")
            for index, row in finalDf.iterrows():
                # if row['disease status'] == 'cd':  # TODO: Should not be hardcoded
                if row[term_chosen[1]] == term_chosen[0]:
                    if row[pc] >= float(threshold):
                        d = sample_to_geneCount_df.loc[index, :].values
                        d = np.append(d, 0)
                        data.append(d)
                    else:
                        d = sample_to_geneCount_df.loc[index, :].values
                        d = np.append(d, 1)
                        data.append(d)
                    indexList.append(index)
            dfNew = pd.DataFrame(data, index=indexList, columns=cols)
            print(dfNew)
            feature_order = dfNew.columns.values[0:-1]  # TODO: Pass to next page

            # TODO: Go to Supervised Learning application and do the rest there

        if 'show' in request.POST:
            print("show")
        return render(request, 'pcaplot.html', context)
    else:
        features = request.session['features1']
        term_list = []
        for feature in features:
            feature_object = AttributeName.objects.get(canonical_name=feature).id
            terms = request.session[feature]
            for term in terms:
                term_object = AttributeTerm.objects.get(canonical_term=term, attribute_name_id=feature_object)
                term_list.append(term_object)
        context = {'features': features, 'terms': term_list}
        print(term_list)
        return render(request, 'pcaplot.html', context)
