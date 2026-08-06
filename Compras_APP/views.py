from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponseForbidden
from .forms import SolicitudCompraForm, CotizacionForm
from .models import SolicitudCompra, Cotizacion
from django.shortcuts import get_object_or_404, redirect

from .models import Cotizacion, OrdenCompra


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


# HU-13: Registrar tiempo de entrega
# HU-14: Asociar proveedor con la cotización
# HU-12: Registrar información económica de la cotización
@login_required
def registrar_cotizacion_view(request, pk):
    """
    Registra una cotización asociada a una solicitud de compra.
    Permite asociar un proveedor (HU-14), registrar la información económica (HU-12),
    y guardar el tiempo estimado de entrega obligatorio (HU-13).
    """
    solicitud = get_object_or_404(SolicitudCompra, pk=pk)

    if request.method == "POST":
        form = CotizacionForm(request.POST)
        if form.is_valid():
            cotizacion = form.save(commit=False)
            cotizacion.solicitud = solicitud  # HU-14: Asociar proveedor con la solicitud de compra
            cotizacion.save()
            registrar_auditoria(
                request.user if request.user.is_authenticated else None,
                "Registrar cotización",
                f"Cotización de {cotizacion.proveedor} registrada para {solicitud.codigo} con tiempo de entrega {cotizacion.tiempo_entrega} días"
            )
            return redirect("lista_cotizaciones", pk=solicitud.id)
    else:
        form = CotizacionForm()

    return render(
        request,
        "solicitudes/registrar_cotizacion.html",
        {
            "form": form,
            "solicitud": solicitud
        }
    )


# HU-11: Consultar cotizaciones registradas
@login_required
def lista_cotizaciones_view(request, pk):
    """
    Muestra todas las cotizaciones registradas de una solicitud de compra (HU-11).
    """
    solicitud = get_object_or_404(SolicitudCompra, pk=pk)
    cotizaciones = solicitud.cotizaciones.order_by("precio_unitario")

    return render(
        request,
        "solicitudes/lista_cotizaciones.html",
        {
            "solicitud": solicitud,
            "cotizaciones": cotizaciones
        }
    )
#sprint 4 HU-16: Seleccionar cotización ganadora
def seleccionar_ganadora_view(request, pk):
    cotizacion = get_object_or_404(Cotizacion, pk=pk)
    solicitud_cotizacion = cotizacion.solicitud_cotizacion
    solicitud_compra = solicitud_cotizacion.solicitud_compra

    # HU-17: la seleccionada queda ACEPTADA, las demás RECHAZADA
    solicitud_cotizacion.cotizaciones.exclude(pk=cotizacion.pk).update(
        estado=Cotizacion.ESTADO_RECHAZADA
    )
    cotizacion.estado = Cotizacion.ESTADO_ACEPTADA
    cotizacion.save()

    # HU-18: genera la orden de compra y calcula el costo total
    costo_total = solicitud_compra.cantidad_solicitada * cotizacion.precio_unitario
    orden = OrdenCompra.objects.create(
        cotizacion_ganadora=cotizacion,
        costo_total=costo_total,
    )

    registrar_auditoria(request.user if request.user.is_authenticated else None,
                         "Generar orden de compra", f"{orden.numero_orden}")

    return redirect("compras_ver_orden", pk=orden.pk)

# HU-15: Visualización de Detalle de Orden de Compra
def ver_orden_view(request, pk):
    orden = get_object_or_404(OrdenCompra, pk=pk)
    return render(request, "compras/ver_orden.html", {"orden": orden})

# HU-22: Exportar orden a PDF
# COMENTARIO DE LOCALIZACIÓN: HU-22 - Esta función genera y descarga la orden de compra como un archivo PDF profesional.
from django.http import HttpResponse
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

