from django.test import TestCase, Client
from .models import SupervisedModel
from diseases.models import Experiment, Sample, Gene, Disease


class LogisticRegressionTestCase(TestCase):
    def setUp(self):
        self.disease = Disease.objects.create(name="Crohns", description="IBD")
        Experiment.objects.create(gse_id='GSE1', gene_format='names', disease=self.disease)
        self.client = Client()

    def test_logisticRegression_post(self):
        context = {'test_experiment': 'GSE1', 'trained_model_gse': 'GSE2'}
        request = self.client.post('/supervised/', context)
        self.assertEqual(request.status_code, 302)

    def test_logisticRegression_get(self):
        session = self.client.session
        session['feature_order'] = [['A1BG', 2.0], ['A2BG', 3.0]]
        session['gse'] = 'GSE1'
        session['pc'] = 'pc1'
        session['threshold'] = '2'
        session['dataframe'] = '{"A1BG": {"20_RNA": 4.8, "21_RNA": 5.0}, "A2BG":{"20_RNA": 3.2, "21_RNA": 4.5}, "sub-type":{"20_RNA": 1.0, "21_RNA": 0.0}}'
        session.save()
        response = self.client.get('/supervised/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(SupervisedModel.objects.get(id=1).gene_means, [2.0, 3.0])


class LogisticRegressionTestingTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.disease = Disease.objects.create(name="Crohns", description="IBD")
        self.exp1 = Experiment.objects.create(gse_id='GSE1', gene_format='ensembl', disease=self.disease)
        self.exp2 = Experiment.objects.create(gse_id='GSE2', gene_format='names', disease=self.disease)
        self.exp3 = Experiment.objects.create(gse_id='GSE3', gene_format='names', disease=self.disease)
        Gene.objects.create(gene_name="A1BG", experiment=self.exp2, position=1)
        Gene.objects.create(gene_name="RABGGTB", experiment=self.exp2, position=2)
        Gene.objects.create(gene_name="ENSG00000121410.0", experiment=self.exp1, position=2)
        Gene.objects.create(gene_name="ENSG000001379568", experiment=self.exp1, position=1)
        Gene.objects.create(gene_name="A1BG", experiment=self.exp3, position=2)
        Gene.objects.create(gene_name="RABGGTB", experiment=self.exp3, position=1)

    def test_logisticRegressionTest_get(self):
        response = self.client.get('/supervisedtest/')
        self.assertEqual(response.status_code, 200)

    def test_LogisticRegressionTest_post_names_ensembl(self):
        session = self.client.session
        session['feature_order'] = [['A1BG', 2.0], ['A2BG', 3.0]]
        session['gse'] = 'GSE2'
        session['pc'] = 'principal component 1'
        session['threshold'] = '0'
        session['dataframe'] = '{"A1BG": {"20_RNA": 4.8, "21_RNA": 5.0}, "RABGGTB":{"20_RNA": 3.2, "21_RNA": 4.5}, "sub-type":{"20_RNA": 1.0, "21_RNA": 0.0}}'
        session.save()
        self.client.get('/supervised/')

        session['test_experiment'] = 'GSE1'
        session['trained_model_gse'] = 'GSE2'
        session.save()
        Sample.objects.create(experiment=self.exp1, sample_gsm='GSM1', sample_id='SAMPLE1', count=[1.0, 2.0])
        Sample.objects.create(experiment=self.exp1, sample_gsm='GSM2', sample_id='SAMPLE2', count=[2.0, 1.0])

        request = self.client.post('/supervisedtest/', {'test_experiment': 'GSE1', 'trained_model': 'GSE2'})

        self.assertEqual(request.status_code, 200)

    def test__LogisticRegressionTest_post_ensembl_names(self):
        session = self.client.session
        session['feature_order'] = [['ENSG00000121410', 2.0], ['ENSG000001379568', 3.0]]
        session['gse'] = 'GSE1'
        session['dataframe'] = '{"ENSG00000121410": {"20_RNA": 4.8, "21_RNA": 5.0}, "ENSG000001379568":{"20_RNA": 3.2, "21_RNA": 4.5}, "sub-type":{"20_RNA": 1.0, "21_RNA": 0.0}}'
        session['pc'] = 'principal component 1'
        session['threshold'] = '0'
        session.save()
        self.client.get('/supervised/')

        session['test_experiment'] = 'GSE2'
        session['trained_model_gse'] = 'GSE1'
        session.save()
        Sample.objects.create(experiment=self.exp2, sample_gsm='GSM1', sample_id='SAMPLE1', count=[1.0, 2.0])
        Sample.objects.create(experiment=self.exp2, sample_gsm='GSM2', sample_id='SAMPLE2', count=[2.0, 1.0])

        request = self.client.post('/supervisedtest/', {'test_experiment': 'GSE2', 'trained_model': 'GSE1'})

        self.assertEqual(request.status_code, 200)

    def test__LogisticRegressionTest_post_names_names(self):
        session = self.client.session
        session['feature_order'] = [['A1BG', 2.0], ['A2BG', 3.0]]
        session['gse'] = 'GSE2'
        session['dataframe'] = '{"A1BG": {"20_RNA": 4.8, "21_RNA": 5.0}, "RABGGTB":{"20_RNA": 3.2, "21_RNA": 4.5}, "sub-type":{"20_RNA": 1.0, "21_RNA": 0.0}}'
        session['pc'] = 'principal component 1'
        session['threshold'] = '0'
        session.save()
        self.client.get('/supervised/')

        session['test_experiment'] = 'GSE3'
        session['trained_model_gse'] = 'GSE2'
        session.save()
        Sample.objects.create(experiment=self.exp3, sample_gsm='GSM1', sample_id='SAMPLE1', count=[1.0, 2.0])
        Sample.objects.create(experiment=self.exp3, sample_gsm='GSM2', sample_id='SAMPLE2', count=[2.0, 1.0])

        request = self.client.post('/supervisedtest/', {'test_experiment': 'GSE3', 'trained_model': 'GSE2'})

        self.assertEqual(request.status_code, 200)
