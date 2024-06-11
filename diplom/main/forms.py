from .models import TaskSubmission, News, StudyPlan, Tasks, Messenger, CustomUser, Curdirs, Regions, Universities
from django.forms import ModelForm, TextInput, Textarea
from django.contrib.auth.forms import UserCreationForm
from django import forms
from django.core.exceptions import ValidationError
from django.core.validators import EmailValidator
from django.utils.translation import gettext_lazy as _
from tempus_dominus.widgets import DateTimePicker


class TaskForm(forms.ModelForm):
    class Meta:
        model = Tasks
        fields = ['title', 'desc', 'dueto', 'file', 'students']
        widgets = {
            'dueto': DateTimePicker(
                options={
                    'useCurrent': True,
                    'collapse': False,
                },
                attrs={
                    'append': 'fa fa-calendar',
                    'icon_toggle': True,
                }
            ),
            'students': forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'})
        }

    def __init__(self, *args, **kwargs):
        tutor = kwargs.pop('tutor', None)
        super(TaskForm, self).__init__(*args, **kwargs)
        if tutor:
            self.fields['students'].queryset = CustomUser.objects.filter(
                student_tutors__tutor=tutor,
                role='participator'
            )
            self.fields['students'].label_from_instance = self.get_user_full_name

    def get_user_full_name(self, user):
        return f"{user.last_name} {user.first_name} {user.fathersname}"


class ChangeLivesForm(forms.Form):
    ACTION_CHOICES = [
        ('add', 'Добавить жизнь'),
        ('remove', 'Убрать жизнь')
    ]
    action = forms.ChoiceField(choices=ACTION_CHOICES, widget=forms.HiddenInput())


class TaskSubmissionForm(forms.ModelForm):
    class Meta:
        model = TaskSubmission
        fields = ['file', 'text']
        widgets = {
            'text': forms.Textarea(attrs={'class': 'form-control'}),
        }
        labels ={
            'file': 'Файл решения',
            'text': 'Решение',
        }


class StudyPlanForm(forms.ModelForm):
    class Meta:
        model = StudyPlan
        fields = ['title', 'description', 'deadline']
        widgets = {
            'deadline': forms.DateInput(attrs={'type': 'date'})
        }
        labels ={
            'title': 'Название пункта',
            'description': 'Описание пункта',
            'deadline': 'Дедлайн',
        }


class LoginForm(forms.Form):
    email = forms.EmailField(label='Email', max_length=255)
    password = forms.CharField(label='Пароль', widget=forms.PasswordInput)


class ProfileForm(ModelForm):
    class Meta:
        model = CustomUser
        fields = ['first_name', 'last_name', 'email', 'fathersname', 'curdir', 'region', 'school', 'university', 'number']

    def __init__(self, *args, **kwargs):
        super(ProfileForm, self).__init__(*args, **kwargs)
        user = self.instance
        if user:
            for field_name in self.fields:
                self.fields[field_name].initial = getattr(user, field_name, None)

    def save(self, commit=True):
        user = super(ProfileForm, self).save(commit=False)
        if commit:
            user.save()
        return user


class ProfileImageForm(forms.ModelForm):
    remove_image = forms.BooleanField(required=False, label="Remove image")

    class Meta:
        model = CustomUser
        fields = ['profile_image']

    def save(self, commit=True):
        user = super().save(commit=False)
        if self.cleaned_data.get('remove_image'):
            user.profile_image.delete(save=False)
            user.profile_image = None
        if commit:
            user.save()
        return user


class CustomUserCreationForm(UserCreationForm):
    last_name = forms.CharField(max_length=100, label='Фамилия', required=True)
    first_name = forms.CharField(max_length=100, label='Имя', required=True)
    fathersname = forms.CharField(max_length=100, label='Отчество', required=False)
    curdir = forms.ModelChoiceField(queryset=Curdirs.objects.all(), label='Направление кураторства', required=True)
    region = forms.ModelChoiceField(queryset=Regions.objects.all(), label='Регион проживания', required=True)
    school = forms.CharField(max_length=100, label='Образовательная учреждение', required=True)
    university = forms.ModelChoiceField(queryset=Universities.objects.all(), label='Университет', required=True)
    number = forms.CharField(max_length=15, label='Номер телефона', required=True)
    email = forms.EmailField(
        label='Адрес электронной почты',
        validators=[EmailValidator(message=_("Пожалуйста, введите правильный адрес электронной почты."))],
        required=True
    )
    sex = forms.ChoiceField(choices=CustomUser.SEX_CHOICES, label='Пол', required=True)

    class Meta:
        model = CustomUser
        fields = [
            'email', 'password1', 'password2', 'sex', 'first_name',
            'last_name', 'fathersname', 'curdir',
            'region', 'school', 'university', 'number'
        ]

    def clean_email(self):
        email = self.cleaned_data.get('email', '').lower()
        if CustomUser.objects.filter(email__iexact=email).exists():
            raise ValidationError(_('Пользователь с такой электронной почтой уже существует.'))
        return email

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'region' in self.data:
            try:
                region_id = int(self.data.get('region'))
                self.fields['university'].queryset = Universities.objects.filter(region_id=region_id).order_by('name')
            except (ValueError, TypeError):
                pass
        else:
            self.fields['university'].queryset = Universities.objects.none()