@login_required
def exportar_orden_pdf(request, pk):
    orden = get_object_or_404(OrdenCompra, pk=pk)

    # Configurar el response para descargar el PDF
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="orden_compra_{orden.id}.pdf"'

    # Crear el documento PDF usando SimpleDocTemplate de reportlab
    doc = SimpleDocTemplate(response, pagesize=letter, rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40)
    story = []

    # Configuración de estilos
    styles = getSampleStyleSheet()

    # Crear estilos personalizados para evitar conflictos
    style_title = ParagraphStyle(
        'DocTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=20,
        leading=24,
        textColor=colors.HexColor('#0d6efd')
    )

    style_subtitle = ParagraphStyle(
        'DocSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=12,
        leading=16,
        textColor=colors.HexColor('#6c757d')
    )

    style_section_heading = ParagraphStyle(
        'SectionHeading',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=11,
        leading=14,
        textColor=colors.HexColor('#1e293b'),
        spaceAfter=6
    )

    style_body = ParagraphStyle(
        'DocBody',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=13,
        textColor=colors.HexColor('#334155')
    )

    style_body_bold = ParagraphStyle(
        'DocBodyBold',
        parent=style_body,
        fontName='Helvetica-Bold'
    )

    style_table_header = ParagraphStyle(
        'TableHeader',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=9,
        leading=11,
        textColor=colors.white
    )

    # 1. ENCABEZADO
    story.append(Paragraph("SISTEMA DE COMPRAS E INVENTARIO", style_subtitle))
    story.append(Paragraph(f"ORDEN DE COMPRA: OC-{orden.id}", style_title))
    story.append(Spacer(1, 15))

    # 2. INFORMACIÓN METADATA (Fecha y Estado)
    meta_data = [
        [Paragraph(f"<b>Fecha de Emisión:</b> {orden.fecha.strftime('%d/%m/%Y %H:%M')}", style_body),
         Paragraph("<b>Estado de la Orden:</b> Generada / Aprobada", style_body)]
    ]
    meta_table = Table(meta_data, colWidths=[260, 260])
    meta_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f8fafc')),
        ('PADDING', (0, 0), (-1, -1), 10),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 20))

    # 3. INFORMACIÓN DE PROVEEDOR Y SOLICITANTE
    info_data = [
        [
            Paragraph("<b>INFORMACIÓN DEL PROVEEDOR</b>", style_section_heading),
            Paragraph("<b>DETALLES DE LA SOLICITUD</b>", style_section_heading)
        ],
        [
            Paragraph(f"<b>Nombre/Empresa:</b> {orden.cotizacion.proveedor}<br/>"
                      f"<b>Vigencia Cotización:</b> {orden.cotizacion.vigencia.strftime('%d/%m/%Y')}<br/>"
                      f"<b>Tiempo de Entrega:</b> {orden.cotizacion.tiempo_entrega} días", style_body),
            Paragraph(f"<b>Código Solicitud:</b> {orden.cotizacion.solicitud.codigo}<br/>"
                      f"<b>Solicitante:</b> {orden.cotizacion.solicitud.solicitante.username}<br/>"
                      f"<b>Justificación:</b> {orden.cotizacion.solicitud.justificacion or 'Sin justificación'}", style_body)
        ]
    ]
    info_table = Table(info_data, colWidths=[260, 260])
    info_table.setStyle(TableStyle([
        ('PADDING', (0, 0), (-1, -1), 10),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e1')),
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f1f5f9')),
        ('LINEBELOW', (0, 0), (-1, 0), 0.5, colors.HexColor('#cbd5e1')),
    ]))
    story.append(info_table)
    story.append(Spacer(1, 25))

    # 4. TABLA DE DETALLES DE PRODUCTO
    product_headers = [
        Paragraph("Producto / Item", style_table_header),
        Paragraph("Descripción", style_table_header),
        Paragraph("Cantidad", style_table_header),
        Paragraph("Precio Unitario", style_table_header),
        Paragraph("Total", style_table_header)
    ]

    product_rows = [
        product_headers,
        [
            Paragraph(orden.cotizacion.solicitud.producto, style_body_bold),
            Paragraph(orden.cotizacion.solicitud.descripcion or "Sin descripción adicional", style_body),
            Paragraph(str(orden.cotizacion.solicitud.cantidad), style_body),
            Paragraph(f"${orden.cotizacion.precio_unitario}", style_body),
            Paragraph(f"${orden.costo_total}", style_body_bold)
        ]
    ]

    product_table = Table(product_rows, colWidths=[120, 180, 60, 80, 80])
    product_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0d6efd')),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('PADDING', (0, 0), (-1, -1), 10),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e1')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8fafc')]),
    ]))
    story.append(product_table)
    story.append(Spacer(1, 20))

    # 5. RESUMEN DE COSTOS
    totals_data = [
        [Paragraph("", style_body), Paragraph("<b>TOTAL DE LA ORDEN:</b>", style_body_bold), Paragraph(f"<b>${orden.costo_total}</b>", style_body_bold)]
    ]
    totals_table = Table(totals_data, colWidths=[360, 80, 80])
    totals_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('PADDING', (0, 0), (-1, -1), 8),
        ('GRID', (1, 0), (-1, -1), 1, colors.HexColor('#0d6efd')),
        ('BACKGROUND', (1, 0), (-1, -1), colors.HexColor('#eff6ff')),
    ]))
    story.append(totals_table)
    story.append(Spacer(1, 60))

    # 6. SECCIÓN DE FIRMAS
    signatures_data = [
        [
            Paragraph("<font color='#6c757d'>____________________________</font><br/><b>Firma Autorizada</b><br/>Departamento de Compras", style_body),
            Paragraph("<font color='#6c757d'>____________________________</font><br/><b>Firma de Recepción</b><br/>Proveedor / Repre. Legal", style_body)
        ]
    ]
    signatures_table = Table(signatures_data, colWidths=[260, 260])
    signatures_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('PADDING', (0, 0), (-1, -1), 10),
    ]))
    story.append(signatures_table)

    # Construir el PDF
    doc.build(story)
    return response

