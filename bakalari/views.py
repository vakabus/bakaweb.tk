import json
import logging
import urllib
from datetime import datetime
from functools import wraps

import requests
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.utils.text import slugify
from django.views.decorators.cache import cache_page
from django.views.decorators.vary import vary_on_cookie
from requests import RequestException

from bakalari import newsfeed
from bakalari.forms import LoginForm
from bakalari.models import NotificationSubscription, Session, LogUser2, LogSubject2

logger = logging.getLogger(__name__)


def get_base_context(request):
    user = request.session['user']
    context = {
        'login_failed': bool(request.session.get('login_failed', False)),
        'logged_in': False if user is None else user.is_logged_in(),
        'account': {
            'name': '' if user is None else user.real_name,
            'school': '' if user is None else user.school_name,
            'username': '' if user is None else user.username,
            'password': '' if user is None else user.password,
            'login_url': urllib.parse.urljoin('' if user is None else user.url, 'login.aspx')
        }
    }
    if not user.is_logged_in():
        context['login_form'] = LoginForm()
    return context


def log(request_handler):

    @wraps(request_handler)
    def wrapper(request, *args, **kwargs):
        if request is not None and request.session is not None and 'user' in request.session:
            user = request.session['user']
            if not user.is_logged_in():
                return request_handler(request, *args, **kwargs)

            userid = LogUser2.get_user_id(user.username, user.password)
            logusers = LogUser2.objects.filter(user_id=userid)
            if len(logusers) > 0:
                loguser = logusers[0]
            else:
                loguser = LogUser2(user_id=userid)

            if request.path == '/dashboard/content':
                loguser.dashboard_count += 1
            if '/subject/content/' in request.path:
                loguser.subject_count += 1
                subject = LogSubject2.objects.filter(subject=kwargs['subject_name'])
                if len(subject) > 0:
                    subject[0].count += 1
                    subject[0].save()
                else:
                    LogSubject2(subject=kwargs['subject_name'], count=1).save()

            loguser.school = user.school_name
            loguser.last_seen = datetime.now()
            loguser.save()

        return request_handler(request, *args, **kwargs)

    return wrapper


def login_handle(request, url, username=None, password=None, perm_token: str = None):
    user = Session(url=url, username=username, password=password, perm_token=perm_token)
    user.login()
    if not user.is_logged_in():
        request.session['login_failed'] = True
        return redirect('index')
    else:
        request.session['user'] = user
        return redirect('dashboard')


def login(request):
    if 'user' in request.session and request.session['user'].is_logged_in():
        return redirect('dashboard')

    if request.method == 'GET':
        if 'd' in request.GET:
            user = Session.login_by_link(request.GET['d'])
            request.session['user'] = user
        return redirect('dashboard')
    else:
        form = LoginForm(request.POST)
        if form.is_valid():
            user = Session(username=form.cleaned_data['username'],
                           password=form.cleaned_data['password'],
                           url=form.cleaned_data['url'])
            user.login()
            request.session['user'] = user
            return redirect('dashboard')
        else:
            request.session['login_failed'] = True
            return redirect('index')


def logout(request):
    request.session.flush()
    return redirect('index')


def index(request):
    if 'user' not in request.session:
        request.session['user'] = Session()

    if request.session['user'].is_logged_in() and 'force' not in request.GET:
        return redirect('dashboard')

    context = get_base_context(request)
    request.session['login_failed'] = False
    return render(request, 'bakalari/index.html', context=context)


def dashboard(request):
    if 'user' not in request.session or not request.session['user'].is_logged_in():
        return redirect('index')

    context = get_base_context(request)
    context.update({
        'load_url': reverse_lazy('dashboard_content'),
    })

    return render(request, 'bakalari/async_load.html', context)


@cache_page(60 * 5)
@vary_on_cookie
@log
def dashboard_content(request):
    try:
        if 'user' not in request.session or not request.session['user'].is_logged_in():
            return HttpResponse('You must first log in...<script>window.location.pathname = "/"<script>')

        subjects = request.session['user'].get_subject_averages()
        feed = newsfeed.Feed(request.session['user'].get_baka_client())

        context = {
            'url': request.session['user'].url,
            'token': request.session['user'].token,
            'feed': feed[:10],
            'subjects': subjects,
        }
        return render(request, 'bakalari/dashboard_content.html', context)
    except Exception as e:
        logger.exception("Failed to serve dashboard content.")
        return render(request, 'bakalari/error.html')


def subject(request, subject_name):
    if 'user' not in request.session:
        return redirect('index')

    context = get_base_context(request)
    context.update({
        'load_url': reverse_lazy('subject_content', args=[subject_name])
    })

    return render(request, 'bakalari/async_load.html', context)


@cache_page(60 * 60 * 3)
def privacy_policy(request):
    return render(request, 'bakalari/privacy.html', get_base_context(request))


@cache_page(60 * 2)
@vary_on_cookie
@log
def subject_content(request, subject_name):
    try:
        if 'user' not in request.session:
            return HttpResponse('You must first log in...<script>window.location.pathname = "/"<script>')

        user = request.session['user']
        client = user.get_baka_client()

        if client is None:
            return HttpResponse('You must first log in...<script>window.location.pathname = "/"<script>')

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
    except Exception as e:
        logger.exception("Failed to server subject detail")
        return render(request, 'bakalari/error.html')


# ----------------------------------------------------------------------------------------------------------


