from django.shortcuts import render, redirect
import rpy2.robjects.packages as rpackages
from rpy2.robjects.vectors import StrVector, FactorVector
from rpy2.robjects import r
from django.core.files.storage import FileSystemStorage
import os
from .models import Sample, AttributeName, AttributeValue, AttributeTerm, Gene, Experiment, Disease
import re
import ast
import csv
import pandas as pd

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def index(request):
    """
    Renders the homepage
    """
    return render(request, 'base.html')


def search(request):
    """
    Handles the download of meta-data, parsing the gene expression values for the samples, and matching the meta-data to
    the appropriate samples
    """
    if request.method == 'POST':
        # Install R libraries
        packageNames = ('GEOquery', 'Biobase')
        utils = rpackages.importr('utils')
        utils.chooseCRANmirror(ind=1)
        packnames_to_install = [x for x in packageNames if not rpackages.isinstalled(x)]
        if len(packnames_to_install) > 0:
            utils.install_packages(StrVector(packnames_to_install))
        GEOquery = rpackages.importr('GEOquery')
        Biobase = rpackages.importr('Biobase')

        # Extract POST data from HTML
        search_id = request.POST.get('textfield', None)
        uploaded_file = request.FILES['document']
        gene_format = request.POST.get('gene_format', None)
        disease = request.POST.get('disease', None)
        experiment = Experiment.objects.get_or_create(gse_id=search_id, gene_format=gene_format, disease=Disease.objects.get(id=disease))

        # Get gene counts for each sample
        allCounts = []
        df = pd.read_csv(uploaded_file)
        df = df.T
        df = df.iloc[1:, :].values
        for row in df:
            allCounts.append(list(row))

        # Extract Genes and Sample IDs from count file
        fs = FileSystemStorage()
        fs.save(search_id+"_expression", uploaded_file)
        with open(os.path.join(BASE_DIR, "media/"+search_id+"_expression")) as csvDataFile:
            csvReader = csv.reader(csvDataFile)
            for idx, row in enumerate(csvReader):
                if idx == 0:
                    expressionFile_sampleIDs = row[1:]
                else:
                    Gene.objects.get_or_create(gene_name=row[0], experiment=experiment[0], position=idx-1)
        request.session['gse'] = search_id

        # Find which column in GEO corresponds to the sample IDs in the expression file
        eList = GEOquery.getGEO(search_id)  # GSE57945
        geo_all = Biobase.pData(eList[0])
        geo_all_list = []

        for i in range(len(geo_all)):
            if type(geo_all[i]) == FactorVector:
                geo_all_list.append(list(geo_all[i].levels))
            else:
                geo_all_list.append(list(geo_all[i]))

        for geo_list in geo_all_list:
            if all(elem in geo_list for elem in expressionFile_sampleIDs):
                ids_idx = geo_all_list.index(geo_list)

        geo_sampleIDs = Biobase.pData(eList[0])[ids_idx]

        # Map sample IDs in expression file to GSM codes in GEO
        geo_GSM_list = Biobase.pData(eList[0])[1]  # GSM Codes always stored in column 1
        sampleIDs_to_geoGSM = {}
        for i in range(len(geo_sampleIDs)):
            if type(geo_sampleIDs) == FactorVector:
                sample_id = str(geo_sampleIDs.levels[geo_sampleIDs[i]-1])
            else:
                sample_id = geo_sampleIDs[i]
            sample_gsm = str(geo_GSM_list[i])
            sampleIDs_to_geoGSM[sample_id] = sample_gsm

        # Create sample objects in database
        for idx, sample_id in enumerate(expressionFile_sampleIDs):
            sample_id = sample_id
            sample_gsm = sampleIDs_to_geoGSM[sample_id]
            Sample.objects.get_or_create(experiment=experiment[0], sample_id=sample_id, sample_gsm=sample_gsm, count=allCounts[idx])

        # Find which features we will be extracting from GEO
        geo_all_features = r.names(Biobase.pData(eList[0]))
        all_features_list = []
        for feature_name in geo_all_features:
            all_features_list.append(feature_name)
        ch1_regex = re.compile(":ch1$")
        features_temp = [item for i, item in enumerate(all_features_list) if re.search(ch1_regex, item)]
        features = [x.replace(':ch1', '') for x in features_temp]

        # Extract attribute values for each attribute for each sample & create corresponding objects in DB
        for feature in features:
            geo_attributeValue = geo_all_list[all_features_list.index(feature+":ch1")]
            attribute_values = []
            for attribute in geo_attributeValue:
                attribute_values.append(attribute)
            attribute_values = [a.lower() for a in attribute_values]
            attribute_values = set(attribute_values)
            attribute_values = list(attribute_values)
            request.session[feature.lower()] = attribute_values
            for sample_id in expressionFile_sampleIDs:
                geo_gsm = sampleIDs_to_geoGSM[sample_id]
                sample_idx = geo_GSM_list.index(geo_gsm)
                attribute_mapping = geo_attributeValue[sample_idx].lower()
                sample = Sample.objects.get(sample_id=sample_id)
                AttributeValue.objects.get_or_create(name=feature.lower(), value=attribute_mapping, sample=sample)

        features = [x.lower() for x in features]
        request.session['features1'] = features

        return redirect('/matchNames/')
    else:
        return render(request, 'searchGEO.html', {'diseases': Disease.objects.all()})


