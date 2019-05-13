from django.shortcuts import render, redirect
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from supervisedLearning.models import SupervisedModel
import pickle
import numpy as np
from diseases.models import Experiment, Sample, Gene
import os
from tqdm import tqdm
from sklearn.decomposition import PCA
import matplotlib.pyplot as plt
import io
import urllib
import base64

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def logisticRegression(request):
    """
    This function handles the training of a logistic regression model on a certain dataset and also extracts feature
    importance using Random Forests.
    """
    if request.method == "POST":
        request.session['test_experiment'] = request.POST.get('test_experiment', None)
        request.session['trained_model_gse'] = request.POST.get('trained_model', None)
        return redirect('/supervisedtest/')
    df = pd.read_json(request.session['dataframe'])
    feature_order = request.session['feature_order']
    gse = request.session['gse']
    X = df.iloc[:, :-1].values
    y = df.iloc[:, -1].values
    # To implement SVM, or other supervised models for that matter, one would only need to create a view
    # similar to this one, and replace the next line with the model needed from sklearn
    lr = LogisticRegression()
    lr.fit(X, y)

    rf = RandomForestClassifier(n_estimators=10000)
    rf.fit(X, y)
    if len(feature_order) < 10:
        important_features_indx = np.argpartition(rf.feature_importances_, -len(feature_order))[-len(feature_order):]
    else:
        important_features_indx = np.argpartition(rf.feature_importances_, -10)[-10:]

    important_features = []
    for indx in important_features_indx:
        important_features.append(feature_order[indx][0])

    gene_order = []
    gene_means = []
    for feature in feature_order:
        gene_order.append(feature[0])
        gene_means.append(feature[1])

    experiment = Experiment.objects.get(gse_id=gse)
    pc = request.session['pc']
    threshold = request.session['threshold']

    SupervisedModel.objects.get_or_create(experiment=experiment, model=pickle.dumps(lr), gene_order=gene_order,  gene_means=gene_means, pc=pc, threshold=threshold)

    return render(request, 'supervised.html', {'important_features': important_features, 'experiment': Experiment.objects.all(), 'models': SupervisedModel.objects.all()})


