import logging

from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.shortcuts import redirect, render
from django.views import View

logger = logging.getLogger(__name__)


class LoginView(View):
    template_name = "documents/login.html"

    def get(self, request):
        if request.user.is_authenticated:
            return redirect("chat-ui")
        form = AuthenticationForm()
        return render(request, self.template_name, {"form": form})

    def post(self, request):
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            next_url = request.GET.get("next", "chat-ui")
            return redirect(next_url)
        return render(request, self.template_name, {"form": form, "error": True})


class LogoutView(View):
    def get(self, request):
        logout(request)
        return redirect("login")
