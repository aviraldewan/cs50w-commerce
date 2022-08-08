from django.contrib.auth import authenticate, login, logout
from django.db import IntegrityError
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse
from datetime import datetime, timedelta
from django.utils import timezone
from .models import User
from django.forms import ModelForm
from .models import Auction, Bid, Comment
from datetime import datetime, timedelta

class AuctionForm(ModelForm):
    class Meta:
        model = Auction
        fields = ['title',
                   'description',
                    'start_bid',
                      'image',
                       'duration',
                        'category']

    def __init__(self, *args, **kwargs):
        super(AuctionForm, self).__init__(*args, **kwargs)
        for visible in self.visible_fields():
            visible.field.widget.attrs['class'] = 'form-control'

class BidForm(ModelForm):
    class Meta:
        model = Bid
        fields = ['bid']

    def __init__(self, *args, **kwargs):
        super(BidForm, self).__init__(*args, **kwargs)
        for visible in self.visible_fields():
            visible.field.widget.attrs['class'] = 'form-control m-2'

class CommentForm(ModelForm):
    class Meta:
        model = Comment
        fields = ['comment']

    def __init__(self, *args, **kwargs):
        super(CommentForm, self).__init__(*args, **kwargs)
        self.visible_fields()[0].field.widget.attrs['class'] = 'form-control w-75 h-75'



def index(request):

    active_listings = Auction.objects.filter(
        ended_manually = False,
        end_time__gte = datetime.now()
    )
    return render(request, "auctions/index.html",{
        "listings": active_listings
    })


def login_view(request):
    if request.method == "POST":

        # Attempt to sign user in
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)

        # Check if authentication successful
        if user is not None:
            login(request, user)
            return HttpResponseRedirect(reverse("index"))
        else:
            return render(request, "auctions/login.html", {
                "message": "Invalid username and/or password."
            })
    else:
        return render(request, "auctions/login.html")


def logout_view(request):
    logout(request)
    return HttpResponseRedirect(reverse("index"))


def register(request):
    if request.method == "POST":
        username = request.POST["username"]
        email = request.POST["email"]

        # Ensure password matches confirmation
        password = request.POST["password"]
        confirmation = request.POST["confirmation"]
        if password != confirmation:
            return render(request, "auctions/register.html", {
                "message": "Passwords must match."
            })

        # Attempt to create new user
        try:
            user = User.objects.create_user(username, email, password)
            user.save()
        except IntegrityError:
            return render(request, "auctions/register.html", {
                "message": "Username already taken."
            })
        login(request, user)
        return HttpResponseRedirect(reverse("index"))
    else:
        return render(request, "auctions/register.html")


def create_listing(request):

    if request.user.is_authenticated:
        f = AuctionForm(request.POST or None, request.FILES or None)
        if f.is_valid():
            new_list = f.save(commit=False)
            new_list.user = request.user
            new_list.save()
            return render(request, "auctions/index.html")

        return render(request, "auctions/createlisting.html", {
            "form": f
        })
    else:
        return render(request, "auctions/error.html",{
            "message": "You need to be logged in to create a new listing"
        })

