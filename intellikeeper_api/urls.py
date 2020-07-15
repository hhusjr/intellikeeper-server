"""intellikeeper_api URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include
from rest_framework import routers

from device.views import DeviceViewset, change_device_status
from intellikeeper_api import settings
from tag.views import TagViewset, find_tag, change_tag_status, test_callback, \
    TriggerViewset, get_classified_tags, test_trigger, change_trigger_status, \
    CallbackView, get_tags_info, get_track, TagCategoryViewset, checkout_tags, ReaderViewset, get_events, \
    get_events_top10

router = routers.DefaultRouter()
router.register(r'devices', DeviceViewset, basename='device')
router.register(r'tags', TagViewset, basename='tag')
router.register(r'tag-categories', TagCategoryViewset, basename='tag_category')
router.register(r'triggers', TriggerViewset, basename='trigger')
router.register(r'readers', ReaderViewset, basename='reader')

urlpatterns = [
    path('devices/<int:pk>/change-status/', change_device_status),

    path('tags/<int:pk>/find-tag/', find_tag),
    path('tags/<int:pk>/change-status/', change_tag_status),
    path('tags/<int:pk>/test-callback/', test_callback),
    path('tags/track/', get_track),
    path('tags/classified/', get_classified_tags),
    path('tags/info/', get_tags_info),
    path('tags/checkout/', checkout_tags),

    path('triggers/<int:pk>/test-trigger/', test_trigger),
    path('triggers/<int:pk>/change-status/', change_trigger_status),
    path('triggers/used/', CallbackView.as_view()),

    path('events/', get_events),
    path('events/top10/', get_events_top10),

    path('admin/', admin.site.urls),
    path('', include('drfpasswordless.urls')),
    path('', include('rest_framework.urls')),
    path('', include(router.urls))
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
