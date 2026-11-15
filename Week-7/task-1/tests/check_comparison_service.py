"""Real CPU Python / Cog / website checks; no retraining or service stops."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
from check_baseline_service import command, request, upload, same_scores

ROOT = Path(__file__).resolve().parents[1]


def main():
    week6 = command("docker", "ps", "--filter", "name=ee471-week6", "--format", "{{.ID}} {{.Names}}")
    names = {"baseline": 5072, "optimized": 5073}
    local, direct, logs = {}, {}, {}
    for name in names:
        local[name] = json.loads(command("docker", "run", "--rm", "--network", "none", "--entrypoint", "python",
            "--mount", f"type=bind,source={ROOT},target=/work", "--workdir", "/work",
            "ee471-week6-classifier:latest", "-B", "tests/local_prediction.py", "--model", name))
        sources = {file: hashlib.sha256((ROOT / file).read_bytes()).hexdigest()
                   for file in ("cog_runner.py", "model.py", "preprocessing.py")}
        script = f'''
from pathlib import Path
from unittest.mock import patch
import hashlib, cog_runner
assert cog_runner.MODEL_NAME == {name!r}
assert hashlib.sha256(cog_runner.CHECKPOINT.read_bytes()).hexdigest() == {local[name]["checkpoint_sha256"]!r}
assert list(Path('/src').rglob('*.pth')) == [Path('/src/checkpoint.pth')]
for file, expected in {sources!r}.items():
    assert hashlib.sha256(Path('/src',file).read_bytes()).hexdigest() == expected
for file in ['data','train.py','optimize.py','evaluate.py','results','website','demo_samples','.venv','.env']:
    assert not Path('/src',file).exists(),file
r=cog_runner.Runner();r.setup()
assert not r.model.training and next(r.model.parameters()).device.type=='cpu'
with patch.object(cog_runner,'CHECKPOINT',Path('/missing.pth')):
    try:r.setup()
    except RuntimeError as error:assert 'README' in str(error)
    else:raise AssertionError('missing checkpoint accepted')
with patch.dict(cog_runner.CONFIG,sha256='invalid'):
    try:r.setup()
    except RuntimeError as error:assert 'SHA256' in str(error)
    else:raise AssertionError('invalid hash accepted')
print('OFFLINE_IMAGE_OK: one correct checkpoint; identical sources; CPU eval; missing/hash errors')
'''
        print(command("docker", "run", "--rm", "--network", "none", "--entrypoint", "python",
                      f"ee471-week7-fashion-{name}", "-B", "-c", script))
    image = ROOT / "demo_samples" / local["baseline"]["image"]
    assert local["baseline"]["image"] == local["optimized"]["image"]
    print(command(sys.executable, "postman/make_request.py", str(image)))
    body = (ROOT / "outputs/postman-request.json").read_bytes()
    env = json.loads((ROOT / "outputs/postman-environment.json").read_text())
    assert json.loads(env["values"][0]["value"]) == json.loads(body)
    for name, port in names.items():
        code, reply = request(port, "/predictions", body)
        assert code == 200 and reply["status"] == "succeeded", reply
        direct[name] = reply["output"]
        same_scores(local[name]["output"], direct[name])
        logs[name] = command("docker", "compose", "--env-file", "/dev/null", "exec", "-T", name,
                             "cat", f"/var/log/ee471/fashion-{name}.log")
    code, website = upload(image.read_bytes())
    assert code == 200 and website["status"] == "succeeded", website
    for name in names:
        same_scores(local[name]["output"], website["results"][name]["output"])
        after = command("docker", "compose", "--env-file", "/dev/null", "exec", "-T", name,
                        "cat", f"/var/log/ee471/fashion-{name}.log")
        assert after.count("Prediction completed") == logs[name].count("Prediction completed") + 1
        assert f"model={name}" in after and "base64" not in after and "data:image" not in after
        print("LOG_EVIDENCE", name, after.splitlines()[-1])
    for data in (b"", b"broken PNG"):
        code, reply = upload(data)
        assert code == 400 and reply.get("error")
    code, reply = request(5071, "/api/classify", b"", "multipart/form-data; boundary=empty")
    assert code == 400 and reply.get("error")
    code, reply = upload(image.read_bytes())
    assert code == 200 and reply["status"] == "succeeded"
    assert command("docker", "ps", "--filter", "name=ee471-week6", "--format", "{{.ID}} {{.Names}}") == week6
    report = {"image": image.name, "image_sha256": hashlib.sha256(image.read_bytes()).hexdigest(),
              "python": local, "cog": direct, "website": website["results"], "scores_match": True,
              "absolute_tolerance": 1e-7, "image_hashes_verified": True, "offline_cpu_setup": True,
              "logs_verified": list(names), "invalid_upload_recovery": True, "week6_unchanged": True,
              "retraining": False, "real_postman_desktop": False}
    (ROOT / "outputs/stage4-comparison.json").write_text(json.dumps(report, indent=2) + "\n")
    print("REAL_COMPARISON", json.dumps(report))


if __name__ == "__main__":
    main()
