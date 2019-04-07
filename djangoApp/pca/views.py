from django.shortcuts import render
from diseases.models import Sample
import pandas as pd
from sklearn.decomposition import PCA
import matplotlib.pyplot as plt
import io
import urllib
import base64


def plotPCA(request):
    if request.method == "POST":
        selected_feature = request.POST.get('selected_feature', None)
        gse = request.session['gse']
        samples = Sample.objects.filter(gse_id=gse)
        sample_to_geneCount = {}
        sample_to_selectedFeature = {}
        featureValues = []
        for sample in samples:
            sample_to_geneCount[sample.sample_id] = sample.count
            # sample_to_selectedFeature[sample.sample_id] = str(sample.attributevalue_set.filter(name='disease status')[0])
            sample_to_selectedFeature[sample.sample_id] = str(sample.attributevalue_set.filter(name=selected_feature)[0])
            featureValues.append(str(sample.attributevalue_set.filter(name=selected_feature)[0]))
        featureValues = list(set(featureValues))
        df = pd.DataFrame.from_dict(sample_to_geneCount, orient='index')
        dfValues = df.iloc[:, :].values
        selectedFeaturesdf = pd.DataFrame.from_dict(sample_to_selectedFeature, orient='index')
        selectedFeaturesdf.columns = ['disease status']
        # print(selectedFeaturesdf)
        pca = PCA(n_components=2)
        principalComponents = pca.fit_transform(dfValues)
        principalDf = pd.DataFrame(data=principalComponents,
                               columns=['principal component 1', 'principal component 2'], index=selectedFeaturesdf.index)
        # print(principalDf)
        finalDf = pd.concat([principalDf, selectedFeaturesdf], axis=1)
        # print(finalDf)
        fig = plt.figure(figsize=(8, 8))
        ax = fig.add_subplot(1, 1, 1)
        ax.set_xlabel('PC1 {0:0.1f}%'''.format(pca.explained_variance_ratio_[0] * 100), fontsize=15)
        ax.set_ylabel('PC2 {0:0.1f}%'''.format(pca.explained_variance_ratio_[1] * 100), fontsize=15)
        ax.set_title('PCA by ' + selected_feature, fontsize=20)
        # targets = ['cd', 'nonibd']
        targets = featureValues
        # colors = ['r', 'b']
        # for target, color in zip(targets, colors):
        for target in targets:
            indicesToKeep = finalDf['disease status'] == target
            ax.scatter(finalDf.loc[indicesToKeep, 'principal component 1']
                       , finalDf.loc[indicesToKeep, 'principal component 2']
                       # , c=color
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
        context = {'image': uri, 'features': features}
        return render(request, 'pcaplot.html', context)
    else:
        features = request.session['features1']
        context = {'features': features}
        return render(request, 'pcaplot.html', context)