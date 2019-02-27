from django.contrib import admin
from .models import Disease, Experiment, ArrayData, AttributeValue, AttributeName, AttributeTerm, Sample


class DiseaseAdmin(admin.ModelAdmin):
    list_display = ('name',)
    ordering = ('name',)
    search_fields = ('name',)


# Register your models here.
admin.site.register(Disease, DiseaseAdmin)
admin.site.register(Experiment)
admin.site.register(ArrayData)
admin.site.register(AttributeValue)
admin.site.register(AttributeName)
admin.site.register(AttributeTerm)
admin.site.register(Sample)
