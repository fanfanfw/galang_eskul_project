from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import CustomUser

class CreateUserForm(UserCreationForm):
    nama_lengkap = forms.CharField(max_length=100, widget=forms.TextInput(attrs={'class': 'form-control'}))
    no_telepon = forms.CharField(max_length=15, required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    alamat = forms.CharField(required=False, widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3}))
    foto_profil = forms.ImageField(required=False, widget=forms.FileInput(attrs={'class': 'form-control'}))
    
    class Meta:
        model = CustomUser
        fields = ('username', 'email', 'nama_lengkap', 'no_telepon', 'alamat', 'foto_profil', 'password1', 'password2')
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({'class': 'form-control'})
        self.fields['email'].widget.attrs.update({'class': 'form-control'})
        self.fields['password1'].widget.attrs.update({'class': 'form-control'})
        self.fields['password2'].widget.attrs.update({'class': 'form-control'})
        
    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = 'pelatih'  # Default role untuk user yang dibuat admin
        if commit:
            user.save()
        return user