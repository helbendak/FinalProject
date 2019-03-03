# Create your models here.
from django.db import models
from django.contrib.postgres.fields import ArrayField


class Disease(models.Model):
    name = models.CharField(max_length=30)
    description = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class Experiment(models.Model):
    description = models.CharField(max_length=100)
    disease = models.ForeignKey(Disease, on_delete=models.CASCADE)

    def __str__(self):
        return self.description


class ArrayData(models.Model):
    data = models.CharField(max_length=100)
    experiment = models.ForeignKey(Experiment, on_delete=models.CASCADE)

    def __str__(self):
        return self.experiment.description


class AttributeName(models.Model):
    id = models.AutoField(primary_key=True)
    canonical_name = models.CharField(max_length=50)
    synonyms = ArrayField(models.CharField(max_length=50), blank=True)
    # experiment = models.ForeignKey(Experiment, on_delete=models.CASCADE)
    # description = models.CharField(max_length=150)

    def __str__(self):
        return self.canonical_name


class AttributeTerm(models.Model):
    id = models.AutoField(primary_key=True)
    canonical_term = models.CharField(max_length=50)
    synonyms = ArrayField(models.CharField(max_length=50), blank=True)
    attribute_name = models.ForeignKey(AttributeName, on_delete=models.CASCADE)

    def __str__(self):
        return self.canonical_term


class Sample(models.Model):
    id = models.AutoField(primary_key=True)
    sample_gsm = models.CharField(max_length=30)
    sample_id = models.CharField(max_length=30)

    def __str__(self):
        return self.sample_id


class AttributeValue(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=50)
    value = models.CharField(max_length=50)
    sample = models.ForeignKey(Sample, on_delete=models.CASCADE)
    attribute_name = models.ForeignKey(AttributeName, on_delete=models.CASCADE, blank=True, null=True)

    def __str__(self):
        return self.value
