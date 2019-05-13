from django.db import models
from django.contrib.postgres.fields import ArrayField


class Disease(models.Model):
    """
    The Disease Model stores information about a particular disease

    :param name: Name of the disease
    :param description: A brief description of the disease
    """
    name = models.CharField(max_length=30)
    description = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class Experiment(models.Model):
    """
    The Experiment Model stores information about a particular experiment

    :param gse_id: GSE Accession Number
    :param gene_format: Either Ensembl IDs or Gene Names
    """
    # description = models.CharField(max_length=100)
    id = models.AutoField(primary_key=True)
    disease = models.ForeignKey(Disease, on_delete=models.CASCADE)
    gse_id = models.CharField(max_length=15)
    gene_format = models.CharField(max_length=10)

    def __str__(self):
        return self.gse_id


class AttributeName(models.Model):
    """
    The AttributeName Model stores information about the attribute's name (i.e. 'gender', 'age')

    :param canonical_name: The canonical name of the attribute
    :param synonyms: A list of synonyms corresponding to the canonical name
    """
    id = models.AutoField(primary_key=True)
    canonical_name = models.CharField(max_length=50)
    synonyms = ArrayField(models.CharField(max_length=50), blank=True)

    def __str__(self):
        return self.canonical_name


class AttributeTerm(models.Model):
    """
    The AttributeTerm Model stores information about the attribute's term (i.e. 'male', 'female')

    :param canonical_term: The canonical term of the attribute
    :param synonyms: A list of synonyms corresponding to the canonical name
    :param attribute_name: An AttributeName object corresponding to this term
    """
    id = models.AutoField(primary_key=True)
    canonical_term = models.CharField(max_length=50)
    synonyms = ArrayField(models.CharField(max_length=50), blank=True)
    attribute_name = models.ForeignKey(AttributeName, on_delete=models.CASCADE)

    def __str__(self):
        return self.canonical_term


class Sample(models.Model):
    """
    The Sample Model stores information about a particular sample

    :param gse_id: TODO
    :param sample_gsm: The unique GSM ID for the sample
    :param sample_id: The Sample ID
    :param count: Array of gene expression values
    """
    id = models.AutoField(primary_key=True)
    # gse_id = models.CharField(max_length=15)  # TODO: Should be Foreign Key to Experiment
    experiment = models.ForeignKey(Experiment, on_delete=models.CASCADE)
    sample_gsm = models.CharField(max_length=30)
    sample_id = models.CharField(max_length=30)
    count = ArrayField(models.FloatField())

    def __str__(self):
        return self.sample_id


class AttributeValue(models.Model):
    """
    The AttributeValue Model stores information about an attribute term and value pair

    :param name: Name of attribute
    :param value: Value of attribute
    :param sample: Sample this pair links to
    :param attribute_name: The attribute name this pair links to (to keep track of the application's ontology)
    """
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=50)
    value = models.CharField(max_length=50)
    sample = models.ForeignKey(Sample, on_delete=models.CASCADE)
    attribute_name = models.ForeignKey(AttributeName, on_delete=models.CASCADE, blank=True, null=True)

    def __str__(self):
        return self.value


class Gene(models.Model):
    """
    The Gene Model stores information about a particular Gene relative to a particular Experiment

    :param gene_name: The gene name or Ensembl ID
    :param experiment: The experiment this gene is linked to
    :param position: The position of this gene in the array of expression values
    """
    id = models.AutoField(primary_key=True)
    gene_name = models.CharField(max_length=100)
    experiment = models.ForeignKey(Experiment, on_delete=models.CASCADE)
    position = models.IntegerField()

    def __str__(self):
        return self.gene_name
