from django.urls import path

from .views import (
    dashboard_home,
    dashboard_module_2,
    dashboard_module_3,
    export_module_2_csv,
    export_module_3_csv,
    home,
    module_2_form,
    module_2_success,
    module_3_form,
    module_3_success,
    network_access_dashboard,
)


app_name = "surveys"

urlpatterns = [
    path("", home, name="home"),
    path("module-2/", module_2_form, name="module_2"),
    path("module-2/success/<int:submission_id>/", module_2_success, name="module_2_success"),
    path("module-3/", module_3_form, name="module_3"),
    path("module-3/success/<int:submission_id>/", module_3_success, name="module_3_success"),
    path("dashboard/", dashboard_home, name="dashboard_home"),
    path("dashboard/module-2/", dashboard_module_2, name="dashboard_module_2"),
    path("dashboard/module-3/", dashboard_module_3, name="dashboard_module_3"),
    path("dashboard/export/module-2.csv", export_module_2_csv, name="export_module_2_csv"),
    path("dashboard/export/module-3.csv", export_module_3_csv, name="export_module_3_csv"),
    path("dashboard/network/", network_access_dashboard, name="dashboard_network"),
]
