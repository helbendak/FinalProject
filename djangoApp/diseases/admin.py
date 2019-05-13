from django.contrib import admin
from .models import Disease, Experiment, AttributeValue, AttributeName, AttributeTerm, Sample, Gene


class DiseaseAdmin(admin.ModelAdmin):
    list_display = ('name',)
    ordering = ('name',)
    search_fields = ('name',)


class AttributeValueInline(admin.TabularInline):
    model = AttributeValue
    exclude = ['name']
    extra = 0


class AttributeTermInline(admin.TabularInline):
    model = AttributeTerm
    extra = 0


class SampleAdmin(admin.ModelAdmin):
    inlines = [AttributeValueInline, ]


class AttributeNameAdmin(admin.ModelAdmin):
    inlines = [AttributeTermInline, ]


# Register your models here.
admin.site.register(Disease, DiseaseAdmin)
admin.site.register(Experiment)
admin.site.register(AttributeValue)
admin.site.register(AttributeName, AttributeNameAdmin)
admin.site.register(AttributeTerm)
admin.site.register(Sample, SampleAdmin)
admin.site.register(Gene)