def notifications(request):
    if 'user' not in request.session:
        return redirect('index')

    user = request.session['user']
    context = get_base_context(request)
    context.update({
        'url': urllib.parse.quote(user.url),
        'token': urllib.parse.quote(user.token),
        'registered': {
            'pushbullet': NotificationSubscription.objects.filter(name=user.real_name,
                                                                  contact_type='pushbullet').exists(),
            'email': NotificationSubscription.objects.filter(name=user.real_name,
                                                             contact_type='email').exists(),
        }
    })
    return render(request, 'bakalari/bakanotifikace.html', context)


def notifications_register_pushbullet(request):
    context = get_base_context(request)

    # Handle unsubscribe attempts
    if 'unsubscribe' in request.POST:
        NotificationSubscription \
            .objects \
            .filter(name=request.session['name'], contact_type='pushbullet') \
            .delete()
        return render(request, 'bakalari/notifications/notifications_unsubscribed.html', context)

    # Handle step 1
    if 'token' in request.session and 'apiKey' not in request.GET:

        # Send test notification
        url = ''.join([
            'https://www.bakaweb.tk',
            str(reverse_lazy('register_pushbullet')),
            '?url=',
            urllib.parse.quote(request.session['url'], safe=''),
            '&token=',
            urllib.parse.quote(request.session['token'], safe=''),
            '&name=',
            urllib.parse.quote(request.session['name'], safe=''),
            '&apiKey=',
            urllib.parse.quote(request.POST['apiKey'])
        ])
        body = {
            'type': 'link',
            'title': 'Dokonči registraci',
            'body': 'Klikni na notifikaci a dokonči registraci',
            'url': url
        }
        headers = {
            'Access-Token': request.POST['apiKey'],
            'Content-Type': 'application/json'
        }

        try:
            resp = requests.post('https://api.pushbullet.com/v2/pushes', headers=headers, data=json.dumps(body))
            resp.raise_for_status()
        except RequestException:
            return render(request, 'bakalari/notifications/pushbullet_registration_failed.html', context=context)

        return render(request, 'bakalari/notifications/pushbullet_registration_step.html', context=context)

    # Handle final step
    if 'url' in request.GET and 'name' in request.GET and 'apiKey' in request.GET and 'token' in request.GET:
        if not NotificationSubscription.objects.filter(name=request.GET['name'], contact_type='pushbullet').exists():
            ns = NotificationSubscription(
                url=request.GET['url'],
                name=request.GET['name'],
                perm_token=request.GET['token'],
                last_check=datetime.now(),
                contact_type='pushbullet',
                contact_id=request.GET['apiKey']
            )
            ns.save()
        return render(request, 'bakalari/notifications/pushbullet_registration_success.html', context=context)

    return redirect('notifications')


def notifications_register_email(request):
    def send(email, link):
        url = 'https://api.mailgun.net/v3/mg.bakaweb.tk/messages'
        data = {
            'from': 'Bakaweb.tk <noreply@bakaweb.tk>',
            'to': email,
            'subject': '[BAKAWEB.TK] Registrace',
            'text': 'Registrace na emailové notifikace\n=================================\n\nPro dokončení registrace prosím klidněte zde:\n{}'.format(
                link),
            'html': '<h1>Registrace na emailové notifikace</h1><p>Pro dokončení registrace prosím klikněte na odkaz níže:</p><p><a href="{}">{}</a></p>'.format(
                link, link)
        }
        resp = requests.post(url, data=data, auth=('api', 'key-a45d0a0f76d9e3dce37949cc0953e81b'))
        resp.raise_for_status()

    data = None
    if request.method == 'POST':
        data = request.POST
    elif request.method == 'GET':
        data = request.GET
    else:
        return render(request, 'bakalari/error.html', status=404)

    if 'unsubscribe' in data:
        if 'token' in request.session:
            NotificationSubscription \
                .objects \
                .filter(name=request.session['name'], contact_type='email') \
                .delete()
        else:
            NotificationSubscription \
                .objects \
                .filter(contact_id=data['email'], contact_type='email') \
                .delete()
        return render(request, 'bakalari/notifications/notifications_unsubscribed.html', get_base_context(request))

    if 'email' in data and 'token' in request.session and 'token' not in data:
        try:
            u = urllib.parse.quote
            send(
                data['email'],
                'https://www.bakaweb.tk' + str(reverse_lazy('register_email')) + '?email={}&url={}&name={}&token={}'
                .format(u(data['email']), u(request.session['url']), u(request.session['name']),
                        u(request.session['token']))
            )
            return render(request, 'bakalari/notifications/email_registration_step.html', get_base_context(request))
        except RequestException:
            return render(request, 'bakalari/notifications/email_registration_failed.html', get_base_context(request))

    if sum([1 for x in ['token', 'url', 'name', 'email'] if x in data]) == 4:
        if not NotificationSubscription.objects.filter(name=request.GET['name'], contact_type='email').exists():
            ns = NotificationSubscription(
                url=request.GET['url'],
                name=request.GET['name'],
                perm_token=request.GET['token'],
                last_check=datetime.now(),
                contact_type='email',
                contact_id=request.GET['email']
            )
            ns.save()
        return render(request, 'bakalari/notifications/email_registration_success.html',
                      context=get_base_context(request))

    return redirect('notifications')


def baka_proxy(request):
    resp = requests.get('https://bakalari.ceskolipska.cz/login.aspx', params=request.GET)
    return HttpResponse(resp.text)
