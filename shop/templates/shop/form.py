from django import forms
from django.contrib.auth.forms import AuthenticationForm

class CustomAuthenticationForm(AuthenticationForm):
    username = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Tên đăng nhập'}),
        error_messages={'required': 'Vui lòng nhập tên đăng nhập'}
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Mật khẩu'}),
        error_messages={'required': 'Vui lòng nhập mật khẩu'}
    )
    
    def clean(self):
        username = self.cleaned_data.get('username')
        password = self.cleaned_data.get('password')
        
        if username and password:
            # Kiểm tra độ dài username
            if len(username) < 3:
                raise forms.ValidationError('Tên đăng nhập phải có ít nhất 3 ký tự')
            
            # Kiểm tra username quá dài
            if len(username) > 30:
                raise forms.ValidationError('Tên đăng nhập không được quá 30 ký tự')
            
            # Kiểm tra độ dài password
            if len(password) < 8:
                raise forms.ValidationError('Mật khẩu phải có ít nhất 8 ký tự')
            
            # Kiểm tra password quá dài
            if len(password) > 128:
                raise forms.ValidationError('Mật khẩu không được quá 128 ký tự')
        
        return super().clean()