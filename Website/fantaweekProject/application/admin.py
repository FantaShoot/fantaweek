from django.contrib import admin

# Register your models here.
from .models import Agenzia, Giocatore, Torneo, Calciatore, Squadra, Iscrizione

admin.site.register(Agenzia)
admin.site.register(Giocatore)
admin.site.register(Torneo)
admin.site.register(Calciatore)
admin.site.register(Squadra)
admin.site.register(Iscrizione)


