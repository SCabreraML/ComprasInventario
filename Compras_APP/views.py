from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.http import HttpResponseForbidden



def login_view(request):
    if request.user.is_authenticated:
        return redirect("dashboard")

    error = None

    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(
            request,
            username=username,
            password=password
        )

        if user is not None:
            login(request, user)
            return redirect("dashboard")
        else:
            error = "Usuario o contraseña incorrectos."

    return render(request, "login.html", {"error": error})


@login_required
def dashboard(request):

    if request.user.groups.filter(name="Administrador").exists():
        rol = "Administrador"

    elif request.user.groups.filter(name="Encargado de Compras").exists():
        rol = "Encargado de Compras"

    else:
        rol = "Sin rol"

    return render(
        request,
        "dashboard.html",
        {
            "rol": rol
        }
    )


@login_required
def logout_view(request):
    logout(request)
    return redirect("login")

@login_required
def usuarios(request):

    if not request.user.groups.filter(name="Administrador").exists():
        return HttpResponseForbidden("No tienes permisos para acceder a esta página.")

    return render(request, "usuarios.html")