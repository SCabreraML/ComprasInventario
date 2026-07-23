from django.shortcuts import get_object_or_404, render
from django.views.decorators.http import require_http_methods

from .forms import (
    DevolucionForm,
    InspeccionPerchaForm,
    MovimientoForm,
    ProductoSearchForm,
    RecepcionForm,
    ReponerPerchaForm,
)
from .models import Lote, MovimientoInventario, Producto
from .services import InventoryService


def dashboard_view(request):
    search_form = ProductoSearchForm(request.GET)
    productos = Producto.objects.filter(activo=True).order_by("codigo")
    if search_form.is_valid():
        q = search_form.cleaned_data.get("q")
        categoria = search_form.cleaned_data.get("categoria")
        if q:
            productos = productos.filter(nombre__icontains=q) | productos.filter(codigo__icontains=q)
        if categoria:
            productos = productos.filter(categoria__icontains=categoria)

    return render(request, "inventory/dashboard.html", {"productos": productos, "search_form": search_form})


def registro_recepcion_view(request):
    form = RecepcionForm(request.POST or None)
    message = None
    if request.method == "POST" and form.is_valid():
        order_compra = form.cleaned_data["order_compra"]
        producto = form.cleaned_data["producto"]
        cantidad = form.cleaned_data["cantidad"]
        lote_numero = form.cleaned_data["lote_numero"]
        ubicacion = form.cleaned_data["ubicacion"]
        conformidad = form.cleaned_data["conformidad"]
        if not conformidad:
            message = "La recepción solo puede registrarse si los productos están conformes."
        else:
            InventoryService.registrar_recepcion(order_compra, producto, cantidad, request.user, lote_numero=lote_numero, ubicacion=ubicacion)
            message = "Recepción registrada correctamente."
            form = RecepcionForm()
    return render(request, "inventory/recepcion.html", {"form": form, "message": message})


def registro_movimiento_view(request):
    form = MovimientoForm(request.POST or None)
    message = None
    if request.method == "POST" and form.is_valid():
        producto = form.cleaned_data["producto"]
        cantidad = form.cleaned_data["cantidad"]
        tipo = form.cleaned_data["tipo"]
        motivo = form.cleaned_data["motivo"]
        referencia = form.cleaned_data["referencia"]
        lote = form.cleaned_data["lote"]
        try:
            InventoryService.registrar_movimiento(producto, cantidad, tipo, request.user, motivo=motivo, lote=lote, referencia=referencia)
            message = "Movimiento registrado correctamente."
            form = MovimientoForm()
        except Exception as exc:
            message = str(exc)
    return render(request, "inventory/movimiento.html", {"form": form, "message": message})


def historial_movimientos_view(request, producto_id):
    producto = get_object_or_404(Producto, id=producto_id)
    movimientos = MovimientoInventario.objects.filter(producto=producto).order_by("-created_at")
    return render(request, "inventory/historial.html", {"producto": producto, "movimientos": movimientos})


def registro_devolucion_view(request):
    form = DevolucionForm(request.POST or None)
    message = None
    if request.method == "POST" and form.is_valid():
        producto = form.cleaned_data["producto"]
        cantidad = form.cleaned_data["cantidad"]
        motivo = form.cleaned_data["motivo"]
        evidencia = form.cleaned_data["evidencia"]
        lote = form.cleaned_data["lote"]
        try:
            InventoryService.registrar_devolucion(producto, cantidad, motivo, request.user, evidencia=evidencia, lote=lote)
            message = "Devolución procesada correctamente."
            form = DevolucionForm()
        except Exception as exc:
            message = str(exc)
    return render(request, "inventory/devolucion.html", {"form": form, "message": message})


def inspeccion_percha_view(request):
    form = InspeccionPerchaForm(request.POST or None)
    message = None
    if request.method == "POST" and form.is_valid():
        producto = form.cleaned_data["producto"]
        observaciones = form.cleaned_data["observaciones"]
        sin_novedades = form.cleaned_data["sin_novedades"]
        InventoryService.registrar_inspeccion(producto, request.user, observaciones=observaciones, sin_novedades=sin_novedades)
        message = "Inspección registrada correctamente."
        form = InspeccionPerchaForm()
    return render(request, "inventory/inspeccion.html", {"form": form, "message": message})


def reporte_existencias_view(request):
    productos = InventoryService.generar_reporte_existencias()
    return render(request, "inventory/reporte.html", {"productos": productos})


def reponer_percha_view(request):
    form = ReponerPerchaForm(request.POST or None)
    message = None
    if request.method == "POST" and form.is_valid():
        producto = form.cleaned_data["producto"]
        cantidad = form.cleaned_data["cantidad"]
        try:
            InventoryService.aplicar_fifo(producto, cantidad, request.user)
            message = "Reposición FIFO realizada correctamente."
            form = ReponerPerchaForm()
        except Exception as exc:
            message = str(exc)
    lotes = Lote.objects.filter(producto__activo=True, estado="DISPONIBLE").order_by("fecha_vencimiento")
    return render(request, "inventory/reponer_percha.html", {"form": form, "message": message, "lotes": lotes})


def proximos_vencer_view(request):
    lotes = InventoryService.monitorear_proximos_a_vencer(dias=30)
    return render(request, "inventory/proximos_vencer.html", {"lotes": lotes})


def retirar_vencidos_view(request):
    if request.method == "POST":
        producto_id = request.POST.get("producto_id")
        cantidad = int(request.POST.get("cantidad", 0))
        motivo = request.POST.get("motivo", "")
        evidencia = request.POST.get("evidencia", "")
        producto = get_object_or_404(Producto, id=producto_id)
        try:
            InventoryService.retirar_vencidos(producto, cantidad, motivo, request.user, evidencia=evidencia)
            message = "Retiro de vencidos registrado correctamente."
        except Exception as exc:
            message = str(exc)
    else:
        message = None
    productos = Producto.objects.filter(stock_bodega__gt=0, activo=True)
    return render(request, "inventory/retirar_vencidos.html", {"productos": productos, "message": message})


from django.http import JsonResponse
from django.db.models import Q

def api_consultar_existencias(request):
    producto_codigo_o_nombre = request.GET.get("producto", "").strip()
    if not producto_codigo_o_nombre:
        return JsonResponse({
            "status": "error",
            "mensaje": "Debe especificar el parámetro 'producto'."
        }, status=400)

    producto = Producto.objects.filter(
        Q(codigo__iexact=producto_codigo_o_nombre) | Q(nombre__iexact=producto_codigo_o_nombre)
    ).first()

    if not producto:
        return JsonResponse({
            "status": "not_found",
            "mensaje": f"Producto '{producto_codigo_o_nombre}' no encontrado."
        }, status=404)

    return JsonResponse({
        "status": "success",
        "producto": {
            "codigo": producto.codigo,
            "nombre": producto.nombre,
            "stock_bodega": producto.stock_bodega,
            "stock_percha": producto.stock_percha,
            "stock_total": producto.stock_total,
            "stock_minimo": producto.stock_minimo,
        }
    })
