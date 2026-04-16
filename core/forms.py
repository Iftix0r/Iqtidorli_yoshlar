from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User, Skill, Project, Contest, REGIONS, ROLE_CHOICES, Message, Resource
import re


def normalize_phone(phone):
    """998901234567 yoki +998901234567 formatga keltiradi"""
    digits = re.sub(r'\D', '', phone)
    if digits.startswith('998') and len(digits) == 12:
        return '+' + digits
    if len(digits) == 9:
        return '+998' + digits
    return '+' + digits


class RegisterForm(UserCreationForm):
    first_name = forms.CharField(label="Ism", max_length=80,
                                 widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ismingiz'}))
    last_name  = forms.CharField(label="Familiya", max_length=80,
                                 widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Familiyangiz'}))
    phone      = forms.CharField(label="Telefon raqam", max_length=20,
                                 widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+998 90 123 45 67'}))
    role       = forms.ChoiceField(label="Rol", choices=ROLE_CHOICES,
                                   widget=forms.Select(attrs={'class': 'form-control'}))
    region     = forms.ChoiceField(label="Viloyat",
                                   choices=[('', '— Tanlang —')] + REGIONS,
                                   widget=forms.Select(attrs={'class': 'form-control'}))

    class Meta:
        model  = User
        fields = ('first_name', 'last_name', 'phone', 'role', 'region', 'password1', 'password2')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password1'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Parol'})
        self.fields['password2'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Parolni tasdiqlang'})

    def clean_phone(self):
        phone = normalize_phone(self.cleaned_data['phone'])
        if User.objects.filter(phone=phone).exists():
            raise forms.ValidationError("Bu telefon raqam allaqachon ro'yxatdan o'tgan.")
        return phone

    def save(self, commit=True):
        user = super().save(commit=False)
        phone = self.cleaned_data['phone']
        # username avtomatik: telefon raqamdan (+ belgisisiz)
        user.username = re.sub(r'\D', '', phone)
        user.phone    = phone
        if commit:
            user.save()
        return user


class ProfileForm(forms.ModelForm):
    class Meta:
        model  = User
        fields = ('first_name', 'last_name', 'bio', 'region', 'avatar')
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name':  forms.TextInput(attrs={'class': 'form-control'}),
            'bio':        forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Kasb yoki qisqacha tavsif'}),
            'region':     forms.Select(attrs={'class': 'form-control'}),
            'avatar':     forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
        }


class SkillForm(forms.ModelForm):
    class Meta:
        model   = Skill
        fields  = ('skill_name',)
        widgets = {'skill_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': "Ko'nikma nomi"})}


class ProjectForm(forms.ModelForm):
    class Meta:
        model   = Project
        fields  = ('title', 'description', 'link', 'is_startup', 'needs_team', 'funding_amount', 'required_resources', 'image')
        widgets = {
            'title':       forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Loyiha yoki Startap nomi'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Loyiha haqida batafsil ma\'lumot...'}),
            'link':        forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://demo-link.uz'}),
            'funding_amount': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Masalan: $2000 yoki 20,000,000 so\'m'}),
            'required_resources': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Ofis, serverlar, investor, va b.'}),
            'image':       forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
        }


class ContestForm(forms.ModelForm):
    class Meta:
        model   = Contest
        fields  = ('title', 'description', 'deadline', 'prize')
        widgets = {
            'title':       forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'deadline':    forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'prize':       forms.TextInput(attrs={'class': 'form-control', 'placeholder': "50,000,000 so'm"}),
        }


class MessageForm(forms.ModelForm):
    class Meta:
        model   = Message
        fields  = ('body',)
        widgets = {'body': forms.Textarea(attrs={
            'class': 'form-control', 'rows': 2,
            'placeholder': 'Xabar yozing...', 'style': 'resize:none;'
        })}


class ResourceForm(forms.ModelForm):
    class Meta:
        model   = Resource
        fields  = ('title', 'description', 'link', 'res_type')
        widgets = {
            'title':       forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Resurs nomi'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'link':        forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://...'}),
            'res_type':    forms.Select(attrs={'class': 'form-control'}),
        }


from .models import Certificate, ContestApplication, Job


class CertificateForm(forms.ModelForm):
    class Meta:
        model   = Certificate
        fields  = ('title', 'issuer', 'issued_date', 'image', 'link')
        widgets = {
            'title':       forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Sertifikat nomi'}),
            'issuer':      forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Masalan: Coursera, Udemy'}),
            'issued_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'image':       forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
            'link':        forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://...'}),
        }


class ContestApplicationForm(forms.ModelForm):
    class Meta:
        model   = ContestApplication
        fields  = ('motivation',)
        widgets = {'motivation': forms.Textarea(attrs={
            'class': 'form-control', 'rows': 4,
            'placeholder': 'Nima uchun bu tanlovda qatnashmoqchisiz?'
        })}


class JobForm(forms.ModelForm):
    class Meta:
        model   = Job
        fields  = ('title', 'company', 'description', 'job_type', 'location', 'salary', 'skills_req')
        widgets = {
            'title':       forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Lavozim nomi'}),
            'company':     forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Kompaniya nomi'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'job_type':    forms.Select(attrs={'class': 'form-control'}),
            'location':    forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Toshkent / Masofaviy'}),
            'salary':      forms.TextInput(attrs={'class': 'form-control', 'placeholder': "3,000,000 so'm"}),
            'skills_req':  forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Python, Django, React'}),
        }
