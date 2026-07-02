from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group

class Command(BaseCommand):
    help = "Crea los grupos iniciales del sistema"

    def handle(self, *args, **kwargs):
        grupos = [
            "Administrador",
            "Encargado de Compras",
        ]

        for nombre in grupos:
            Group.objects.get_or_create(name=nombre)

        self.stdout.write(
            self.style.SUCCESS("Roles creados correctamente.")
        )