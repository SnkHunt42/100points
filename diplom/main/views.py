from django.shortcuts import render, redirect, get_object_or_404
from .models import Question, TaskSubmission, NewsImage, News, StudyPlan, Tasks, Universities, Messenger, TutorStudent
from .forms import ProfileImageForm, ChangeLivesForm, TaskSubmissionForm, NewsForm, NewsCreatorForm, StudyPlanForm, MessageForm, LoginForm, TaskForm, ParticipatorForm, TutorForm, SupervisorForm, AreaCuratorForm, CoordinatorForm, ZamRukForm, MasterForm
from django.urls import reverse_lazy, reverse
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse
from django.contrib import messages, auth
from django.contrib.auth import authenticate, login
import json, logging
from urllib.parse import urlencode
from django.views.generic import CreateView, View
from django.http import Http404, HttpResponseRedirect, HttpResponseForbidden
from django.conf import settings
from django.templatetags.static import static
from .models import CustomUser, Regions, Curdirs
from django.db.models import Q, Max, Count
from django import forms
from django.core.paginator import Paginator
from .decorators import role_required
import openpyxl
from openpyxl.styles import Font


logger = logging.getLogger(__name__)


ROLE_CHOICES = {
    'participator': 'Участник',
    'tutor': 'Тьютор',
    'supervisor': 'Наставник',
    'areacurator': 'Куратор направления',
    'coordinator': 'Координатор проекта',
    'zamruk': 'Заместитель руководителя проекта',
    'master': 'Руководитель проекта',
    'newscreator': 'Новостник'}


def login_view(request):
    storage = messages.get_messages(request)
    list(storage)

    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            user = authenticate(request, username=email, password=password)
            if user is not None:
                login(request, user)
                return redirect(reverse('profile', kwargs={'user_id': user.id}))
            else:
                messages.error(request, 'Неправильный адрес электронной почты или пароль', extra_tags='login')
    else:
        form = LoginForm()

    return render(request, 'main/login.html', {'form': form})


def index(request):
    news = News.objects.all()
    return render(request, 'main/index.html', {
        'title': 'Главная страница',
        'news': news,
    })


def news_detail(request, pk):
    news = get_object_or_404(News, pk=pk)
    return render(request, 'main/news_detail.html', {
        'title': news.title,
        'news': news
    })


def about(request):
    return render(request, 'main/about.html', {'title': 'О нас'})


@login_required
@role_required(allowed_roles=['newscreator'])
def news(request):
    news = News.objects.all()
    return render(request, 'main/news.html', {'news': news, 'title': 'Новости'})


@login_required
@role_required(allowed_roles=['newscreator'])
def news_create(request):
    if request.method == 'POST':
        form = NewsForm(request.POST, request.FILES)
        if form.is_valid():
            news = form.save(commit=False)
            news.author = request.user
            news.save()
            image = request.FILES.get('image')
            if image:
                NewsImage.objects.create(news=news, image=image)
            return redirect('news')
        else:
            print("Форма не валидна", form.errors)  # Для отладки ошибок формы
    else:
        form = NewsForm()
    return render(request, 'main/news_form.html', {'form': form, 'title': 'Добавить новость'})


@login_required
@role_required(allowed_roles=['newscreator'])
def news_update(request, pk):
    news = get_object_or_404(News, pk=pk)
    if request.method == 'POST':
        form = NewsForm(request.POST, request.FILES, instance=news)
        if form.is_valid():
            news = form.save(commit=False)
            news.save()
            image = request.FILES.get('image')
            if image:
                NewsImage.objects.create(news=news, image=image)
            return redirect('news')
    else:
        form = NewsForm(instance=news)
    return render(request, 'main/news_form.html', {'form': form, 'title': 'Редактировать новость'})


@login_required
@role_required(allowed_roles=['newscreator'])
def news_delete(request, pk):
    news = get_object_or_404(News, pk=pk)
    if request.method == 'POST':
        news.delete()
        return redirect('news')
    return render(request, 'main/news_confirm_delete.html', {'news': news, 'title': 'Удалить новость'})


@login_required
@role_required(allowed_roles=['participator'])
def tutors(request):
    current_user = request.user
    tutor_students = TutorStudent.objects.filter(student=current_user).select_related('tutor')
    return render(request, 'main/tutors.html', {'tutor_students': tutor_students, 'title': 'Тьюторы'})


