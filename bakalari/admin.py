from django.contrib import admin

from bakalari.models import NotificationSubscription, LogSubject2, LogUser2


class NotificationSubscriptionAdmin(admin.ModelAdmin):
    list_display = ('name', 'last_check', 'contact_type', 'contact_id', 'url', 'failed_checks')
    list_filter = ('last_check', 'contact_type', 'contact_id', 'url', 'failed_checks')


class LogUser2Admin(admin.ModelAdmin):
    list_display = ('user_id', 'school', 'dashboard_count', 'subject_count', 'last_seen')
    list_filter = ('school', 'dashboard_count', 'subject_count', 'last_seen')


class LogSubject2Admin(admin.ModelAdmin):
    list_display = ('subject', 'count')
    list_filter = ('subject', 'count')

admin.site.register(NotificationSubscription, NotificationSubscriptionAdmin)
admin.site.register(LogUser2, LogUser2Admin)
admin.site.register(LogSubject2, LogSubject2Admin)
