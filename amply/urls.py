from django.contrib import admin
from django.urls import include
from django.conf.urls import url
from users import views as user_views

urlpatterns = [
    url(r'admin/', admin.site.urls),
    url(r'register/', user_views.register, name="register"),
    url(r'', include('peck.urls'))
]
