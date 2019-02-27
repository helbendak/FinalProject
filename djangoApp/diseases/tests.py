from django.test import TestCase, Client, RequestFactory
from .models import AttributeName


# Create your tests here.
class matchFeaturesTestCase(TestCase):
    # Test Case for the View: matchFeatures
    def setUp(self):
        AttributeName.objects.create(canonical_name='gender', synonyms=[])
        AttributeName.objects.create(canonical_name='none', synonyms=[])
        AttributeName.objects.create(canonical_name='deep ulcer', synonyms=['ulcer'])
        self.client = Client()

    def test_matchFeatures_post(self):
        session = self.client.session
        session['features1'] = ['sex', 'diagnosis', 'age']
        session.save()
        request = self.client.post('/matchFeatures/', {'existing_features_match': ['gender', 'none', 'none']})
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

    def test_matchFeatures_get_emptyList(self):
        session = self.client.session
        session['features1'] = ['gender', 'ulcer']
        session.save()
        response = self.client.get('/matchFeatures/')
        self.assertEqual(response.status_code, 302)  # Redirect
