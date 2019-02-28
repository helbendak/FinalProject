from django.test import TestCase, Client, RequestFactory
from .models import AttributeName, AttributeTerm


# Create your tests here.
class matchFeaturesTestCase(TestCase):
    # Test Case for the View: matchFeatures
    def setUp(self):
        AttributeName.objects.create(canonical_name='gender', synonyms=[])
        AttributeName.objects.create(canonical_name='none', synonyms=[])
        AttributeName.objects.create(canonical_name='deep ulcer', synonyms=['ulcer'])
        self.client = Client()

    def test_matchFeatures_post(self):
        context = {'features': ["['sex', 'diagnosis', 'age']"], 'existing_features_match': ['gender', 'none', 'none']}
        request = self.client.post('/matchFeatures/', context)
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
        response = self.client.get('/matchFeatures/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['features'], ['age', 'diagnosis'])
        self.assertEqual(response.context['existing_features'][0], AttributeName.objects.all()[0])

    def test_matchFeatures_get_redirect(self):
        session = self.client.session
        session['features1'] = ['gender', 'ulcer']
        session.save()
        response = self.client.get('/matchFeatures/')
        self.assertEqual(response.status_code, 302)  # Redirect


class matchTermsTestCase(TestCase):
    # Test Case for the View: matchTerms
    def setUp(self):
        gender = AttributeName.objects.create(canonical_name='gender', synonyms=['sex'])
        ulcer = AttributeName.objects.create(canonical_name='deep ulcer', synonyms=['ulcer'])
        age = AttributeName.objects.create(canonical_name='age at diagnosis', synonyms=['age'])
        none = AttributeName.objects.create(canonical_name='none', synonyms=[])
        AttributeTerm.objects.create(canonical_term='male', synonyms=['man'], attribute_name=gender)
        AttributeTerm.objects.create(canonical_term='female', synonyms=[], attribute_name=gender)
        AttributeTerm.objects.create(canonical_term='deep', synonyms=[], attribute_name=ulcer)
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
        session['features1'] = ['gender', 'deep ulcer']
        session['gender'] = ['man', 'female']
        session['deep ulcer'] = ['deep', 'not deep']
        session.save()
        response = self.client.get('/matchTerms/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['term_list'], ['deep ulcer : not deep'])
        self.assertEqual(response.context['all_terms'][0], AttributeTerm.objects.all()[0])

    def test_matchTerms_get_redirect(self):
        session = self.client.session
        session['features1'] = ['gender', 'deep ulcer']
        session['gender'] = ['man', 'female']
        session['deep ulcer'] = ['deep']
        session.save()
        response = self.client.get('/matchTerms/')
        self.assertEqual(response.status_code, 302)