class ParticipatorForm(CustomUserCreationForm):
    def __init__(self, *args, **kwargs):
        super(ParticipatorForm, self).__init__(*args, **kwargs)
        self.fields['school'].required = True
        self.fields.pop('university', None)
        self.fields.pop('curdir', None)

        self.fields['curdir'] = forms.ModelMultipleChoiceField(
            queryset=Curdirs.objects.all(),
            widget=forms.CheckboxSelectMultiple,
            required=True,
            label="Направления"
        )


class TutorForm(CustomUserCreationForm):
    def __init__(self, *args, **kwargs):
        super(TutorForm, self).__init__(*args, **kwargs)
        self.fields['university'].required = True
        self.fields.pop('school', None)
        self.fields.pop('curdir', None)

        self.fields['curdir'] = forms.ModelChoiceField(
            queryset=Curdirs.objects.all(),
            required=True,
            label="Направление"
        )


class SupervisorForm(CustomUserCreationForm):
    def __init__(self, *args, **kwargs):
        super(SupervisorForm, self).__init__(*args, **kwargs)
        self.fields['university'].required = True
        self.fields.pop('school', None)
        self.fields.pop('curdir', None)

        self.fields['curdir'] = forms.ModelChoiceField(
            queryset=Curdirs.objects.all(),
            required=True,
            label="Направление"
        )


class AreaCuratorForm(CustomUserCreationForm):
    def __init__(self, *args, **kwargs):
        super(AreaCuratorForm, self).__init__(*args, **kwargs)
        self.fields['curdir'].required = True
        self.fields['university'].required = True
        self.fields.pop('school', None)

        self.fields['curdir'] = forms.ModelChoiceField(
            queryset=Curdirs.objects.all(),
            required=True,
            label="Направление"
        )


class CoordinatorForm(CustomUserCreationForm):
    def __init__(self, *args, **kwargs):
        super(CoordinatorForm, self).__init__(*args, **kwargs)
        self.fields.pop('curdir', None)
        self.fields.pop('university', None)
        self.fields.pop('school', None)


class ZamRukForm(CustomUserCreationForm):
    def __init__(self, *args, **kwargs):
        super(ZamRukForm, self).__init__(*args, **kwargs)
        self.fields.pop('curdir', None)
        self.fields.pop('university', None)
        self.fields.pop('school', None)


class MasterForm(CustomUserCreationForm):
    def __init__(self, *args, **kwargs):
        super(MasterForm, self).__init__(*args, **kwargs)
        self.fields.pop('curdir', None)
        self.fields.pop('university', None)
        self.fields.pop('school', None)


class NewsCreatorForm(CustomUserCreationForm):
    def __init__(self, *args, **kwargs):
        super(NewsCreatorForm, self).__init__(*args, **kwargs)
        self.fields.pop('school', None)
        self.fields.pop('curdir', None)
        self.fields.pop('university', None)


class MessageForm(forms.ModelForm):
    class Meta:
        model = Messenger
        fields = ['content', 'sticker', 'file']
        widgets = {
            'content': forms.Textarea(attrs={
                'rows': 3,
                'placeholder': 'Напишите сообщение...',
                'style': 'height: 50px;'  # Initial height for the textarea
            }),
            'sticker': forms.HiddenInput(),
            'file': forms.ClearableFileInput(attrs={'multiple': False}),
        }


class NewsForm(forms.ModelForm):
    image = forms.ImageField(required=False, label='Изображение')

    class Meta:
        model = News
        fields = ['title', 'content']
        labels = {
            'title': 'Заголовок',
            'content': 'Содержание',
            'image': 'Изображение',
        }