from django.db import models


class User(models.Model):
    id = models.AutoField(primary_key=True)
    full_name = models.CharField(max_length=100)

    def __str__(self):
        return self.full_name
