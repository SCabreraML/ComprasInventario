from django.db import models
from django.contrib.auth import get_user_model
import uuid

Usuario = get_user_model()


class SolicitudCompra(models.Model):

    # Dev 1 - ST-2.1
    # Modelo para registrar solicitudes

    ESTADOS = [
        ('PENDIENTE', 'Pendiente'),
        ('APROBADA', 'Aprobada'),
        ('RECHAZADA', 'Rechazada'),
    ]

    codigo = models.CharField(
        max_length=20,
        unique=True,
        editable=False
    )

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