@login_required
def participants(request):
    query = request.GET.get('q', '')
    university_id = request.GET.get('university', '')
    region_id = request.GET.get('region', '')
    curdir_id = request.GET.get('curdir', '')
    role = request.GET.get('role', '')

    users = CustomUser.objects.all()

    if query:
        users = users.filter(
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query) |
            Q(fathersname__icontains=query)
        )

    if university_id:
        users = users.filter(university_id=university_id)

    if region_id:
        users = users.filter(region_id=region_id)

    if curdir_id:
        users = users.filter(curdir__id=curdir_id)

    if role:
        users = users.filter(role=role)

    paginator = Paginator(users, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    print(f"Total users: {users.count()}")
    for user in users:
        print(f"{user.last_name} {user.first_name} {user.fathersname}")

    context = {
        'title': 'Участники проекта',
        'page_obj': page_obj,
        'universities': Universities.objects.all(),
        'regions': Regions.objects.all(),
        'curdirs': Curdirs.objects.all(),
    }

    return render(request, 'main/participants.html', context)


@login_required
def conversation_detail(request, user_id):
    other_user = get_object_or_404(CustomUser, id=user_id)
    messages_queryset = Messenger.objects.filter(
        (Q(sender=request.user) & Q(receiver=other_user)) |
        (Q(sender=other_user) & Q(receiver=request.user))
    ).order_by('mtime')

    messages_queryset.filter(receiver=request.user, is_read=False).update(is_read=True)

    if request.method == "POST":
        form = MessageForm(request.POST, request.FILES)
        if form.is_valid():
            message = form.save(commit=False)
            message.sender = request.user
            message.receiver = other_user
            message.save()
            return redirect('conversation_detail', user_id=other_user.id)
    else:
        form = MessageForm()

    stickers = [
        '4smiles.png', 'awkward.png', 'clown.png', 'clumsy.png', 'confused.png',
        'eggy.png', 'ehm.png', 'flowey.png', 'wow.png', 'kitty.png',
        'mystery.png', 'nosey.png', 'peekaboo.png', 'star.png', 'stars.png',
        'smile.png', 'uhoh.png', 'whatsup.png', 'yay.png', 'yikes.png'
    ]

    return render(request, 'main/conversation_detail.html', {
        'messages': messages_queryset,
        'form': form,
        'other_user': other_user,
        'stickers': stickers,
    })


@login_required
def remove_file(request, message_id):
    message = get_object_or_404(Messenger, id=message_id, sender=request.user)
    message.file.delete()
    message.file = None
    message.save()
    return JsonResponse({'status': 'success'})


@login_required
@role_required(allowed_roles=['tutor', 'participator', 'areacurator'])
def study_plan(request):
    study_plans = []

    if request.user.role == 'tutor':
        study_plans = StudyPlan.objects.filter(tutor=request.user)
    elif request.user.role == 'participator':
        tutor_students = TutorStudent.objects.filter(student=request.user)
        tutors = [ts.tutor for ts in tutor_students]
        study_plans = StudyPlan.objects.filter(tutor__in=tutors)
    elif request.user.role == 'areacurator':
        study_plans = StudyPlan.objects.filter(tutor__curdir=request.user.curdir)

    return render(request, 'main/study_plan.html', {
        'title': 'Учебный план',
        'study_plans': study_plans,
        'can_add': request.user.role == 'tutor',
        'can_edit': request.user.role == 'tutor'
    })


@login_required
@role_required(allowed_roles=['tutor'])
def add_study_plan(request):
    if request.user.role != 'tutor':
        return redirect('study_plan')

    if request.method == 'POST':
        form = StudyPlanForm(request.POST)
        if form.is_valid():
            study_plan = form.save(commit=False)
            study_plan.tutor = request.user
            study_plan.save()
            return redirect('study_plan')
    else:
        form = StudyPlanForm()
    return render(request, 'main/add_study_plan.html', {'form': form, 'title': 'Добавить пункт учебного плана'})


@login_required
@role_required(allowed_roles=['tutor'])
def edit_study_plan(request, plan_id):
    study_plan = get_object_or_404(StudyPlan, id=plan_id)
    if request.user.role != 'tutor':
        return redirect('study_plan')

    if request.method == 'POST':
        form = StudyPlanForm(request.POST, instance=study_plan)
        if form.is_valid():
            form.save()
            return redirect('study_plan')
    else:
        form = StudyPlanForm(instance=study_plan)
    return render(request, 'main/edit_study_plan.html', {'form': form, 'title': 'Редактировать пункт учебного плана'})


@login_required
@role_required(allowed_roles=['tutor'])
def delete_study_plan(request, plan_id):
    study_plan = get_object_or_404(StudyPlan, id=plan_id)
    if request.user.role != 'tutor':
        return redirect('study_plan')

    if request.method == 'POST':
        study_plan.delete()
        return redirect('study_plan')
    return render(request, 'main/delete_study_plan.html', {'study_plan': study_plan, 'title': 'Удалить пункт учебного плана'})


@login_required
@role_required(allowed_roles=['areacurator'])
def working_program(request):
    current_user = request.user

    if current_user.role != 'areacurator':
        return HttpResponseForbidden("У вас нет доступа к этой странице.")

    user_curdirs = current_user.curdir.all()

    tutors = CustomUser.objects.filter(curdir__in=user_curdirs, role='tutor').distinct()

    tutors_plans = {tutor: tutor.study_plans.all() for tutor in tutors}

    return render(request, 'main/working_program.html', {'tutors': tutors_plans})


@login_required
@role_required(allowed_roles=['tutor'])
def my_students(request):
    current_user = request.user
    tutor_students = TutorStudent.objects.filter(tutor=current_user).select_related('student')

    students = [ts.student for ts in tutor_students]

    return render(request, 'main/my_students.html', {
        'title': 'Мои ученики',
        'students': students,
    })


@login_required
@role_required(allowed_roles=['tutor'])
def tasks(request):
    tutor_students = TutorStudent.objects.filter(tutor=request.user).values_list('student', flat=True)
    tasks = Tasks.objects.filter(students__in=tutor_students).distinct()
    return render(request, 'main/tasks.html', {'tasks': tasks, 'title': 'Задания'})


@login_required
@role_required(allowed_roles=['tutor'])
def view_task_tutor(request, task_id):
    try:
        task_id = int(task_id)
    except ValueError:
        raise Http404("Invalid task ID")

    task = get_object_or_404(Tasks, id=task_id, tutor=request.user)
    submissions = TaskSubmission.objects.filter(task=task)
    return render(request, 'main/view_task_tutor.html', {'task': task, 'submissions': submissions, 'title': task.title})


@login_required
@role_required(allowed_roles=['participator'])
def view_task_student(request, task_id):
    task = get_object_or_404(Tasks, id=task_id, students=request.user)

    if request.method == 'POST':
        form = TaskSubmissionForm(request.POST, request.FILES)
        if form.is_valid():
            submission = form.save(commit=False)
            submission.task = task
            submission.student = request.user
            submission.save()
            messages.success(request, 'Задание отправлено на проверку.')
            return redirect('my_tasks')
    else:
        form = TaskSubmissionForm()

    return render(request, 'main/view_task_student.html', {'task': task, 'form': form, 'title': task.title})


@login_required
@role_required(allowed_roles=['participator'])
def my_tasks(request):
    tasks = Tasks.objects.filter(students=request.user)
    return render(request, 'main/my_tasks.html', {'tasks': tasks, 'title': 'Мои задания'})


@login_required
@role_required(allowed_roles=['tutor'])
def edit_task(request, task_id):
    task = get_object_or_404(Tasks, id=task_id)
    if request.method == 'POST':
        form = TaskForm(request.POST, request.FILES, instance=task, tutor=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Задание обновлено.')
            return redirect('tasks')
    else:
        form = TaskForm(instance=task, tutor=request.user)
    return render(request, 'main/edit_task.html', {'form': form, 'title': 'Редактирование задания', 'task': task})


@login_required
@role_required(allowed_roles=['tutor'])
def delete_task(request, task_id):
    task = get_object_or_404(Tasks, id=task_id)
    if request.method == 'POST':
        task.delete()
        messages.success(request, 'Задание удалено.')
        return redirect('tasks')
    return render(request, 'main/delete_task.html', {'task': task, 'title': 'Удаление задания'})


@login_required
@role_required(allowed_roles=['tutor'])
def create_task(request):
    if request.method == 'POST':
        form = TaskForm(request.POST, request.FILES, tutor=request.user)
        if form.is_valid():
            task = form.save(commit=False)
            task.tutor = request.user
            task.save()
            form.save_m2m()  # Сохраняем связи многие ко многим
            messages.success(request, 'Задание создано.')
            return redirect('tasks')
        else:
            print(form.errors)
    else:
        form = TaskForm(tutor=request.user)
        print(f"Form initialized for tutor: {request.user}")
    return render(request, 'main/create_task.html', {'form': form, 'title': 'Создание задания'})


@login_required
@role_required(allowed_roles=['tutor'])
def task_statistics(request, task_id):
    task = get_object_or_404(Tasks, id=task_id)
    students = CustomUser.objects.filter(tasks=task)
    return render(request, 'main/task_statistics.html', {'task': task, 'title': 'Статистика задания'})


@login_required
@role_required(allowed_roles=['areacurator', 'tutor', 'supervisor'])
def my_team(request):
    current_user = request.user
    curdir_ids = current_user.curdir.values_list('id', flat=True)

    tutors = CustomUser.objects.filter(role='tutor', curdir__in=curdir_ids).distinct()

    tutor_students = {}
    for tutor in tutors:
        students = TutorStudent.objects.filter(tutor=tutor).select_related('student')
        tutor_students[tutor] = [ts.student for ts in students]

    context = {
        'title': 'Моя команда',
        'tutors': tutor_students
    }
    return render(request, 'main/my_team.html', context)


@login_required
@role_required(allowed_roles=['master', 'zamruk'])
def statistics(request):
    return render(request, 'main/statistics.html', {'title': 'Статистика'})


def get_unread_counts(user):
    unread_counts = Messenger.objects.filter(receiver=user, is_read=False).values('sender').annotate(total=Count('id'))
    return unread_counts


@login_required
def base_view(request):
    unread_messages = Messenger.objects.filter(receiver=request.user, is_read=False).count()
    return {'unread_messages': unread_messages}


@login_required
def messenger(request):
    user = request.user
    messages_queryset = Messenger.objects.filter(
        Q(sender=user) | Q(receiver=user)
    ).order_by('-mtime')

    participants = {}
    for message in messages_queryset:
        if message.sender == user:
            participant = message.receiver
        else:
            participant = message.sender

        if participant not in participants or message.mtime > participants[participant].mtime:
            participants[participant] = message

    unread_counts = Messenger.objects.filter(receiver=user, is_read=False).values('sender').annotate(total=Count('id'))
    unread_dict = {item['sender']: item['total'] for item in unread_counts}

    return render(request, 'main/messenger.html', {
        'title': 'Мессенджер',
        'participants': participants,
        'unread_dict': unread_dict
    })


@login_required
def send_message(request):
    stickers = [
        {'name': 'smile', 'url': '/static/stickers/smile.png'},
        {'name': 'sad', 'url': '/static/stickers/4smiles.png'},
        {'name': 'awkward', 'url': '/static/stickers/awkward.png'},
        {'name': 'clumsy', 'url': '/static/stickers/clumsy.png'},
        {'name': 'confused', 'url': '/static/stickers/confused.png'},
        {'name': 'eggy', 'url': '/static/stickers/eggy.png'},
        {'name': 'ehm', 'url': '/static/stickers/ehm.png'},
        {'name': 'flowey', 'url': '/static/stickers/flowey.png'},
        {'name': 'kitty', 'url': '/static/stickers/kitty.png'},
        {'name': 'mystery', 'url': '/static/stickers/mystery.png'},
        {'name': 'nosey', 'url': '/static/stickers/nosey.png'},
        {'name': 'peekaboo', 'url': '/static/stickers/peekaboo.png'},
        {'name': 'star', 'url': '/static/stickers/star.png'},
        {'name': 'stars', 'url': '/static/stickers/stars.png'},
        {'name': 'uhoh', 'url': '/static/stickers/uhoh.png'},
        {'name': 'whatsup', 'url': '/static/stickers/whatsup.png'},
        {'name': 'wow', 'url': '/static/stickers/wow.png'},
        {'name': 'yay', 'url': '/static/stickers/yay.png'},
        {'name': 'yikes', 'url': '/static/stickers/yikes.png'},
    ]

    if request.method == "POST":
        form = MessageForm(request.POST, request.FILES)
        if form.is_valid():
            message = form.save(commit=False)
            message.sender = request.user
            message.save()
            return redirect('inbox')
    else:
        form = MessageForm()
    return render(request, 'main/send_message.html', {
        'form': form,
        'title': 'Отправить сообщение',
        'stickers': stickers,
    })


def create(request):
    error = ''
    if request.method == 'POST':
        form = TaskForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('home')
        else:
            error = 'Форма была неверной'

    form = TaskForm()
    context = {
        'form': form,
        'error': error
    }
    return render(request, 'main/create.html', context)


@login_required
@role_required(allowed_roles=['areacurator'])
def division(request):
    query = request.GET.get('q')
    university_id = request.GET.get('university')
    region_id = request.GET.get('region')

    curdir_ids = request.user.curdir.values_list('id', flat=True)

    students = CustomUser.objects.filter(
        role='participator',
        curdir__in=curdir_ids
    ).distinct()

    already_assigned_student_ids = TutorStudent.objects.filter(
        tutor__curdir__in=curdir_ids
    ).values_list('student_id', flat=True)

    students = students.exclude(id__in=already_assigned_student_ids)

    if query:
        students = students.filter(
            first_name__icontains=query) | students.filter(
            last_name__icontains=query) | students.filter(
            fathersname__icontains=query)

    if region_id:
        students = students.filter(region_id=region_id)

    print(f"Query: {query}")
    print(f"University ID: {university_id}")
    print(f"Region ID: {region_id}")
    print(f"Filtered Students: {students}")

    context = {
        'title': 'Распределение',
        'students': students,
        'universities': Universities.objects.all(),
        'regions': Regions.objects.all(),
        'curdirs': request.user.curdir.all(),
    }
    return render(request, 'main/division.html', context)


@login_required
@role_required(allowed_roles=['areacurator'])
def assign_tutors(request):
    current_user = request.user
    curdir_ids = current_user.curdir.values_list('id', flat=True)

    if request.method == 'POST':
        student_ids = request.POST.getlist('students')
        print(f"Selected student IDs from POST: {student_ids}")  # Debug log

        if student_ids:
            students = CustomUser.objects.filter(id__in=student_ids, role='participator', curdir__in=curdir_ids).distinct()
        else:
            students = CustomUser.objects.none()

        tutors = CustomUser.objects.filter(role='tutor', curdir__in=curdir_ids).distinct()

        context = {
            'students': students,
            'tutors': tutors
        }
        return render(request, 'main/assign_tutors.html', context)

    return HttpResponseRedirect(reverse('division'))


@login_required
@role_required(allowed_roles=['areacurator'])
def confirm_assignment(request):
    if request.method == 'POST':
        tutor_id = request.POST.get('tutor')
        student_ids = request.POST.getlist('students')
        print(f"Received tutor ID: {tutor_id}")  # Debug log
        print(f"Received student IDs from POST: {student_ids}")  # Debug log

        if not student_ids or not tutor_id:
            print("Missing student_ids or tutor_id")  # Debug log
            messages.error(request, "Пожалуйста, выберите участников и тьютора.")
            return HttpResponseRedirect(reverse('assign_tutors') + '?' + urlencode({'students': ','.join(student_ids)}))

        tutor = get_object_or_404(CustomUser, id=tutor_id, role='tutor')
        students = CustomUser.objects.filter(id__in=student_ids, role='participator')

        if 'confirm' in request.POST:
            for student in students:
                TutorStudent.objects.get_or_create(tutor=tutor, student=student)
            messages.success(request, f"Участники успешно привязаны к тьютору {tutor.first_name} {tutor.last_name}.")
            return HttpResponseRedirect(
                reverse('assign_tutors') + '?' + urlencode({'students': ','.join(map(str, student_ids))}))

        context = {
            'tutor': tutor,
            'students': students
        }
        return render(request, 'main/confirm_assignment.html', context)

    return HttpResponseRedirect(
        reverse('assign_tutors') + '?' + urlencode({'students': ','.join(map(str, request.GET.getlist('students')))}))


def contacts(request):
    if request.method == 'POST' and 'email' in request.POST and 'question' in request.POST:
        email = request.POST['email']
        question = request.POST['question']
        Question.objects.create(email=email, question=question)
        return HttpResponseRedirect(reverse('contacts'))

    questions = []
    can_delete = False
    if request.user.is_authenticated:
        if request.user.role in ['zamruk', 'master']:
            can_delete = True
            questions = Question.objects.all()

    return render(request, 'main/contacts.html', {
        'title': 'Контакты',
        'questions': questions,
        'can_delete': can_delete,
    })


def delete_question(request, question_id):
    if request.user.is_authenticated and request.user.role in ['zamruk', 'master']:
        question = Question.objects.get(id=question_id)
        question.delete()
    return redirect('contacts')


@login_required
def delete_question(request, question_id):
    question = Question.objects.get(id=question_id)
    if request.user.role in ['zamruk', 'master']:
        question.delete()
    return redirect('contacts')


class SignUp(CreateView):
    template_name = 'main/signup.html'
    success_url = reverse_lazy('login')
    initial_role = 'participator'

    ROLE_FORM_MAPPING = {
        'participator': ParticipatorForm,
        'tutor': TutorForm,
        'supervisor': SupervisorForm,
        'areacurator': AreaCuratorForm,
        'coordinator': CoordinatorForm,
        'zamruk': ZamRukForm,
        'master': MasterForm,
        'newscreator': NewsCreatorForm,
    }

    def get_form_class(self):
        role = self.request.POST.get('role', self.initial_role)
        return self.ROLE_FORM_MAPPING.get(role, ParticipatorForm)

    def form_invalid(self, form):
        logger.error(f"Form is invalid: {form.errors.as_json()}")
        if self.request.headers.get('x-requested-with') == 'XMLHttpRequest':
            errors = json.loads(form.errors.as_json())
            return JsonResponse({'success': False, 'errors': errors}, status=400)
        else:
            for error in form.errors.values():
                messages.error(self.request, error)
            return super().form_invalid(form)

    def form_valid(self, form):
        user = form.save(commit=False)
        user.role = self.request.POST.get('role', self.initial_role)
        user.save()

        curdir_field = form.fields.get('curdir')
        if isinstance(curdir_field, forms.ModelMultipleChoiceField):
            form.save_m2m()  # Save ManyToMany data
        elif isinstance(curdir_field, forms.ModelChoiceField):
            user.curdir.set([form.cleaned_data['curdir']])  # Save single selected direction

        if self.request.headers.get('x-requested-with') == 'XMLHttpRequest':
            self.object = user
            return JsonResponse({'success': True, 'redirect_url': self.get_success_url()})
        else:
            return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['initial_role'] = self.initial_role
        return context


def load_universities(request):
    region_id = request.GET.get('region')
    universities = Universities.objects.filter(region_id=region_id).order_by('name')
    return JsonResponse(list(universities.values('id', 'name')), safe=False)


class GetFieldsView(View):
    def get(self, request, *args, **kwargs):
        role = kwargs.get('role')
        form_class = SignUp.ROLE_FORM_MAPPING.get(role)
        if form_class:
            form = form_class()
            extra_fields_html = form.as_p()
            return JsonResponse({'extra_fields_html': extra_fields_html})
        else:
            return JsonResponse({'error': 'Role not defined'}, status=400)


@login_required
def delete_profile_image(request):
    user = request.user
    if user.profile_image:
        user.profile_image.delete(save=False)
        user.profile_image = None
        user.save()
    return redirect('profile', user_id=user.id)


def get_default_profile_image():
    return static(settings.DEFAULT_PROFILE_IMAGE)


@login_required
def profile(request, user_id):
    user = get_object_or_404(CustomUser, id=user_id)
    is_owner = user == request.user

    user_roles = ['tutor', 'supervisor', 'areacurator', 'coordinator', 'zamruk', 'master']

    user_role = request.user.role  # Предполагается, что роль пользователя хранится в поле `role`
    print(f"User Role: {user_role}")
    can_manage = user_role in user_roles and TutorStudent.objects.filter(student=user, tutor=request.user).exists()

    print(f"Is Tutor: {user_role in user_roles}")
    print(f"Tutor-Student Link Exists: {TutorStudent.objects.filter(student=user, tutor=request.user).exists()}")
    print(f"Can Manage: {can_manage}")

    show_lives = user.role == 'participator'

    if is_owner and request.method == 'POST':
        profile_form = ProfileImageForm(request.POST, request.FILES, instance=user)
        if profile_form.is_valid():
            profile_form.save()
            messages.success(request, 'Изображение профиля обновлено.')
        else:
            messages.error(request, 'Ошибка при обновлении изображения профиля.')

    else:
        profile_form = ProfileImageForm(instance=user)

    if can_manage and request.method == 'POST':
        form = ChangeLivesForm(request.POST)
        if form.is_valid():
            action = form.cleaned_data['action']
            if action == 'add':
                user.add_life()
                messages.success(request, 'Жизнь добавлена.')
            elif action == 'remove':
                if user.lives > 1:
                    user.remove_life(request.user)
                    messages.success(request, 'Жизнь убрана.')
                elif user.lives == 1:
                    if 'confirm' in request.POST:
                        user.remove_life(request.user)
                        messages.success(request, 'Все жизни удалены. Студент отчислен.')
                    elif 'cancel' in request.POST:
                        messages.info(request, 'Удаление последней жизни отменено.')
                    else:
                        messages.warning(request, 'У студента одна жизнь. Подтвердите удаление последней жизни.')
                        return render(request, 'main/profile.html',
                                      {'user': user, 'is_owner': is_owner, 'can_manage': can_manage, 'confirm': True,
                                       'form': form, 'show_lives': show_lives})
            return redirect('profile', user_id=user.id)
    else:
        form = ChangeLivesForm()

    field_data = {
        'last_name': user.last_name,
        'first_name': user.first_name,
        'fathersname': user.fathersname,
        'sex': user.sex,
        'region': user.region,
        'school': user.school,
        'university': user.university,
        'number': user.number,
        'email': user.email,
        'curdir': user.curdir
    }

    role_fields = {
        'participator': ['last_name', 'first_name', 'fathersname', 'region', 'school', 'number', 'email'],
        'tutor': ['last_name', 'first_name', 'fathersname', 'region', 'university', 'number', 'email'],
        'supervisor': ['last_name', 'first_name', 'fathersname', 'region', 'university', 'number', 'email'],
        'areacurator': ['last_name', 'first_name', 'fathersname', 'curdir', 'region', 'university', 'number', 'email'],
        'coordinator': ['last_name', 'first_name', 'fathersname', 'curdir', 'region', 'university', 'number', 'email'],
        'zamruk': ['last_name', 'first_name', 'fathersname', 'curdir', 'region', 'university', 'number', 'email'],
        'master': ['last_name', 'first_name', 'fathersname', 'curdir', 'region', 'university', 'number', 'email'],
    }

    if not is_owner:
        del field_data['email']

    fields_to_display = role_fields.get(user.role, [])
    field_data = {field: field_data[field] for field in fields_to_display if field in field_data}

    context = {
        'user': user,
        'field_data': field_data,
        'title': 'Профиль пользователя',
        'is_owner': is_owner,
        'can_manage': can_manage,
        'form': form,
        'show_lives': show_lives,
        'profile_image_url': user.profile_image.url if user.profile_image else static('images/defaultpic.png'),
        'role_choices': ROLE_CHOICES
    }

    return render(request, 'main/profile.html', context)


@login_required
@role_required(allowed_roles=['master', 'zamruk'])
def export_statistics(request):
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Статистика"

    headers = ['ФИО', 'Количество жизней', 'Учебное заведение', 'Номер телефона', 'Электронная почта', 'Роль', 'Дата вступления', 'Дисциплина']
    ws.append(headers)

    for col in ws.iter_cols(min_col=1, max_col=len(headers), min_row=1, max_row=1):
        for cell in col:
            cell.font = Font(bold=True)

    participants = CustomUser.objects.all().prefetch_related('curdir').select_related('region', 'university')
    print(f"Всего пользователей: {participants.count()}")

    for participant in participants:
        curdir = ', '.join([d.name for d in participant.curdir.all()])
        educational_institution = participant.school if participant.school else (participant.university.name if participant.university else "Не указано")
        row = [
            f"{participant.last_name} {participant.first_name} {participant.fathersname}",
            participant.lives,
            educational_institution,
            participant.number,
            participant.email,
            participant.get_role_display(),  # Используем get_role_display для получения человеческого названия роли
            participant.date_joined.strftime('%Y-%m-%d'),
            curdir
        ]
        print(row)  # Отладочная печать для проверки данных
        ws.append(row)

    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename=statistics.xlsx'
    wb.save(response)
    return response