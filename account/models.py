from django.db import models


class LoginForm(models.Model):
    username = models.CharField(max_length=200)
    password = models.CharField(max_length=150)

    def __str__(self):
        return self.usenrame

