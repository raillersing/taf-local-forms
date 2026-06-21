from django.urls import path

from .views import (
    dashboard_home,
    dashboard_module_2,
    export_module_2_csv,
    home,
    module_2_form,
    module_2_success,
    network_access_dashboard,
)


app_name = "surveys"

urlpatterns = [
    path("", home, name="home"),
    path("module-2/", module_2_form, name="module_2"),
    path("module-2/success/<int:submission_id>/", module_2_success, name="module_2_success"),
    path("dashboard/", dashboard_home, name="dashboard_home"),
    path("dashboard/module-2/", dashboard_module_2, name="dashboard_module_2"),
    path("dashboard/export/module-2.csv", export_module_2_csv, name="export_module_2_csv"),
    path("dashboard/network/", network_access_dashboard, name="dashboard_network"),
]
