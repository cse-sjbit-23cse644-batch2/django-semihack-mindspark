from django import forms
from .models import Syllabus

class SyllabusForm(forms.ModelForm):
    class Meta:
        model = Syllabus
        fields = '__all__'