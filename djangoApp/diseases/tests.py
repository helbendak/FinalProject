from django.test import TestCase, Client, RequestFactory, LiveServerTestCase
from .models import AttributeName, AttributeTerm, AttributeValue, Sample, Experiment, Disease
import mock
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
import os
from rpy2.robjects.vectors import ListVector
from django.core.files.uploadedfile import SimpleUploadedFile

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class MatchNamesTestCase(TestCase):
    def setUp(self):
        AttributeName.objects.create(canonical_name='gender', synonyms=[])
        AttributeName.objects.create(canonical_name='none', synonyms=[])
        AttributeName.objects.create(canonical_name='deep ulcer', synonyms=['ulcer'])
        self.client = Client()

    def test_matchFeatures_post(self):
        context = {'features': ["['sex', 'diagnosis', 'age']"], 'existing_features_match': ['gender', 'none', 'none']}
        request = self.client.post('/matchNames/', context)
        self.assertEqual(request.status_code, 302)
        gender = AttributeName.objects.get(canonical_name='gender')
        diagnosis = AttributeName.objects.get(canonical_name='diagnosis')
        age = AttributeName.objects.get(canonical_name='age')
        self.assertEqual(gender.canonical_name, 'gender')
        self.assertEqual(gender.synonyms, ['sex'])
        self.assertEqual(diagnosis.canonical_name, 'diagnosis')
        self.assertEqual(age.canonical_name, 'age')

    def test_matchFeatures_get(self):
        session = self.client.session
        session['features1'] = ['gender', 'ulcer', 'age', 'diagnosis']
        session.save()
        response = self.client.get('/matchNames/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['features'], ['age', 'diagnosis'])
        self.assertEqual(response.context['existing_features'][0], AttributeName.objects.all()[0])

    def test_matchFeatures_get_redirect(self):
        session = self.client.session
        session['features1'] = ['gender', 'ulcer']
        session.save()
        response = self.client.get('/matchNames/')
        self.assertEqual(response.status_code, 302)  # Redirect


class MatchTermsTestCase(TestCase):
    def setUp(self):
        gender = AttributeName.objects.create(canonical_name='gender', synonyms=['sex'])
        ulcer = AttributeName.objects.create(canonical_name='deep ulcer', synonyms=['ulcer'])
        age = AttributeName.objects.create(canonical_name='age at diagnosis', synonyms=['age'])
        none = AttributeName.objects.create(canonical_name='none', synonyms=[])
        AttributeTerm.objects.create(canonical_term='male', synonyms=['man'], attribute_name=gender)
        AttributeTerm.objects.create(canonical_term='female', synonyms=[], attribute_name=gender)
        AttributeTerm.objects.create(canonical_term='deep', synonyms=[], attribute_name=ulcer)
        AttributeTerm.objects.create(canonical_term='na', synonyms=[], attribute_name=gender)
        AttributeTerm.objects.create(canonical_term='na', synonyms=[], attribute_name=ulcer)
        AttributeTerm.objects.create(canonical_term='none', synonyms=[], attribute_name=none)
        self.client = Client()

    def test_matchTerms_post(self):
        context = {'existing_terms_match': ['deep', 'deep', 'none', 'female'],
                   'term_list': ["['deep ulcer : almost deep', 'ulcer : kinda deep', 'age : 9.42', 'sex : woman']"]}
        request = self.client.post('/matchTerms/', context)
        self.assertEqual(request.status_code, 302)
        deep = AttributeTerm.objects.get(canonical_term='deep')
        nine = AttributeTerm.objects.filter(canonical_term='9.42')
        female = AttributeTerm.objects.get(canonical_term='female')
        self.assertEqual(deep, AttributeTerm.objects.filter(synonyms__contains=['almost deep'])[0])
        self.assertEqual(len(AttributeTerm.objects.filter(synonyms__contains=['almost deep'])), 1)
        self.assertEqual(deep, AttributeTerm.objects.filter(synonyms__contains=['kinda deep'])[0])
        self.assertEqual(len(AttributeTerm.objects.filter(synonyms__contains=['kinda deep'])), 1)
        self.assertEqual(len(nine), 1)
        self.assertEqual(female, AttributeTerm.objects.filter(synonyms__contains=['woman'])[0])

    def test_matchTerms_get(self):
        session = self.client.session
        session['features1'] = ['gender', 'deep ulcer', 'anything_feature']
        session['gender'] = ['man', 'female']
        session['deep ulcer'] = ['deep', 'not deep']
        session['anything_feature'] = ['na']
        session.save()
        response = self.client.get('/matchTerms/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['term_list'], ['deep ulcer : not deep', 'anything_feature : na'])
        self.assertEqual(response.context['all_terms'][0], AttributeTerm.objects.all()[0])

    def test_matchTerms_get_redirect(self):
        session = self.client.session
        session['features1'] = ['gender', 'deep ulcer', 'sex']
        session['gender'] = ['man', 'female']
        session['deep ulcer'] = ['deep', 'na']
        session['sex'] = ['na']
        session.save()
        response = self.client.get('/matchTerms/')
        self.assertEqual(response.status_code, 302)


class SyncValuesTestCase(TestCase):
    def setUp(self):
        self.disease = Disease.objects.create(name="Crohns", description="IBD")
        experiment = Experiment.objects.create(gse_id='GSE1', gene_format='names', disease=self.disease)
        sample1 = Sample.objects.create(experiment=experiment, sample_gsm='GSM1', sample_id='SAMPLE1', count=[1.0, 2.0])
        sample2 = Sample.objects.create(experiment=experiment, sample_gsm='GSM2', sample_id='SAMPLE2', count=[2.0, 1.0])
        AttributeName.objects.create(canonical_name='none', synonyms=[])
        gender = AttributeName.objects.create(canonical_name='gender', synonyms=['sex'])
        diagnosis = AttributeName.objects.create(canonical_name='diagnosis', synonyms=['disease status'])
        male = AttributeValue.objects.create(name='gender', value='male', sample=sample1)
        female = AttributeValue.objects.create(name='sex', value='female', sample=sample2)
        cd = AttributeValue.objects.create(name='diagnosis', value='cd', sample=sample1)
        uc = AttributeValue.objects.create(name='diagnosis', value='uc', sample=sample2)
        self.client = Client()

    def test_syncValues(self):
        response = self.client.get('/syncValues/')
        gender = AttributeName.objects.get(canonical_name='gender')
        diagnosis = AttributeName.objects.get(canonical_name='diagnosis', synonyms=['disease status'])
        male = AttributeValue.objects.get(name='gender', value='male')
        female = AttributeValue.objects.get(name='sex', value='female')
        cd = AttributeValue.objects.get(name='diagnosis', value='cd')
        uc = AttributeValue.objects.get(name='diagnosis', value='uc')

        self.assertEqual(male.attribute_name, gender)
        self.assertEqual(female.attribute_name, gender)
        self.assertEqual(uc.attribute_name, diagnosis)
        self.assertEqual(cd.attribute_name, diagnosis)
        self.assertEqual(response.status_code, 302)


class IndexTestCase(TestCase):
    def setUp(self):
        self.client = Client()

    def test_index(self):
        request = self.client.post('/')
        self.assertEqual(request.status_code, 200)


class SearchTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.disease = Disease.objects.create(name="Crohns", description="IBD")

    def test_search_post(self):
        path = os.path.join(BASE_DIR, "diseases/test_helpers/gse85499_log_expression.csv")
        file = open(path, 'r')
        context = {'textfield': 'GSE85499', 'document': file, 'gene_format': 'names', 'disease': self.disease.id}
        request = self.client.post('/search/', context)
        self.assertEqual(request.status_code, 302)
        self.assertEqual(Experiment.objects.get(id=1).gse_id, 'GSE85499')

    def test_search_get(self):
        response = self.client.get('/search/')
        self.assertEqual(response.status_code, 200)
