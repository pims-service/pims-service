from django.contrib import admin
from .models import Questionnaire, Question, Option, ResponseSet, Response

class OptionInline(admin.TabularInline):
    model = Option
    extra = 3

@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ('content', 'questionnaire', 'type', 'order')
    list_filter = ('questionnaire', 'type')
    inlines = [OptionInline]
    ordering = ('questionnaire', 'order')

class QuestionInline(admin.StackedInline):
    model = Question
    extra = 1

@admin.register(Questionnaire)
class QuestionnaireAdmin(admin.ModelAdmin):
    list_display = ('title', 'is_active', 'created_at')
    list_filter = ('is_active',)
    search_fields = ('title', 'description')
    inlines = [QuestionInline]

class ResponseInline(admin.TabularInline):
    model = Response
    extra = 0
    readonly_fields = ('question', 'selected_option', 'text_value')

@admin.register(ResponseSet)
class ResponseSetAdmin(admin.ModelAdmin):
    list_display = ('user', 'questionnaire', 'status', 'started_at', 'completed_at')
    list_filter = ('status', 'questionnaire')
    search_fields = ('user__username', 'questionnaire__title')
    inlines = [ResponseInline]
    readonly_fields = ('started_at',)

@admin.register(Option)
class OptionAdmin(admin.ModelAdmin):
    list_display = ('label', 'question', 'numeric_value', 'order')
    list_filter = ('question__questionnaire',)
