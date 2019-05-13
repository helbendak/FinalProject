from django.db import models
from django.contrib.postgres.fields import ArrayField
from diseases.models import Experiment


class SupervisedModel(models.Model):
    """
    This class stores a Supervised Learning algorithm

    :param experiment: The experiment this Supervised Learning algorithm corresponds to
    :param model: The actual model, stored as a binary file
    :param gene_order: The ordering of the genes in the feature vector when the training was done
    :param gene_means: The mean value of each gene in the training set
    :param pc: The principal component the split was done on
    :param threshold: The threshold the split was done on
    """
    experiment = models.ForeignKey(Experiment, on_delete=models.CASCADE)
    model = models.BinaryField()
    gene_order = ArrayField(models.CharField(max_length=60))
    gene_means = ArrayField(models.FloatField())
    pc = models.CharField(max_length=60)
    threshold = models.CharField(max_length=20)
