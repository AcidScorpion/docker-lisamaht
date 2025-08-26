
# Add traffic <https://www.telia.ee/lismaht>

Make image:

```text
podman build --format docker -t lisamaht:latest .
```

Or, with version:

```text
podman build --format docker -t lisamaht:1.0.0 -t lisamaht:latest
```

SELinux:

```text
# semanage fcontext -a -t container_file_t '/opt/lisamaht/lisamaht\.(json|py)?'

# restorecon -rv /opt/lisamaht/
```

Run container without entrypoint:

```text
podman run -it --rm -v "$(pwd)/lisamaht.py:/opt/lisamaht.py" -v "$(pwd)/lisamaht.json:/opt/lisamaht.json" -v "/var/log/lisamaht.log:/opt/lisamaht.log" --name lisamaht lisamaht:latest
```

With entrypoint:

```text
podman run -it --rm -v "$(pwd)/lisamaht.py:/opt/lisamaht.py" -v "$(pwd)/lisamaht.json:/opt/lisamaht.json" -v "/var/log/lisamaht.log:/opt/lisamaht.log" --entrypoint='["/opt/.venv/bin/python3", "/opt/lisamaht.py"]' --name lisamaht01 lisamaht:latest
```
