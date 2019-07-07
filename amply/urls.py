from django.contrib import admin
from django.conf.urls import url, include
from users import views as user_views


urlpatterns = [
    url(r'^admin/', admin.site.urls),
    url(r'^register/', user_views.register, name="register"),
    url(r'', include('peck.urls')),

]
