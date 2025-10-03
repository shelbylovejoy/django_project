from django.db import models
from django.contrib.auth.models import User

class Petition(models.Model):
    id = models.AutoField(primary_key=True)
    movie_name = models.CharField(max_length=255)
    reason = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)
    voters = models.ManyToManyField(User, related_name='petition_votes', blank=True)

    def votes_count(self):
        return self.voters.count()

    def __str__(self):
        return f"Petition: {self.movie_name} ({self.votes_count()} votes)"
