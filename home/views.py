from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Petition

def index(request):
    template_data = {}
    template_data['title'] = 'Movies Store'
    return render(request, 'home/index.html', {'template_data': template_data})

def about(request):
    template_data = {}
    template_data['title'] = 'About'
    return render(request, 'home/about.html', {'template_data': template_data})

def petition(request):
    # create a new petition (any user can submit)
    if request.method == 'POST' and request.POST.get('movie_name'):
        movie_name = request.POST.get('movie_name')
        reason = request.POST.get('reason', '')
        p = Petition.objects.create(movie_name=movie_name, reason=reason, created_by=request.user if request.user.is_authenticated else None)
        return redirect('home.petition')

    # handle voting/unvoting via POST action
    if request.method == 'POST' and request.POST.get('action') == 'vote':
        # must be logged in to vote
        if not request.user.is_authenticated:
            return redirect('accounts.login')
        petition_id = request.POST.get('petition_id')
        petition_obj = get_object_or_404(Petition, id=petition_id)
        # toggle vote
        if request.user in petition_obj.voters.all():
            petition_obj.voters.remove(request.user)
        else:
            petition_obj.voters.add(request.user)
        return redirect('home.petition')

    petitions = Petition.objects.all().order_by('-created_at')
    template_data = {'title': 'Movie Petition', 'petitions': petitions}
    return render(request, 'home/petition.html', {'template_data': template_data})