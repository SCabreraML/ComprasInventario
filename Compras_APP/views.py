from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponseForbidden
from .models import SolicitudCompra
from .forms import SolicitudCompraForm


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

@login_required
def lista_solicitudes(request):
    solicitudes = SolicitudCompra.objects.all().order_by('-fecha_registro')
    return render(request, "solicitudes/lista.html", {"solicitudes": solicitudes})

@login_required
def crear_solicitud(request):
    if request.method == "POST":
        form = SolicitudCompraForm(request.POST)
        if form.is_valid():
            solicitud = form.save(commit=False)
            solicitud.usuario = request.user
            solicitud.save()
            return redirect("lista_solicitudes")
    else:
        form = SolicitudCompraForm()
    return render(request, "solicitudes/formulario.html", {"form": form, "titulo": "Nueva Solicitud"})

@login_required
def editar_solicitud(request, pk):
    solicitud = get_object_or_404(SolicitudCompra, pk=pk)

    # Solo permitir edición si está en estado Pendiente
    if solicitud.estado != 'Pendiente':
        return HttpResponseForbidden("No se puede editar una solicitud que ya ha sido procesada.")

    if request.method == "POST":
        form = SolicitudCompraForm(request.POST, instance=solicitud)
        if form.is_valid():
            form.save()
            return redirect("lista_solicitudes")
    else:
        form = SolicitudCompraForm(instance=solicitud)
    return render(request, "solicitudes/formulario.html", {"form": form, "titulo": "Editar Solicitud"})