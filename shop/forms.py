from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError

class CustomUserCreationForm(UserCreationForm):
    username = forms.CharField(
        label='Tên đăng nhập',
        help_text='Tối đa 150 ký tự. Chỉ bao gồm chữ, số và @/./+/-/_'
    )
    password1 = forms.CharField(
        label='Mật khẩu',
        widget=forms.PasswordInput,
        help_text='Mật khẩu phải dài ít nhất 8 ký tự và không quá đơn giản.'
    )
    password2 = forms.CharField(
        label='Xác nhận mật khẩu',
        widget=forms.PasswordInput,
        help_text='Nhập lại mật khẩu giống như ở trên.'
    )

    class Meta:
        model = User
        fields = ['username', 'password1', 'password2']
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Ghi đè thông báo lỗi mặc định
        self.error_messages.update({
            'password_mismatch': 'Hai mật khẩu không khớp với nhau.',
            'password_too_short': 'Mật khẩu quá ngắn. Cần ít nhất 8 ký tự.',
            'password_too_similar': 'Mật khẩu quá giống với tên đăng nhập.',
            'password_entirely_numeric': 'Mật khẩu không thể chỉ chứa số.',
            'password_too_common': 'Mật khẩu quá phổ biến và dễ đoán.',
        })
    
    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise ValidationError(
                self.error_messages['password_mismatch'],
                code='password_mismatch',
            )
        return password2
    
    # Hàm tùy chỉnh để thay đổi thông báo lỗi khi kiểm tra mật khẩu
    def _password_validators_help_text_html(self):
        help_text = super()._password_validators_help_text_html()
        # Thay thế các phần tiếng Anh bằng tiếng Việt nếu cần
        return help_text
        
    def _post_clean(self):
        super()._post_clean()
        # Chuyển đổi thông báo lỗi validator sang tiếng Việt
        for field in ['password1', 'password2']:
            if field in self._errors:
                error_list = []
                for error in self._errors[field]:
                    if "too similar to the username" in error:
                        error_list.append("Mật khẩu quá giống với tên đăng nhập.")
                    elif "too short" in error:
                        error_list.append("Mật khẩu quá ngắn. Cần ít nhất 8 ký tự.")
                    elif "entirely numeric" in error:
                        error_list.append("Mật khẩu không thể chỉ chứa số.")
                    elif "too common" in error:
                        error_list.append("Mật khẩu quá phổ biến và dễ đoán.")
                    elif "must contain at least" in error:
                        error_list.append("Mật khẩu phải chứa ít nhất 8 ký tự.")
                    elif "didn't match" in error:
                        error_list.append("Hai mật khẩu không khớp với nhau.")
                    else:
                        error_list.append(error)
                
                if error_list:
                    self._errors[field] = self.error_class(error_list)
