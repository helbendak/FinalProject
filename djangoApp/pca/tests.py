from django.test import TestCase, Client
from diseases.models import AttributeName, AttributeTerm, Sample, AttributeValue, Experiment, Gene, Disease


class PlotPCATestCase(TestCase):
    def setUp(self):
        self.disease = Disease.objects.create(name="Crohns", description="IBD")
        experiment = Experiment.objects.create(gse_id='GSE1', gene_format='names', disease=self.disease)
        sample1 = Sample.objects.create(experiment=experiment, sample_gsm='GSM1', sample_id='SAMPLE1', count=[1.0, 2.0])
        sample2 = Sample.objects.create(experiment=experiment, sample_gsm='GSM2', sample_id='SAMPLE2', count=[2.0, 1.0])

        gender = AttributeName.objects.create(canonical_name='gender', synonyms=['sex'])
        ulcer = AttributeName.objects.create(canonical_name='deep ulcer', synonyms=['ulcer'])

        AttributeName.objects.create(canonical_name='none', synonyms=[])
        self.male = AttributeTerm.objects.create(canonical_term='male', synonyms=['man'], attribute_name=gender)
        self.female = AttributeTerm.objects.create(canonical_term='female', synonyms=[], attribute_name=gender)
        self.deep = AttributeTerm.objects.create(canonical_term='deep', synonyms=[], attribute_name=ulcer)
        self.not_deep = AttributeTerm.objects.create(canonical_term='not deep', synonyms=[], attribute_name=ulcer)

        AttributeValue.objects.create(name='gender', value='male', sample=sample1, attribute_name=gender)
        AttributeValue.objects.create(name='gender', value='female', sample=sample2, attribute_name=gender)
        AttributeValue.objects.create(name='deep ulcer', value='deep', sample=sample1, attribute_name=ulcer)
        AttributeValue.objects.create(name='deep ulcer', value='not deep', sample=sample2, attribute_name=ulcer)

        Gene.objects.create(gene_name='GENE1', experiment=experiment, position=1)
        Gene.objects.create(gene_name='GENE2', experiment=experiment, position=2)

        self.client = Client()

    def test_plotPCA_get(self):
        session = self.client.session
        session['features1'] = ['gender', 'deep ulcer']
        session['gender'] = ['man', 'female']
        session['deep ulcer'] = ['deep', 'not deep']
        session.save()
        response = self.client.get('/plotpca/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['terms'], [self.male, self.female, self.deep, self.not_deep])

    def test_plotPCA_post_show(self):
        session = self.client.session
        session['gse'] = 'GSE1'
        session['features1'] = ['gender', 'deep ulcer']
        session['gender'] = ['man', 'female']
        session['deep ulcer'] = ['deep', 'not deep']
        session.save()
        context = {'selected_feature': 'gender', 'show':'show'}
        response = self.client.post('/plotpca/', context)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['terms'], [self.male, self.female, self.deep, self.not_deep])

    def test_plotPCA_post_submit(self):
        session = self.client.session
        session['gse'] = 'GSE1'
        session['features1'] = ['gender', 'deep ulcer']
        session['gender'] = ['man', 'female']
        session['deep ulcer'] = ['deep', 'not deep']
        session.save()
        context = {'selected_feature': 'gender', 'submit': 'submit', 'threshold': '0', 'pc': 'principal component 1'}
        response = self.client.post('/plotpca/', context)
        self.assertEqual(response.status_code, 302)


