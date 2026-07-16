from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponseForbidden
from .forms import SolicitudCompraForm
from .models import SolicitudCompra

def registrar_auditoria(user, accion, detalle):
    print(f"[AUDITORIA] Usuario: {user} - Acción: {accion} - Detalle: {detalle}")



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

# Dev 2 - ST-2.4
# Registrar solicitud


@login_required
def crear_solicitud(request):

    if request.method == "POST":

        form = SolicitudCompraForm(request.POST)

        if form.is_valid():

            solicitud = form.save(commit=False)

            solicitud.solicitante = request.user

            solicitud.save()

            return redirect("lista_solicitudes")

    else:

        form = SolicitudCompraForm()

    return render(
        request,
        "solicitudes/formulario.html",
        {
            "form": form
        }
    )

# Dev 3 - ST-2.5
# Consultar solicitudes


@login_required
def lista_solicitudes(request):
    solicitudes = SolicitudCompra.objects.order_by("-fecha_registro")

    from .utils import consultar_existencias_api
    for sol in solicitudes:
        info_stock = consultar_existencias_api(sol.producto)
        if info_stock:
            sol.stock_logistica = info_stock.get("stock_total", 0)
            sol.stock_bodega = info_stock.get("stock_bodega", 0)
            sol.stock_percha = info_stock.get("stock_percha", 0)
            sol.disponibilidad = "Suficiente" if sol.stock_logistica >= sol.cantidad else "Insuficiente"
            sol.producto_existe = True
        else:
            sol.stock_logistica = 0
            sol.disponibilidad = "No encontrado en Logística"
            sol.producto_existe = False

    es_gestor = request.user.groups.filter(name__in=["Administrador", "Encargado de Compras"]).exists() or request.user.is_superuser

    return render(
        request,
        "solicitudes/lista.html",
        {
            "solicitudes": solicitudes,
            "es_gestor": es_gestor
        }
    )



# Dev 3 - ST-2.6
# Editar solicitudes pendientes


@login_required
def editar_solicitud(request, pk):

    solicitud = SolicitudCompra.objects.get(pk=pk)

    if solicitud.estado != "PENDIENTE":
        return redirect("lista_solicitudes")

    if request.method == "POST":

        form = SolicitudCompraForm(
            request.POST,
            instance=solicitud
        )

        if form.is_valid():
            form.save()
            return redirect("lista_solicitudes")

    else:

        form = SolicitudCompraForm(
            instance=solicitud
        )

    return render(
        request,
        "solicitudes/formulario.html",
        {
            "form": form
        }
    )

#Sprint 3 
# HU-07: Implementar aprobación de solicitudes
@login_required
def aprobar_solicitud_view(request, pk):
    solicitud = get_object_or_404(SolicitudCompra, pk=pk)
    solicitud.estado = SolicitudCompra.ESTADO_APROBADA
    solicitud.save()
    registrar_auditoria(request.user if request.user.is_authenticated else None,
                         "Aprobar solicitud", f"{solicitud.codigo}")
    return redirect("lista_solicitudes")

#HU-08 Implementar rechazo con justificación
@login_required
def rechazar_solicitud_view(request, pk):
    solicitud = get_object_or_404(SolicitudCompra, pk=pk)

    if request.method == "POST":
        justificacion = request.POST.get("justificacion", "").strip()
        #no se puede rechazar sin justificación
        if not justificacion:
            return render(request, "solicitudes/rechazar_solicitud.html", {
                "solicitud": solicitud,
                "error": "Debes ingresar una justificación para rechazar.",
            })
        solicitud.estado = SolicitudCompra.ESTADO_RECHAZADA
        solicitud.justificacion = justificacion
        solicitud.save()
        registrar_auditoria(request.user if request.user.is_authenticated else None,
                             "Rechazar solicitud", f"{solicitud.codigo} - {justificacion}")
        return redirect("lista_solicitudes")

    return render(request, "solicitudes/rechazar_solicitud.html", {"solicitud": solicitud})
