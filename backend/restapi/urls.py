from django.urls import include, path
from rest_framework import routers

from restapi import views

router = routers.DefaultRouter()

router.register(r'users', views.UserViewSet, basename = 'user')

router.register(r'worlds'    , views.WorldViewSet)
router.register(r'movables'  , views.MovableViewSet  , basename = 'movable')
router.register(r'sectors'   , views.SectorViewSet   , basename = 'sector')
router.register(r'celestials', views.CelestialViewSet, basename = 'celestial')
router.register(r'unveiled'  , views.UnveiledViewSet , basename = 'unveiled')

router.register(r'empires'      , views.EmpireViewSet      , basename = 'empire')
router.register(r'empires'      , views.PrivateEmpireViewSet, basename = 'empire')
router.register(r'blueprints'   , views.BlueprintViewSet   , basename = 'blueprint')
router.register(r'constructions', views.ConstructionViewSet, basename = 'construction')
router.register(r'ships'        , views.ShipViewSet        , basename = 'ship')

router.register(r'processes', views.ProcessViewSet, basename = 'process')

urlpatterns = [
    path('', include(router.urls)),
    path('login/', views.LoginView.as_view()),
]

urlpatterns += router.urls