def matchNames(request):
    """
    Handles matching the attribute names to each other in order to keep a synchronized ontology
    """
    if request.method == 'POST':
        existing_features = request.POST.getlist('existing_features_match')
        new_features = request.POST.getlist('features')[0]
        new_features = ast.literal_eval(new_features)
        for i, f in enumerate(existing_features):
            if f == "none":
                attributeName = AttributeName(canonical_name=new_features[i], synonyms=[])
                attributeName.save()
            else:
                attributeName = AttributeName.objects.get(canonical_name=f)
                attributeName.synonyms.append(new_features[i])
                attributeName.save()
        return redirect('/matchTerms/')

    else:
        features_temp = request.session['features1']

        # Filter features to exclude any that have an exact match - don't want the user to go through all of them
        features = []
        for feature in features_temp:
            # Check in canonical
            try:
                AttributeName.objects.get(canonical_name=feature)
            except AttributeName.DoesNotExist:
                # Check in synonyms
                synonyms_exist = AttributeName.objects.filter(synonyms__contains=[feature])
                if not synonyms_exist:
                    features.append(feature)

        if not features:
            # If all features get filtered here, move on to next screen
            return redirect('/matchTerms/')
        else:
            context = {'features': features, 'existing_features': AttributeName.objects.all()}
            return render(request, 'matchFeatures.html', context)


def matchTerms(request):
    """
    Handles matching the attribute values to each other in order to keep a synchronized ontology
    """
    if request.method == 'POST':
        existing_terms = request.POST.getlist('existing_terms_match')
        new_terms = request.POST.getlist('term_list')[0]
        new_terms = ast.literal_eval(new_terms)  # POST gets this as a string, need to convert it to a list
        for i, t in enumerate(existing_terms):
            name, term = new_terms[i].split(' : ')
            if t == "none":
                try:
                    attributeName = AttributeName.objects.get(canonical_name=name)
                except AttributeName.DoesNotExist:
                    attributeName = AttributeName.objects.filter(synonyms__contains=[name])[0]
                attributeTerm = AttributeTerm.objects.create(
                    canonical_term=term, synonyms=[], attribute_name=attributeName)
            else:
                try:
                    attributeName = AttributeName.objects.get(canonical_name=name)
                except AttributeName.DoesNotExist:
                    attributeName = AttributeName.objects.filter(synonyms__contains=[name])[0]
                attributeTerm = AttributeTerm.objects.get(canonical_term=t, attribute_name=attributeName)
                attributeTerm.synonyms.append(term)
                attributeTerm.save()
        return redirect('/syncValues/')

    else:
        new_features = request.session['features1']
        term_list = []
        for feature in new_features:
            terms = request.session[feature]
            for term in terms:
                try:
                    # Check in canonical names
                    AttributeTerm.objects.get(canonical_term=term)
                except AttributeTerm.DoesNotExist:
                    # Check in synonyms
                    synonyms_exist = AttributeTerm.objects.filter(synonyms__contains=[term])
                    if not synonyms_exist:
                        term_list.append(feature + " : " + term)
                except AttributeTerm.MultipleObjectsReturned:
                    # Check if AttributeName matches
                    try:
                        attributeName = AttributeName.objects.get(canonical_name=feature)
                    except AttributeName.DoesNotExist:
                        attributeName = AttributeName.objects.filter(synonyms__contains=[feature])
                        if not attributeName:
                            term_list.append(feature + " : " + term)

        if not term_list:
            return redirect('/syncValues/')
        else:
            context = {'term_list': term_list, 'all_terms': AttributeTerm.objects.all()}
            return render(request, 'matchTerms.html', context)


def syncValues(request):
    """
    Handles matching the attribute terms and values in the ontology to the attribute terms and values of the samples
    """
    all_values = AttributeValue.objects.all()
    for attValue in all_values:
        name = attValue.name
        try:
            attName = AttributeName.objects.get(canonical_name=name)
        except AttributeName.DoesNotExist:
            attName = AttributeName.objects.filter(synonyms__contains=[name])[0]
        attValue.attribute_name = attName
        attValue.save()
    return redirect('/plotpca/')
