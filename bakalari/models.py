from django.db import models


class NotificationSubscription(models.Model):
    url = models.CharField(max_length=128)
    name = models.CharField(max_length=32)
    perm_token = models.CharField(max_length=128)
    last_check = models.DateTimeField()
    contact_type = models.CharField(max_length=16)
    contact_id = models.CharField(max_length=128)

    def __str__(self):
        return '{} (last check: {})'.format(self.name, self.last_check.strftime('%d.%m. %H:%M:%S'))


class LogUser(models.Model):
    url = models.CharField(max_length=128)
    username = models.CharField(max_length=32)
    real_name = models.CharField(max_length=64)
    login_count = models.PositiveSmallIntegerField(default=0)
    dashboard_count = models.PositiveSmallIntegerField(default=0)
    subject_count = models.PositiveSmallIntegerField(default=0)

    def __str__(self):
        return '{} ({} logins)'.format(self.real_name, str(self.login_count))


class LogSubject(models.Model):
    subject = models.CharField(max_length=64)
    count = models.PositiveSmallIntegerField(default=0)

    def __str__(self):
        return '{}: {}'.format(self.subject, str(self.count))