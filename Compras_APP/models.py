from django.db import models
from django.contrib.auth import get_user_model
import uuid

Usuario = get_user_model()


class SolicitudCompra(models.Model):

    ESTADO_PENDIENTE = "PENDIENTE"
    ESTADO_APROBADA = "APROBADA"
    ESTADO_RECHAZADA = "RECHAZADA"

    # Dev 1 - ST-2.1
    # Modelo para registrar solicitudes

    ESTADOS = [
        (ESTADO_PENDIENTE, 'Pendiente'),
        (ESTADO_APROBADA, 'Aprobada'),
        (ESTADO_RECHAZADA, 'Rechazada'),
    ]

    codigo = models.CharField(
        max_length=20,
        unique=True,
        editable=False
    )

    justificacion = models.TextField(blank=True, default="")

    producto = models.CharField(max_length=150)

    descripcion = models.TextField(blank=True)

    cantidad = models.PositiveIntegerField()

    solicitante = models.ForeignKey(
        Usuario,
        on_delete=models.CASCADE
    )

    fecha_registro = models.DateTimeField(
        auto_now_add=True
    )

    estado = models.CharField(
        max_length=15,
        choices=ESTADOS,
        default="PENDIENTE"
    )

    # Dev 1 - ST-2.2
    # Generación automática del código
    def save(self, *args, **kwargs):

        if not self.codigo:
            self.codigo = "SOL-" + uuid.uuid4().hex[:8].upper()

        super().save(*args, **kwargs)

    def __str__(self):
        return self.codigo


class Cotizacion(models.Model):
    
    # HU-14: Asociar proveedor con la cotización
    # Relacionar proveedor y solicitud (SolicitudCompra).
    solicitud = models.ForeignKey(
        SolicitudCompra,
        on_delete=models.CASCADE,
        related_name="cotizaciones"
    )

    # HU-14: Asociar proveedor con la cotización (Proveedor como dato registrado)
    proveedor = models.CharField(
        max_length=150,
        blank=False,
        null=False
    )

    # HU-12: Registrar información económica de la cotización
    precio_unitario = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        blank=False,
        null=False
    )

    vigencia = models.DateField(
        blank=False,
        null=False
    )

    # HU-13: Registrar tiempo de entrega
    # Guardar el tiempo estimado de entrega (en días). El dato es obligatorio.
    tiempo_entrega = models.PositiveIntegerField(
        blank=False,
        null=False
    )

    fecha_registro = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return f"Cotización de {self.proveedor} para {self.solicitud.codigo}"

class OrdenCompra(models.Model):

    cotizacion = models.OneToOneField(
        Cotizacion,
        on_delete=models.CASCADE
    )

    fecha = models.DateTimeField(auto_now_add=True)

    costo_total = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        editable=False
    )

    def save(self, *args, **kwargs):
        self.costo_total = (
            self.cotizacion.solicitud.cantidad *
            self.cotizacion.precio_unitario
        )
        super().save(*args, **kwargs)

    def __str__(self):
        return f"OC-{self.id}"