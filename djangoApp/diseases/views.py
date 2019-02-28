from django.shortcuts import render, redirect
import rpy2.robjects.packages as rpackages
from rpy2.robjects.vectors import StrVector, FactorVector
from rpy2.robjects import r
from django.core.files.storage import FileSystemStorage
import os
from .models import Sample, AttributeName, AttributeValue, AttributeTerm
import re
import ast

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# Create your views here.
def search(request):
    if request.method == 'POST':
        search_id = request.POST.get('textfield', None)
        packageNames = ('GEOquery', 'Biobase')
        utils = rpackages.importr('utils')
        utils.chooseCRANmirror(ind=1)
        packnames_to_install = [x for x in packageNames if not rpackages.isinstalled(x)]
        if len(packnames_to_install) > 0:
            utils.install_packages(StrVector(packnames_to_install))
        GEOquery = rpackages.importr('GEOquery')
        Biobase = rpackages.importr('Biobase')

        uploaded_file = request.FILES['document']
        fs = FileSystemStorage()
        fs.save(search_id+"_RPKM", uploaded_file)
        with open(os.path.join(BASE_DIR, "media/"+search_id+"_RPKM")) as f:
            rpkmFile_sampleIDs = f.readline().split()
        # TODO: Remove first 4 words: the column/row headers 'Gene ID Gene Symbol' -- should probably do this using
        #  the replace function to make it clear what we're replacing
        rpkmFile_sampleIDs = rpkmFile_sampleIDs[4:]

        # Find which column in GEO corresponds to the sample IDs in the RPKM file
        eList = GEOquery.getGEO(search_id)  # GSE57945
        geo_all = Biobase.pData(eList[0])
        geo_all_list = []

        for i in range(len(geo_all)):
            if type(geo_all[i]) == FactorVector:
                geo_all_list.append(list(geo_all[i].levels))
            else:
                geo_all_list.append(list(geo_all[i]))

        for geo_list in geo_all_list:
            if all(elem in geo_list for elem in rpkmFile_sampleIDs):
                ids_idx = geo_all_list.index(geo_list)

        geo_sampleIDs = Biobase.pData(eList[0])[ids_idx]

        # Map gene IDs in RPKM file to GEO Accession codes in GEO
        geo_GSM = Biobase.pData(eList[0])[1]

        sampleIDs_to_geoGSM = {}
        for i in range(len(geo_sampleIDs)):
            sampleIDs_to_geoGSM[str(geo_sampleIDs.levels[geo_sampleIDs[i]-1])] = str(geo_GSM[i])

        # Find which features we will be extracting from GEO
        geo_all_features = r.names(Biobase.pData(eList[0]))
        all_features_list = []
        for feature_name in geo_all_features:
            all_features_list.append(feature_name)
        ch1_regex = re.compile(":ch1$")
        features_temp = [item for i, item in enumerate(all_features_list) if re.search(ch1_regex, item)]
        features = [x.replace(':ch1', '') for x in features_temp]  # TODO: Make lowercase?

        for feature in features:
            geo_attributeValue = geo_all_list[all_features_list.index(feature+":ch1")]
            attribute_values = []
            for attribute in geo_attributeValue:
                attribute_values.append(attribute)
            attribute_values = [a.lower() for a in attribute_values]
            attribute_values = set(attribute_values)
            attribute_values = list(attribute_values)
            request.session[feature.lower()] = attribute_values

        # Create SampleAttributes
        # for feature in features:
        #     sampleAttribute, created = SampleAttribute.objects.get_or_create(name=feature)
        #     # sampleAttribute = SampleAttribute(name=feature)
        #     if created:
        #         sampleAttribute.save()

        # # TODO:Find attribute values for each feature
        # geneID_to_attributeValue = {}
        # geo_attributeValue = Biobase.pData(eList[0])[-8]
        # for i in range(len(geo_sampleIDs)):
        #     geneID_to_attributeValue[str(geo_sampleIDs.levels[geo_sampleIDs[i] - 1])] = str(geo_attributeValue[i]).lower()
        #
        # attribute_values = []
        # for i in range(len(geo_sampleIDs)):
        #     attribute_values.append(geo_attributeValue[i])
        #     attribute_values = [x.lower() for x in attribute_values]
        # attribute_values = set(attribute_values)
        #
        # # Create SampleAttributeValues
        # for attVal in attribute_values:
        #     attributeValue = AttributeValue(value=attVal, attribute=sampleAttribute)
        #     attributeValue.save()
        #
        # # Create Sample entries in database
        # for geneID in rpkmFile_sampleIDs:
        #     geoAccs = sampleIDs_to_geoGSM[geneID]
        #     sample = Sample(geoAccs=geoAccs, geneID=geneID)
        #     sample.save()
        #     #sample.sampleAttribute.add(sampleAttribute)
        #     attVal = geneID_to_attributeValue[geneID]
        #     attributeValue = AttributeValue.objects.get(value=attVal)
        #     sample.sampleAttributeValue.add(attributeValue)

        features = [x.lower() for x in features]
        request.session['features1'] = features

        return redirect('/matchFeatures/')
    else:
        return render(request, 'searchGEO.html')


def matchFeatures(request):
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
    if request.method == 'POST':
        existing_terms = request.POST.getlist('existing_terms_match')
        new_terms = request.POST.getlist('term_list')[0]  # TODO: Fix other function's HTML
        new_terms = ast.literal_eval(new_terms)  # POST gets this as a string, need to evaluate it into a list
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
        return redirect('/search/')

    else:
        new_features = request.session['features1']
        term_list = []
        for feature in new_features:
            terms = request.session[feature]
            for term in terms:
                try:
                    # Check in canonical names
                    AttributeTerm.objects.get(canonical_term=term)
                except (AttributeTerm.DoesNotExist, AttributeTerm.MultipleObjectsReturned) as error:
                    # Check in synonyms
                    synonyms_exist = AttributeTerm.objects.filter(synonyms__contains=[term])
                    if not synonyms_exist:
                        term_list.append(feature + " : " + term)

        if not term_list:
            return redirect('/search/')
        else:
            context = {'term_list': term_list, 'all_terms': AttributeTerm.objects.all()}
            return render(request, 'matchTerms.html', context)
