from django.contrib.auth.models import AbstractUser
from django.db import models
from datetime import datetime, timedelta
from django.utils import timezone

class User(AbstractUser):
    def __str__(self):
        return f"{self.username}"


class Auction(models.Model):
    title = models.CharField(max_length=64)

    description = models.TextField(max_length=800)

    start_bid = models.DecimalField(max_digits=6, decimal_places=2)

    category = models.CharField(blank=True,null=True,max_length=32)

    image = models.ImageField(blank=True,
                              null=True,
                              upload_to='')

    DURATIONS = (
        (3, "Three Days"),
        (7, "One Week"),
        (14, "Two Weeks"),
        (28, "Four Weeks")
    )

    duration = models.IntegerField(choices=DURATIONS)
    ended_manually = models.BooleanField(default=False)

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="auctions"
    )

    start_time = models.DateTimeField()
    end_time = models.DateTimeField()

    watchers = models.ManyToManyField(User,blank=True,related_name="watchlist")

    class Meta:
        ordering = ('-end_time',)

    def __str__(self):
        return f"Auction #{self.id}: {self.title} ({self.user.username})"

    def save(self, *args, **kwargs):
        self.start_time = datetime.now()
        self.end_time = self.start_time + timedelta(days=self.duration)
        super().save(*args, **kwargs)  # call existing save() method

    def is_finshed(self):
        if self.ended_manually or self.end_time < timezone.now():
            return True
        else:
            return False

class Bid(models.Model):
    bid = models.DecimalField(max_digits=6, decimal_places=2)
    user = models.ForeignKey(User,on_delete=models.CASCADE,related_name="bids")
    auction = models.ForeignKey(Auction,on_delete=models.CASCADE,related_name="bids")

    class Meta:
        ordering = ('-bid',)

    def __str__(self):
        return f"Bid #{self.id}: {self.bid} on {self.auction.title} by {self.user.username}"

class Comment(models.Model):
    comment = models.TextField(max_length=250)
    time = models.DateTimeField(auto_now_add=True)
    user    = models.ForeignKey(User, on_delete=models.CASCADE, related_name="comments")
    auction = models.ForeignKey(Auction, on_delete=models.CASCADE, related_name="comments")

    class Meta:
        ordering = ('-time',)

    def __str__(self):
        return f"Comment #{self.id}: {self.user.username} on {self.auction.title} : {self.comment}"