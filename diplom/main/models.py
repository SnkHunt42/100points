from django.contrib.auth.models import AbstractUser, Group, Permission
from django.db import models
from django.utils import timezone
from django.conf import settings


class Curdirs(models.Model):
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name


class Regions(models.Model):
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name


class Universities(models.Model):
    name = models.CharField(max_length=255)
    region = models.ForeignKey(Regions, on_delete=models.CASCADE)

    def __str__(self):
        return self.name


class CustomUser(AbstractUser):
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    email = models.EmailField('email address', unique=True)
    username = models.CharField(max_length=150, unique=True, blank=True, null=True)
    fathersname = models.CharField('father\'s name', max_length=100, blank=True, null=True)
    curdir = models.ManyToManyField('Curdirs', blank=True)
    region = models.ForeignKey(Regions, on_delete=models.SET_NULL, null=True, blank=True)
    school = models.CharField('school', max_length=150, blank=True, null=True)
    university = models.ForeignKey(Universities, on_delete=models.SET_NULL, null=True, blank=True)
    number = models.CharField('phone number', max_length=15, blank=True, null=True)
    profile_image = models.ImageField(upload_to='profile_images/', null=True, blank=True)
    lives = models.IntegerField(default=3)

    ROLE_CHOICES = (
        ('participator', 'Участник'),
        ('tutor', 'Тьютор'),
        ('supervisor', 'Наставник'),
        ('areacurator', 'Куратор направления'),
        ('coordinator', 'Координатор проекта'),
        ('zamruk', 'Заместитель руководителя проекта'),
        ('master', 'Руководитель проекта'),
        ('newscreator', 'Новостник'),
    )
    role = models.CharField('role', max_length=50, choices=ROLE_CHOICES, default='participator')

    SEX_CHOICES = (
        ('male', 'Мужской'),
        ('female', 'Женский'),
    )
    sex = models.CharField('sex', max_length=10, choices=SEX_CHOICES)

    def save(self, *args, **kwargs):
        if not self.username:
            self.username = self.email
            if self.role == 'unique_role':
                if CustomUser.objects.filter(role='unique_role').exclude(pk=self.pk).exists():
                    raise ValueError("Редактор новостей уже назначен.")
        super(CustomUser, self).save(*args, **kwargs)

    @property
    def profile_image_url(self):
        if self.profile_image:
            return self.profile_image.url
        else:
            return '/images/defaultpic.png'

    def remove_life(self, tutor):
        if self.lives > 0:
            self.lives -= 1
            self.save()
            if self.lives == 0:
                TutorStudent.objects.filter(student=self, tutor=tutor).delete()  # Отчисление студента
                return True
        return False

    def add_life(self):
        if self.lives < 3:
            self.lives += 1
            self.save()

    def has_role(self, roles):
        return self.role.filter(name__in=role).exists()


class Messenger(models.Model):
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='sent_messages', on_delete=models.CASCADE)
    receiver = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='received_messages', on_delete=models.CASCADE)
    content = models.TextField(blank=True, null=True)
    sticker = models.CharField(max_length=255, blank=True, null=True)
    file = models.FileField(upload_to='uploads/', blank=True, null=True)  # Поле для хранения файлов
    mtime = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    def __str__(self):
        return self.content[:50] if self.content else 'Стикер или файл'


class Question(models.Model):
    email = models.EmailField()
    question = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.email}: {self.question[:20]}...'


class News(models.Model):
    title = models.CharField(max_length=255)
    content = models.TextField()
    author = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


class NewsImage(models.Model):
    news = models.ForeignKey(News, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='news_images/')

    def __str__(self):
        return f"{self.news.title} Image"


class Tasks(models.Model):
    title = models.CharField(max_length=255)
    desc = models.TextField()
    dueto = models.DateTimeField()
    students = models.ManyToManyField('main.CustomUser', related_name='tasks')
    tutor = models.ForeignKey('main.CustomUser', related_name='assigned_tasks', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    file = models.FileField(upload_to='tasks/', null=True, blank=True)

    def __str__(self):
        return self.title


class StudyPlan(models.Model):
    tutor = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='study_plans', on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    description = models.TextField()
    deadline = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title


class TutorStudent(models.Model):
    tutor = models.ForeignKey(CustomUser, related_name='tutor_students', on_delete=models.CASCADE)
    student = models.ForeignKey(CustomUser, related_name='student_tutors', on_delete=models.CASCADE)

    class Meta:
        unique_together = ('tutor', 'student')

    def __str__(self):
        return f'{self.tutor} -> {self.student}'


class Profile(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='profile')
    extra_data = models.JSONField(default=dict)

    def get_extra_data(self, key, default=None):
        return self.extra_data.get(key, default)

    def set_extra_data(self, key, value):
        self.extra_data[key] = value
        self.save()


class TaskSubmission(models.Model):
    task = models.ForeignKey(Tasks, related_name='submissions', on_delete=models.CASCADE)
    student = models.ForeignKey(CustomUser, related_name='submissions', on_delete=models.CASCADE)
    text = models.TextField()
    file = models.FileField(upload_to='submissions/', null=True, blank=True)
    submitted_at = models.DateTimeField(auto_now_add=True)