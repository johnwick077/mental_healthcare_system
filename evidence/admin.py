from django.contrib import admin
from .models import ResearchPaper, ResearchDataset, ObservationPattern


@admin.register(ResearchPaper)
class ResearchPaperAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "source",
        "publication_year",
        "verified",
    )

    list_filter = (
        "source",
        "verified",
        "publication_year",
    )

    search_fields = (
        "title",
        "authors",
        "doi",
    )


@admin.register(ResearchDataset)
class ResearchDatasetAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "sample_size",
    )

    search_fields = (
        "name",
    )


@admin.register(ObservationPattern)
class ObservationPatternAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "minimum_days",
        "active",
    )

    list_filter = (
        "active",
    )

    search_fields = (
        "name",
        "description",
    )