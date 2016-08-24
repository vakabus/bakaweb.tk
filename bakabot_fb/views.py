import json

import requests
from django.http import HttpResponse

# Create your views here.
from django.utils.decorators import method_decorator
from django.views import generic
from django.views.decorators.csrf import csrf_exempt


def post_facebook_message(fbid, message):
    post_message_url = 'https://graph.facebook.com/v2.7/me/messages?access_token=EAAEDiKBqyVEBAGd2W3ZC0fkU7ZAdyPJ81KM9chX5rw3rB9ZCKr4a1UZAYa0Y'
    response_msg = json.dumps({"recipient": {"id": fbid}, "message": {"text": message}})
    status = requests.post(post_message_url, headers={"Content-Type": "application/json"}, data=response_msg)
    print('Send FB message status: ', status.json())


class Bot(generic.View):
    def get(self, request, *args, **kwargs):
        if self.request.GET.get('hub.verify_token', '') == 'hustejtoken':
            return HttpResponse(self.request.GET['hub.challenge'])
        else:
            return HttpResponse('Error, invalid token')

    ''' This stops Django's complains about not using CSRF '''

    @method_decorator(csrf_exempt)
    def dispatch(self, request, *args, **kwargs):
        return generic.View.dispatch(self, request, *args, **kwargs)

    # Post function to handle Facebook messages
    def post(self, request, *args, **kwargs):
        incoming_message = json.loads(self.request.body.decode('utf-8'))
        for entry in incoming_message['entry']:
            for message in entry['messaging']:
                # Check to make sure the received call is a message call
                # This might be delivery, optin, postback for other events
                if 'message' in message:
                    print('Received FB message: ', message)
                    post_facebook_message(message['sender']['id'], message['message']['text'])
        return HttpResponse()