# HU 20
@login_required
def generar_orden_view(request, pk):

    cotizacion = get_object_or_404(Cotizacion, pk=pk)

    orden, creada = OrdenCompra.objects.get_or_create(
        cotizacion=cotizacion
    )

    return redirect("ver_orden", orden.id)

@login_required
def lista_ordenes(request):

    ordenes = OrdenCompra.objects.select_related(
        "cotizacion",
        "cotizacion__solicitud"
    ).order_by("-fecha")

    return render(
        request,
        "compras/lista_ordenes.html",
        {
            "ordenes": ordenes
        }
    )

from .forms import ProveedorForm
from .models import Proveedor

@login_required
def compras_listado_proveedores(request):
    proveedores = Proveedor.objects.all().order_by("nombre")
    return render(
        request,
        "compras/lista_proveedores.html",
        {
            "proveedores": proveedores
        }
    )

@login_required
def registrar_proveedor(request):
    if request.method == "POST":
        form = ProveedorForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("compras_listado_proveedores")
    else:
        form = ProveedorForm()

    return render(
        request,
        "compras/registrar_proveedor.html",
        {
            "form": form
        }
    )

@login_required
def reporte_ordenes(request):
    from django.db.models import Sum, Count, Avg
    import collections

    stats = OrdenCompra.objects.aggregate(
        total=Count("id"),
        total_gasto=Sum("costo_total"),
        promedio_gasto=Avg("costo_total")
    )

    total_ordenes = stats.get("total") or 0
    costo_total_acumulado = stats.get("total_gasto") or 0
    gasto_promedio = stats.get("promedio_gasto") or 0

    # Agrupar gastos por proveedor
    proveedor_totals = collections.defaultdict(lambda: {"count": 0, "total": 0})
    for orden in OrdenCompra.objects.all():
        prov_name = orden.cotizacion.proveedor
        proveedor_totals[prov_name]["count"] += 1
        proveedor_totals[prov_name]["total"] += orden.costo_total

    proveedores_gasto = [
        {"proveedor": k, "count": v["count"], "total": v["total"]}
        for k, v in proveedor_totals.items()
    ]
    # Ordenar por gasto total descendente
    proveedores_gasto = sorted(proveedores_gasto, key=lambda x: x["total"], reverse=True)

    return render(
        request,
        "compras/reporte_ordenes.html",
        {
            "total_ordenes": total_ordenes,
            "costo_total_acumulado": costo_total_acumulado,
            "gasto_promedio": gasto_promedio,
            "proveedores_gasto": proveedores_gasto
        }
    )