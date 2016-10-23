from django.contrib import admin

from bakalari.models import NotificationSubscription, LogSubject, LogUser

admin.site.register(NotificationSubscription)
admin.site.register(LogUser)
admin.site.register(LogSubject)
# Register your models here.
