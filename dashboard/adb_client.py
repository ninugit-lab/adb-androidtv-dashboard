from ppadb.client import Client as AdbClient

_client = None


def get_client():
    global _client
    if _client is None:
        _client = AdbClient(host="127.0.0.1", port=5037)
    return _client


def connect_device(ip, port):
    client = get_client()
    try:
        connected = client.remote_connect(ip, port)
        if not connected:
            return None
        return client.device(f"{ip}:{port}")
    except Exception:
        return None


def check_status(ip, port):
    return connect_device(ip, port) is not None


def run_command(ip, port, cmd):
    try:
        device = connect_device(ip, port)
        if device is None:
            return {"ok": False, "output": None, "error": "Gerät nicht erreichbar"}
        output = device.shell(cmd)
        return {"ok": True, "output": output, "error": None}
    except Exception as exc:
        return {"ok": False, "output": None, "error": str(exc)}
