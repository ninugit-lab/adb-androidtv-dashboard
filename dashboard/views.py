from django.http import HttpResponse
from django.shortcuts import render

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


def run_command(request, device_id, command_id):
    return HttpResponse(status=501)


def config_view(request):
    return HttpResponse(status=501)
