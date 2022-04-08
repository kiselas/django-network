from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.contrib import messages, auth


def home_view(request):
    user = request.user
    hello = 'Hello world'

    context = {
        'user': user,
        'hello': hello
    }
    return render(request, 'main/home.html', context)


def login(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']

        user = auth.authenticate(username=username, password=password)
        if user:
            auth.login(request, user)
            # messages.success(request, 'You are now logged in')
            return redirect('home_view')
        else:
            messages.error(request, 'Invalid username or password')
            return redirect('login')
    else:
        return render(request, 'main/login.html')


def logout(request):
    if request.method == 'POST':
        auth.logout(request)
        # messages.success(request, 'You are now logout')
    return redirect('home_view')
