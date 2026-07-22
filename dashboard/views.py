from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_POST

from . import adb_client, config_store


def dashboard(request):
    data = config_store.load()
    command_map = {c["id"]: c for c in data["commands"]}
    devices = []
    for device in data["devices"]:
        commands = [command_map[cid] for cid in device["command_ids"] if cid in command_map]
        online = adb_client.check_status(device["ip"], device["port"])
        devices.append({**device, "commands": commands, "online": online})
    return render(request, "dashboard/index.html", {"devices": devices})


@require_POST
def run_command(request, device_id, command_id):
    device = config_store.get_device(device_id)
    command = config_store.get_command(command_id)
    if device is None or command is None:
        return JsonResponse({"ok": False, "error": "Unbekanntes Gerät oder Command"}, status=404)
    result = adb_client.run_command(device["ip"], device["port"], command["cmd"])
    return JsonResponse(result)


def config_view(request):
    return HttpResponse(status=501)
