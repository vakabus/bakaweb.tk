from django.db import models


class NotificationSubscription(models.Model):
    url = models.CharField(max_length=128)
    name = models.CharField(max_length=32)
    perm_token = models.CharField(max_length=128)
    last_check = models.DateTimeField()
    contact_type = models.CharField(max_length=16)
    contact_id = models.CharField(max_length=128)

    def __str__(self):
        return '{}: {} ({})'.format(self.url, self.name, str(self.last_check))
