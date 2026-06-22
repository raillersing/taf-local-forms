from django.urls import path

from .views import (
    dashboard_home,
    dashboard_module_2,
    dashboard_module_3,
    dashboard_module_4,
    dashboard_presence_json,
    dashboard_settings,
    export_module_2_csv,
    export_module_3_csv,
    export_module_4_csv,
    home,
    module_2_form,
    module_2_success,
    module_3_form,
    module_3_success,
    module_4_form,
    module_4_success,
    network_access_dashboard,
    presence_heartbeat,
    toggle_module_responses,
)


app_name = "surveys"

urlpatterns = [
    path("", home, name="home"),
    path("module-2/", module_2_form, name="module_2"),
    path("module-2/success/<int:submission_id>/", module_2_success, name="module_2_success"),
    path("module-3/", module_3_form, name="module_3"),
    path("module-3/success/<int:submission_id>/", module_3_success, name="module_3_success"),
    path("module-4/", module_4_form, name="module_4"),
    path("module-4/success/<int:submission_id>/", module_4_success, name="module_4_success"),
    path("dashboard/", dashboard_home, name="dashboard_home"),
    path("dashboard/module-2/", dashboard_module_2, name="dashboard_module_2"),
    path("dashboard/module-3/", dashboard_module_3, name="dashboard_module_3"),
    path("dashboard/module-4/", dashboard_module_4, name="dashboard_module_4"),
    path("dashboard/export/module-2.csv", export_module_2_csv, name="export_module_2_csv"),
    path("dashboard/export/module-3.csv", export_module_3_csv, name="export_module_3_csv"),
    path("dashboard/export/module-4.csv", export_module_4_csv, name="export_module_4_csv"),
    path("dashboard/network/", network_access_dashboard, name="dashboard_network"),
    path("dashboard/settings/", dashboard_settings, name="dashboard_settings"),
    path("dashboard/presence.json", dashboard_presence_json, name="dashboard_presence_json"),
    path("dashboard/modules/<str:module_code>/toggle-responses/", toggle_module_responses, name="toggle_module_responses"),
    path("presence/heartbeat/", presence_heartbeat, name="presence_heartbeat"),
]
