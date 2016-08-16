import base64
import urllib

from django.core.urlresolvers import reverse
from django.http import HttpResponse
from django.shortcuts import render, redirect

# Create your views here.
from django.utils.text import slugify
from django.views.decorators.cache import cache_page
from django.views.decorators.vary import vary_on_cookie
from pybakalib.client import BakaClient
from pybakalib.errors import LoginError, BakalariError

from bakalari import newsfeed
from bakalari.forms import LoginForm


def login(request):
    if request.method == 'GET':
        return redirect('index')
    else:
        form = LoginForm(request.POST)
        if form.is_valid():
            client = BakaClient(form.cleaned_data['url'])
            try:
                client.login(form.cleaned_data['username'], form.cleaned_data['password'])
            except (BakalariError, LoginError) as ex:
                request.session['login_failed'] = True
                return redirect('index')

            account = client.get_module('login')
            request.session['url'] = form.cleaned_data['url']
            request.session['token'] = client.token_perm
            request.session['name'] = account.name
            request.session['school'] = account.school

            return redirect('dashboard')
        else:
            request.session['login_failed'] = True
            return redirect('index')


def logout(request):
    request.session.flush()
    return redirect('index')


def index(request):
    context = {
        'login_failed': bool(request.session.get('login_failed', 'False')),
        'logged_in': 'token' in request.session,
        'login_form': LoginForm(),
        'account': {
            'name': request.session.get('name', ''),
            'school': request.session.get('school', '')
        }
    }
    request.session['login_failed'] = False
    return render(request, 'bakalari/index.html', context=context)


def dashboard(request):
    if 'token' not in request.session:
        return redirect('index')

    context = {
        'load_url': reverse('dashboard_content'),
        'logged_in': True,
        'account': {
            'name': request.session.get('name', ''),
            'school': request.session.get('school', '')
        }
    }
    return render(request, 'bakalari/async_load.html', context)


@vary_on_cookie
@cache_page(60*5)
def dashboard_content(request):
    if 'token' not in request.session:
        return HttpResponse('You must first log in...<script>window.location.pathname = "/"<script>')

    client = BakaClient(request.session['url'])

    try:
        client.login(request.session['token'])
    except LoginError as er:
        request.session.flush()
        request.session['login_failed'] = True
        return redirect('index')

    weights = client.get_module('predvidac')
    marks = client.get_module('znamky')
    subjects = marks.get_all_averages(weights)

    feed = newsfeed.Feed(client)

    context = {
        'url': urllib.parse.quote(request.session['url']),
        'token': urllib.parse.quote(request.session['token']),
        'feed': feed[:10],
        'subjects': subjects,
    }
    return render(request, 'bakalari/dashboard_content.html', context)


def subject(request, subject_name):
    if 'token' not in request.session:
        return redirect('index')

    context = {
        'load_url': reverse('subject_content', args=[subject_name]),
        'logged_in': True,
        'account': {
            'name': request.session.get('name', ''),
            'school': request.session.get('school', '')
        }
    }
    return render(request, 'bakalari/async_load.html', context)


@vary_on_cookie
@cache_page(60*2)
def subject_content(request, subject_name):
    if 'token' not in request.session:
        return HttpResponse('You must first log in...<script>window.location.pathname = "/"<script>')

    client = BakaClient(request.session['url'])
    client.login(request.session['token'])

    marks = client.get_module('znamky')
    weights = client.get_module('predvidac')

    subject = None
    for s in marks:
        if slugify(s.name) == subject_name:
            subject = s
    if subject is None:
        return HttpResponse('Subject does not exist...<script>window.location.pathname = "/"<script>')

    for mark in subject.marks:
        mark.weight = mark.get_weight(weights)
    subject.weighted_average = subject.get_weighted_average(weights)
    context = {
        'subject': subject,
    }
    return render(request, 'bakalari/subject_detail.html', context)


def notifications(request):
    if 'token' not in request.session:
        return redirect('index')

    context = {
        'url': urllib.parse.quote(request.session['url']),
        'token': urllib.parse.quote(request.session['token']),
        'logged_in': True,
        'account': {
            'name': request.session.get('name', ''),
            'school': request.session.get('school', '')
        }
    }
    return render(request, 'bakalari/bakanotifikace.html', context)
