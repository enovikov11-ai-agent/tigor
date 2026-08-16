# Kata Containers on Box

Status: experimental and not currently deployed in `infra/0-box/configuration.nix`.

## What Was Tried

- Added `pkgs.kata-runtime` to `virtualisation.podman.extraRuntimes`.
- Added a `kata-hello` Compose service using `docker.io/library/nginx:alpine` on host port `8888`.
- First tried `runtime: kata-runtime`.
- After Podman reported the runtime name was missing, tried an explicit `/etc/containers/containers.conf` alias:

```nix
virtualisation.containers.containersConf.settings = lib.mkIf enablePodmanStack {
  engine = {
    runtimes.kata = [ "${pkgs.kata-runtime}/bin/kata-runtime" ];
    runtime_supports_kvm = [ "kata" ];
  };
};
```

with Compose:

```yaml
runtime: kata
```

This still did not work reliably enough to keep in the deployed host config.

## Failure Seen

With `runtime: kata-runtime`, Podman failed immediately:

```text
Error: default OCI runtime "kata-runtime" not found: invalid argument
```

`podman compose up` then produced follow-on cleanup/start errors:

```text
[kata-hello] | Error: no container with name or ID "kata-hello" found: no such container
[p-vllm]     | Error: unable to start container ... failed to connect to container's attach socket ... connection refused
[p-chat]     | Error: unable to start container ... failed to connect to container's attach socket ... connection refused
```

Those attach socket errors looked like fallout from a failed Compose run leaving existing containers half-started, not the root cause.

## Debug Commands

Full logs for the failed service invocation:

```bash
sudo journalctl -u podman-compose.service -b -a --no-pager -o short-precise
```

Filter likely runtime errors:

```bash
sudo journalctl -u podman-compose.service -b -a --no-pager -g 'kata|runtime|error|fail|125|cannot'
```

Check what Podman thinks its runtimes are:

```bash
sudo podman info
```

Direct Kata smoke tests:

```bash
sudo podman run --rm --runtime kata-runtime docker.io/library/busybox:latest uname -a
```

```bash
sudo podman run --rm --runtime kata docker.io/library/busybox:latest uname -a
```

Kata runtime logs:

```bash
sudo journalctl -t kata-runtime -b -a --no-pager
```

Shim-v2 logs, if using the containerd-style Kata path:

```bash
sudo journalctl -t kata -b -a --no-pager
```

## Notes

- `virtualisation.podman.extraRuntimes = [ pkgs.kata-runtime ]` alone does not guarantee `runtime: kata-runtime` is a valid Podman runtime name.
- On some systems the Podman runtime alias is `kata`, not `kata-runtime`.
- Modern Kata is primarily a shim-v2/containerd/Kubernetes path. Current Kata docs list Podman support as limited/unsupported in some paths, so expect rough edges.
- Do not add Kata back to the deployed box AI stack without first proving a standalone smoke test works outside Compose.
- Keep `p-vllm` on the default Podman runtime. Kata is not the first choice for GPU inference on this host.
