from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponseForbidden
from .forms import SolicitudCompraForm, ProveedorForm, SolicitudCotizacionForm
from .utils import hay_stock_suficiente 
from .models import SolicitudCompra
from django.shortcuts import get_object_or_404, redirect, render

from .forms import CotizacionForm
from .models import SolicitudCotizacion

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

    ##HU-04: Validar disponibilidad de stock (Logistica)
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

# HU-05: Actualizar estado de la solicitud de inventario
def verificar_stock_view(request, pk):
    solicitud = get_object_or_404(SolicitudCompra, pk=pk)

    if hay_stock_suficiente(solicitud.producto_codigo, solicitud.cantidad_solicitada):
        solicitud.estado = SolicitudCompra.ESTADO_HAY_STOCK
    else:
        solicitud.estado = SolicitudCompra.ESTADO_SIN_STOCK
    solicitud.save()

    return redirect("compras_listado_solicitudes")
# HU-06: Crear bandeja de solicitudes pendientes
def bandeja_pendientes_view(request):
    # ST-3.4: solo se muestran solicitudes que requieren revisión
    # (ya se verificó el stock, y todavía no hay decisión de aprobación)
    solicitudes = SolicitudCompra.objects.filter(
        estado__in=[SolicitudCompra.ESTADO_HAY_STOCK, SolicitudCompra.ESTADO_SIN_STOCK]
    ).order_by("fecha_registro")
    return render(request, "compras/bandeja_pendientes.html", {"solicitudes": solicitudes})
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
        #no se puede rechfazar sin justificación
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

    #sprint 4 
    # HU-09: Registrar proveedores
def registrar_proveedor_view(request):

    if request.method == "POST":
        form = ProveedorForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("compras_listado_proveedores")
    else:
        form = ProveedorForm()
    return render(request, "compras/registrar_proveedor.html", {"form": form})

    # HU-10: Registrar solicitud de cotización
def crear_solicitud_cotizacion_view(request, pk):
    solicitud_compra = get_object_or_404(SolicitudCompra, pk=pk)

    # Si ya existe una solicitud de cotización para esta compra, no crear otra:
    # la mostramos directamente (ahí se pueden seguir agregando cotizaciones)
    solicitud_cotizacion_existente = getattr(solicitud_compra, "solicitud_cotizacion", None)
    if solicitud_cotizacion_existente is not None:
        return redirect("compras_ver_cotizaciones", pk=solicitud_cotizacion_existente.pk)

    if request.method == "POST":
        form = SolicitudCotizacionForm(request.POST)
        if form.is_valid():
            solicitud_cotizacion = form.save(commit=False)
            solicitud_cotizacion.solicitud_compra = solicitud_compra
            solicitud_cotizacion.save()
            form.save_m2m()
            return redirect("compras_ver_cotizaciones", pk=solicitud_cotizacion.pk)
    else:
        form = SolicitudCotizacionForm()

    return render(request, "compras/crear_solicitud_cotizacion.html", {
        "form": form,
        "solicitud_compra": solicitud_compra,
    })

def ver_cotizaciones_view(request, pk):
    # HU-11 (COMINV-66): consultar las cotizaciones registradas de una solicitud
    solicitud_cotizacion = get_object_or_404(SolicitudCotizacion, pk=pk)
    cotizaciones = solicitud_cotizacion.cotizaciones.all()

    if request.method == "POST":
        # HU-12 (COMINV-67): registrar la información económica de una cotización
        cot_form = CotizacionForm(request.POST)
        if cot_form.is_valid():
            cotizacion = cot_form.save(commit=False)
            cotizacion.solicitud_cotizacion = solicitud_cotizacion
            cotizacion.save()
            return redirect("compras_ver_cotizaciones", pk=pk)
    else:
        cot_form = CotizacionForm()
        cot_form.fields["proveedor"].queryset = solicitud_cotizacion.proveedores.all()

    return render(request, "compras/ver_cotizaciones.html", {
        "solicitud_cotizacion": solicitud_cotizacion,
        "cotizaciones": cotizaciones,
        "cot_form": cot_form,
    })