def logisticRegressionTesting(request):
    """
    This function handles testing a logistic regression model on a new dataset. This includes converting the gene
    index format as needed.
    """
    if request.method == "GET":
        request.session['test_experiment'] = request.POST.get('test_experiment', None)
        request.session['trained_model_gse'] = request.POST.get('trained_model', None)
        return render(request, 'supervised.html', {'experiment': Experiment.objects.all(), 'models': SupervisedModel.objects.all()})
    test_experiment_gse = request.POST.get('test_experiment', None)
    trained_model_gse = request.POST.get('trained_model', None)

    test_experiment = Experiment.objects.get(gse_id=test_experiment_gse)
    train_experiment = Experiment.objects.get(gse_id=trained_model_gse)

    train_gene_format = train_experiment.gene_format
    test_gene_format = test_experiment.gene_format

    model = SupervisedModel.objects.get(experiment=train_experiment)
    train_gene_order = model.gene_order
    train_gene_means = model.gene_means

    if train_gene_format == 'names' and test_gene_format == 'ensembl':
        with open(os.path.join(BASE_DIR, "supervisedLearning/helper/ensembl_to_name"), 'rb') as f:
            ensembl_to_name = pickle.load(f)

        test_samples = Sample.objects.filter(experiment=test_experiment)
        test_genes = Gene.objects.filter(experiment__exact=Experiment.objects.get(gse_id=test_experiment_gse))

        test_gene_names = []
        test_gene_position = []
        for gene in test_genes:
            ensembl_id = gene.gene_name
            try:
                if '.' in ensembl_id:
                    ensembl_id = ensembl_id.split('.')[0]
                gene_name = ensembl_to_name[ensembl_id]

            except KeyError:
                gene_name = None
            if gene_name:
                test_gene_names.append(gene_name)
                test_gene_position.append(gene.position)

        test_df_values = []
        indices = []
        for sample in tqdm(test_samples):
            indices.append(sample.sample_id)
            sample_counts = []
            gene_counts = sample.count
            for i, gene in enumerate(train_gene_order):
                try:
                    gene_idx = test_gene_names.index(gene)
                    pos = test_gene_position[gene_idx]
                    count = gene_counts[pos]
                except Exception:
                    count = train_gene_means[i]
                sample_counts.append(count)
            test_df_values.append(np.array(sample_counts))
        df = pd.DataFrame(np.array(test_df_values), columns=train_gene_order, index=indices)

        X = df.values
        lr = pickle.loads(model.model)
        y = lr.predict(X)

        samples = Sample.objects.filter(experiment=test_experiment)
        sample_to_geneCount = {}
        for sample in samples:
            sample_to_geneCount[sample.sample_id] = sample.count

        sample_to_geneCount_df = pd.DataFrame.from_dict(sample_to_geneCount, orient='index')
        new_cols = []
        allgenes = Gene.objects.filter(experiment=test_experiment).order_by('position')

        for gene in allgenes:
            new_cols.append(gene.gene_name)
        sample_to_geneCount_df.columns = new_cols

        dfValues = sample_to_geneCount_df.iloc[:, :].values

        pca = PCA(n_components=2)
        principalComponents = pca.fit_transform(dfValues)
        principalDf = pd.DataFrame(data=principalComponents,
                                   columns=['principal component 1', 'principal component 2'],
                                   index=indices)
        fig = plt.figure(figsize=(8, 8))
        ax = fig.add_subplot(1, 1, 1)
        ax.set_xlabel('PC1 {0:0.1f}%'''.format(pca.explained_variance_ratio_[0] * 100), fontsize=15)
        ax.set_ylabel('PC2 {0:0.1f}%'''.format(pca.explained_variance_ratio_[1] * 100), fontsize=15)
        yDict = {}
        for i, x in enumerate(indices):
            yDict[x] = y[i]
        selectedFeaturesdf = pd.DataFrame.from_dict(yDict, orient='index')
        selectedFeaturesdf.columns = ['subtype']
        finalDf = pd.concat([principalDf, selectedFeaturesdf], axis=1)
        targets = [0, 1]
        for target in targets:
            indicesToKeep = finalDf['subtype'] == target
            ax.scatter(finalDf.loc[indicesToKeep, 'principal component 1']
                       , finalDf.loc[indicesToKeep, 'principal component 2']
                       , s=50)
        ax.legend(targets)
        ax.set_xticks([0], minor=True)
        ax.xaxis.grid(True, which='minor', linestyle='--', linewidth=2)
        buf = io.BytesIO()
        fig.savefig(buf, format='png')
        buf.seek(0)
        string = base64.b64encode(buf.read())
        uri = 'data:image/png;base64,' + urllib.parse.quote(string)
        context = {'image': uri}
        return render(request, 'pcatest.html', context)

    elif train_gene_format == 'ensembl' and test_gene_format == 'names':
        with open(os.path.join(BASE_DIR, "supervisedLearning/helper/name_to_ensembl"), 'rb') as f:
            name_to_ensembl = pickle.load(f)

        test_samples = Sample.objects.filter(experiment=test_experiment)
        test_genes = Gene.objects.filter(experiment__exact=Experiment.objects.get(gse_id=test_experiment_gse))

        test_gene_names = []
        test_gene_position = []
        for gene in test_genes:
            ensembl_id = gene.gene_name
            if '.' in ensembl_id:
                ensembl_id = ensembl_id.split('.')[0]
            try:
                gene_name = name_to_ensembl[ensembl_id]
            except KeyError:
                gene_name = None
            if gene_name:
                test_gene_names.append(gene_name)
                test_gene_position.append(gene.position)

        test_df_values = []
        indices = []
        for sample in tqdm(test_samples):
            indices.append(sample.sample_id)
            sample_counts = []
            gene_counts = sample.count
            for i, gene in enumerate(train_gene_order):
                try:
                    gene_idx = test_gene_names.index(gene)
                    pos = test_gene_position[gene_idx]
                    count = gene_counts[pos]
                except Exception:
                    count = train_gene_means[i]
                sample_counts.append(count)
            test_df_values.append(np.array(sample_counts))
        df = pd.DataFrame(np.array(test_df_values), columns=train_gene_order, index=indices)

        X = df.values
        lr = pickle.loads(model.model)
        y = lr.predict(X)

        samples = Sample.objects.filter(experiment=test_experiment)
        sample_to_geneCount = {}
        for sample in samples:
            sample_to_geneCount[sample.sample_id] = sample.count

        sample_to_geneCount_df = pd.DataFrame.from_dict(sample_to_geneCount, orient='index')
        new_cols = []
        allgenes = Gene.objects.filter(experiment=test_experiment).order_by('position')

        for gene in allgenes:
            new_cols.append(gene.gene_name)
        sample_to_geneCount_df.columns = new_cols

        dfValues = sample_to_geneCount_df.iloc[:, :].values

        pca = PCA(n_components=2)
        principalComponents = pca.fit_transform(dfValues)
        principalDf = pd.DataFrame(data=principalComponents,
                                   columns=['principal component 1', 'principal component 2'],
                                   index=indices)
        fig = plt.figure(figsize=(8, 8))
        ax = fig.add_subplot(1, 1, 1)
        ax.set_xlabel('PC1 {0:0.1f}%'''.format(pca.explained_variance_ratio_[0] * 100), fontsize=15)
        ax.set_ylabel('PC2 {0:0.1f}%'''.format(pca.explained_variance_ratio_[1] * 100), fontsize=15)
        yDict = {}
        for i, x in enumerate(indices):
            yDict[x] = y[i]
        selectedFeaturesdf = pd.DataFrame.from_dict(yDict, orient='index')
        selectedFeaturesdf.columns = ['subtype']
        finalDf = pd.concat([principalDf, selectedFeaturesdf], axis=1)
        targets = [0, 1]
        for target in targets:
            indicesToKeep = finalDf['subtype'] == target
            ax.scatter(finalDf.loc[indicesToKeep, 'principal component 1']
                       , finalDf.loc[indicesToKeep, 'principal component 2']
                       , s=50)
        ax.legend(targets)
        ax.set_xticks([0], minor=True)
        ax.xaxis.grid(True, which='minor', linestyle='--', linewidth=2)
        buf = io.BytesIO()
        fig.savefig(buf, format='png')
        buf.seek(0)
        string = base64.b64encode(buf.read())
        uri = 'data:image/png;base64,' + urllib.parse.quote(string)
        context = {'image': uri}
        return render(request, 'pcatest.html', context)

    else:
        test_samples = Sample.objects.filter(experiment=test_experiment)
        test_genes = Gene.objects.filter(experiment__exact=Experiment.objects.get(gse_id=test_experiment_gse))

        test_gene_names = []
        test_gene_position = []
        for gene in test_genes:
            gene_name = gene.gene_name
            test_gene_names.append(gene_name)
            test_gene_position.append(gene.position)

        test_df_values = []
        indices = []
        for sample in tqdm(test_samples):
            indices.append(sample.sample_id)
            sample_counts = []
            gene_counts = sample.count
            for i, gene in enumerate(train_gene_order):
                try:
                    gene_idx = test_gene_names.index(gene)
                    pos = test_gene_position[gene_idx]
                    count = gene_counts[pos]
                except Exception:
                    count = train_gene_means[i]
                sample_counts.append(count)
            test_df_values.append(np.array(sample_counts))
        df = pd.DataFrame(np.array(test_df_values), columns=train_gene_order, index=indices)

        X = df.values
        lr = pickle.loads(model.model)
        y = lr.predict(X)

        samples = Sample.objects.filter(experiment=test_experiment)
        sample_to_geneCount = {}
        for sample in samples:
            sample_to_geneCount[sample.sample_id] = sample.count

        sample_to_geneCount_df = pd.DataFrame.from_dict(sample_to_geneCount, orient='index')
        new_cols = []
        allgenes = Gene.objects.filter(experiment=test_experiment).order_by('position')

        for gene in allgenes:
            new_cols.append(gene.gene_name)
        sample_to_geneCount_df.columns = new_cols

        dfValues = sample_to_geneCount_df.iloc[:, :].values

        pca = PCA(n_components=2)
        principalComponents = pca.fit_transform(dfValues)
        principalDf = pd.DataFrame(data=principalComponents,
                                   columns=['principal component 1', 'principal component 2'],
                                   index=indices)
        fig = plt.figure(figsize=(8, 8))
        ax = fig.add_subplot(1, 1, 1)
        ax.set_xlabel('PC1 {0:0.1f}%'''.format(pca.explained_variance_ratio_[0] * 100), fontsize=15)
        ax.set_ylabel('PC2 {0:0.1f}%'''.format(pca.explained_variance_ratio_[1] * 100), fontsize=15)
        yDict = {}
        for i, x in enumerate(indices):
            yDict[x] = y[i]
        selectedFeaturesdf = pd.DataFrame.from_dict(yDict, orient='index')
        selectedFeaturesdf.columns = ['subtype']
        finalDf = pd.concat([principalDf, selectedFeaturesdf], axis=1)
        targets = [0, 1]
        for target in targets:
            indicesToKeep = finalDf['subtype'] == target
            ax.scatter(finalDf.loc[indicesToKeep, 'principal component 1']
                       , finalDf.loc[indicesToKeep, 'principal component 2']
                       , s=50)
        ax.legend(targets)
        ax.set_xticks([0], minor=True)
        ax.xaxis.grid(True, which='minor', linestyle='--', linewidth=2)
        buf = io.BytesIO()
        fig.savefig(buf, format='png')
        buf.seek(0)
        string = base64.b64encode(buf.read())
        uri = 'data:image/png;base64,' + urllib.parse.quote(string)
        context = {'image': uri}
        return render(request, 'pcatest.html', context)
