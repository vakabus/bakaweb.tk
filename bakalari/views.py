import json
import urllib
from datetime import datetime

import requests
from django.core.urlresolvers import reverse, reverse_lazy
from django.http import HttpResponse
from django.shortcuts import render, redirect

# Create your views here.
from django.utils.text import slugify
from django.views.decorators.cache import cache_page
from django.views.decorators.vary import vary_on_cookie
from requests import RequestException

from bakalari.models import NotificationSubscription, LogSubject, LogUser
from pybakalib.client import BakaClient
from pybakalib.errors import LoginError, BakalariError

from bakalari import newsfeed
from bakalari.forms import LoginForm

import logging

logger = logging.getLogger(__name__)


def get_base_context(request):
    context = {
        'login_failed': bool(request.session.get('login_failed', False)),
        'logged_in': 'token' in request.session,
        'account': {
            'name': request.session.get('name', ''),
            'school': request.session.get('school', ''),
            'username': request.session.get('username', ''),
            'password': request.session.get('password', ''),
            'login_url': urllib.parse.urljoin(request.session.get('url', ''), 'login.aspx')
        }
    }
    if not context['logged_in']:
        context['login_form'] = LoginForm()
    return context


def login(request):
    if request.method == 'GET':
        return redirect('index')
    else:
        form = LoginForm(request.POST)
        if form.is_valid():
            form.cleaned_data['url'] = form.cleaned_data['url'].replace('bakaweb.tk', 'bakalari.ceskolipska.cz')
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
            request.session['password'] = form.cleaned_data['password']
            request.session['username'] = form.cleaned_data['username']

            # Logging
            users = LogUser.objects.filter(real_name=request.session['name'], username=request.session['username'])
            if len(users) > 0:
                users[0].login_count += 1
                users[0].save()
            else:
                LogUser(real_name=request.session['name'], url=request.session['url'],
                        username=request.session['username'], login_count=1).save()

            return redirect('dashboard')
        else:
            request.session['login_failed'] = True
            return redirect('index')


def logout(request):
    request.session.flush()
    return redirect('index')


def index(request):
    if 'token' in request.session and 'force' not in request.GET:
        return redirect('dashboard')
    context = get_base_context(request)

    request.session['login_failed'] = False
    return render(request, 'bakalari/index.html', context=context)


def dashboard(request):
    if 'token' not in request.session:
        return redirect('index')

    context = get_base_context(request)
    context.update({
        'load_url': reverse_lazy('dashboard_content'),
    })

    return render(request, 'bakalari/async_load.html', context)


@cache_page(60 * 5)
@vary_on_cookie
def dashboard_content(request):
    try:
        if 'token' not in request.session:
            return HttpResponse('You must first log in...<script>window.location.pathname = "/"<script>')

        # Logging
        users = LogUser.objects.filter(real_name=request.session['name'], username=request.session['username'])
        if len(users) > 0:
            users[0].dashboard_count += 1
            users[0].save()

        client = BakaClient(request.session['url'])

        try:
            client.login(request.session['token'])
        except LoginError as er:
            request.session.flush()
            request.session['login_failed'] = True
            return HttpResponse(
                '<script>alert("Je nejaky problem s prihlasenim."); window.location.pathname = "/"</script>')

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
    except BaseException as e:
        logger.exception("Failed to serve dashboard content.")
        return render(request, 'bakalari/error.html')


def subject(request, subject_name):
    if 'token' not in request.session:
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
def subject_content(request, subject_name):
    try:
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

        # Logging
        users = LogUser.objects.filter(real_name=request.session['name'], username=request.session['username'])
        if len(users) > 0:
            users[0].subject_count += 1
            users[0].save()
        s = LogSubject.objects.filter(subject=subject_name)
        if len(s) > 0:
            s[0].count += 1
            s[0].save()
        else:
            LogSubject(subject=subject_name, count=1).save()

        for mark in subject.marks:
            mark.weight = mark.get_weight(weights)
        subject.weighted_average = subject.get_weighted_average(weights)
        context = {
            'subject': subject,
        }
        return render(request, 'bakalari/subject_detail.html', context)
    except BaseException as e:
        logger.exception("Failed to server subject detail")
        return render(request, 'bakalari/error.html')


def notifications(request):
    if 'token' not in request.session:
        return redirect('index')

    context = get_base_context(request)
    context.update({
        'url': urllib.parse.quote(request.session['url']),
        'token': urllib.parse.quote(request.session['token']),
        'registered': {
            'pushbullet': NotificationSubscription.objects.filter(name=request.session['name'],
                                                                  contact_type='pushbullet').exists(),
            'email': NotificationSubscription.objects.filter(name=request.session['name'],
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
        return redirect('notifications')

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
            return render(request, 'bakalari/pushbullet_registration_failed.html', context=context)

        return render(request, 'bakalari/pushbullet_registration_step.html', context=context)

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
        return render(request, 'bakalari/pushbullet_registration_success.html', context=context)

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
        return redirect('notifications')

    if 'email' in data and 'token' in request.session and 'token' not in data:
        try:
            u = urllib.parse.quote
            send(
                data['email'],
                'https://www.bakaweb.tk' + str(reverse_lazy('register_email')) + '?email={}&url={}&name={}&token={}'
                .format(u(data['email']), u(request.session['url']), u(request.session['name']),
                        u(request.session['token']))
            )
            return render(request, 'bakalari/email_registration_step.html', get_base_context(request))
        except RequestException:
            return render(request, 'bakalari/email_registration_failed.html', get_base_context(request))

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
        return render(request, 'bakalari/email_registration_success.html', context=get_base_context(request))

    return redirect('notifications')


def baka_proxy(request):
    resp = requests.get('https://bakalari.ceskolipska.cz/login.aspx', params=request.GET)
    return HttpResponse(resp.text)
