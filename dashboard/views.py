from django.http import HttpResponse


def dashboard(request):
    return HttpResponse(status=501)


def run_command(request, device_id, command_id):
    return HttpResponse(status=501)


def config_view(request):
    return HttpResponse(status=501)