def listing(request,title):

    all_items = Auction.objects.all()
    for item in all_items:
        if item.title == title:

            highest_bid = 0
            for n in Bid.objects.filter(auction=item):
                highest_bid = max(highest_bid,n.bid)
            if highest_bid == 0:
                highest_bid = item.start_bid

            if item.ended_manually or item.end_time < timezone.now():
                auction = Auction.objects.get(title=title)
                if auction.ended_manually or auction.end_time < timezone.now():
                    max_bid = 0
                    for new_bid in Bid.objects.all():
                        if new_bid.bid > max_bid:
                            max_bid = new_bid.bid
                    highest_bidder = Bid.objects.get(bid=max_bid)
                    if request.user == highest_bidder.user:

                        return render(request,"auctions/listing.html",{
                            "info": item,
                            "ended": True,
                            "win": True,
                            "winner": "Congratulations! You have WON the auction! ",
                            "owner": False,
                            "comments": Comment.objects.filter(auction=item),
                            "highest_bid": highest_bid,
                            "owner": request.user == item.user
                        })
                    else:
                        return render(request, "auctions/listing.html", {
                            "info": item,
                            "ended": True,
                            "win": False,
                            "owner": False,
                            "comments": Comment.objects.filter(auction=item),
                            "highest_bid": highest_bid,
                            "owner": request.user == item.user
                        })
            time_remaining = item.end_time - timezone.now()
            days = time_remaining.days
            hours = int(time_remaining.seconds/3600)
            minutes = int(time_remaining.seconds/60 - (hours*60))
            bidform = BidForm()
            commentform = CommentForm()

            return render(request,"auctions/listing.html",{
                "days": days,
                "hours": hours,
                "minutes": minutes,
                "bidform": bidform,
                "commentform": commentform,
                "ended": False,
                "info": item,
                "comments": Comment.objects.filter(auction=item),
                "highest_bid": highest_bid,
                "owner": request.user == item.user
            })

    return render(request,"auctions/error.html",{
        "message": "Item not found!"
    })

def watch_auction(request, title):

    if request.method == "POST":
        auctions = Auction.objects.all()
        for item in auctions:
            if item.title == title:
                watchlist = request.user.watchlist
                if item in watchlist.all():
                    watchlist.remove(item)
                else:
                    watchlist.add(item)

    url = reverse("listing", kwargs={"title":title})
    return HttpResponseRedirect(url)


def watchlist(request):

    if request.user.is_authenticated:
        return render(request, "auctions/watchlist.html", {
            "listings": request.user.watchlist.all()
        })


def place_bid(request,title):
    bidform = BidForm(request.POST or none)

    if bidform.is_valid():
        all_items = Auction.objects.all()
        for auction in all_items:
            if auction.title == title:
                user = request.user
                if user == auction.user:
                    return render(request,"auctions/error.html",{
                        "message": "You cannot place a bid in your own auction"
                    })
                new_bid = bidform.save(commit=False)
                current_bids = Bid.objects.filter(auction=auction)
                is_highest_bid = all(new_bid.bid > n.bid for n in current_bids)
                is_valid_first_bid = new_bid.bid >= auction.start_bid

                highest_bid = 0
                for n in Bid.objects.filter(auction=auction):
                    highest_bid = max(highest_bid, n.bid)

                if is_highest_bid == True and is_valid_first_bid == True:
                    # print("in if")
                    new_bid.auction = auction
                    new_bid.user = request.user
                    new_bid.save()
                    url = reverse("listing", kwargs={"title": title})
                    return HttpResponseRedirect(url)
                else:
                    if highest_bid == 0:
                        highest_bid = auction.start_bid
                    return render(request, "auctions/error.html", {
                        "message": "Current highest bid is $"+str(highest_bid)+". Raise your bid value."
                    })


def comment(request,title):

    commentform = CommentForm(request.POST or none)

    if commentform.is_valid():
        new_comment = commentform.save(commit=False)
        new_comment.auction = Auction.objects.get(title=title)
        new_comment.user = request.user
        new_comment.time = datetime.now()
        new_comment.save()

        url = reverse("listing", kwargs={"title": title})
        return HttpResponseRedirect(url)

def end_auction(request,title):

    auction = Auction.objects.get(title=title)
    if request.user == auction.user:
        auction.ended_manually = True
        auction.save()

    return render(request, "auctions/error.html", {
        "message": "Auction ended Successfully!"
    })

def archives(request):
    item = Auction.objects.filter(
        ended_manually=True)
    return render(request,"auctions/archives.html",{
        "listings": item
    })

def category(request,name):
    cate = Auction.objects.filter(category=name,ended_manually=False,end_time__gte = datetime.now())
    return render(request,"auctions/index.html",{
        "listings": cate
    })

def categories(request):

    return render(request,"auctions/categories.html",{
        "categories": list(set(Auction.objects.all()))
    })