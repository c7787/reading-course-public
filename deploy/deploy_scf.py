#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
腾讯云 SCF 一键部署脚本（控制台「云函数 SCF」）。
前置：
    pip install tencentcloud-sdk-python-scf tencentcloud-sdk-python-apigateway
    export TENCENT_SECRET_ID=xxx
    export TENCENT_SECRET_KEY=xxx
    export VISION_API_KEY=你的智谱key
可选：
    REGION（默认 ap-guangzhou）、FUNCTION_NAME（默认 reading-course）、
    MEMORY_SIZE（256）、TIMEOUT（30）、SCF_NAMESPACE（default）

做了什么：
    1. 调 deploy/build_scf_zip.py 重建部署包
    2. 创建 / 更新 SCF 函数（Python3.10，Handler=webapp.scf_main.main_handler）
    3. 新建 API 网关服务 + API（ANY / -> SCF）+ 发布到 release
    4. 创建 API 网关触发器，拿到公网地址
"""
import os
import sys
import json
import base64
import subprocess

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def step(msg):
    print(f"\n==> {msg}")


def build_zip():
    step("构建部署包 zip")
    subprocess.run([sys.executable, "deploy/build_scf_zip.py"],
                   cwd=ROOT, check=True)
    zip_path = os.path.join(ROOT, "reading-course-scf.zip")
    with open(zip_path, "rb") as f:
        return base64.b64encode(f.read()).decode("ascii")


def get_clients():
    from tencentcloud.common import credential
    from tencentcloud.common.profile.client_profile import ClientProfile
    from tencentcloud.common.profile.http_profile import HttpProfile
    from tencentcloud.scf.v20180416 import scf_client
    from tencentcloud.apigateway.v20180808 import apigateway_client

    sid = os.environ.get("TENCENT_SECRET_ID")
    skey = os.environ.get("TENCENT_SECRET_KEY")
    if not sid or not skey:
        sys.exit("✗ 缺少环境变量 TENCENT_SECRET_ID / TENCENT_SECRET_KEY")
    region = os.environ.get("REGION", "ap-guangzhou")
    cred = credential.Credential(sid, skey)
    hp = HttpProfile()
    cp = ClientProfile()
    cp.httpProfile = hp
    scf = scf_client.ScfClient(cred, region, cp)
    apigw = apigateway_client.ApigatewayClient(cred, region, cp)
    return scf, apigw


def deploy_function(scf, zip_b64):
    from tencentcloud.scf.v20180416 import models as scf_models
    fn = os.environ.get("FUNCTION_NAME", "reading-course")
    ns = os.environ.get("SCF_NAMESPACE", "default")
    vision = os.environ.get("VISION_API_KEY", "")
    mem = int(os.environ.get("MEMORY_SIZE", "256"))
    tout = int(os.environ.get("TIMEOUT", "30"))

    env_json = json.dumps({"Variables": [{"Key": "VISION_API_KEY", "Value": vision}]})
    try:
        step(f"创建函数 {fn}")
        req = scf_models.CreateFunctionRequest()
        req.FunctionName = fn
        req.Runtime = "Python3.10"
        req.Handler = "webapp.scf_main.main_handler"
        req.Code = {"ZipFile": zip_b64}
        req.Environment = env_json
        req.MemorySize = mem
        req.Timeout = tout
        req.Namespace = ns
        scf.CreateFunction(req)
        print(f"  ✓ 函数 {fn} 已创建")
    except Exception as e:
        msg = str(e)
        if "Function already exists" in msg or "ResourceInUse" in msg or "已存在" in msg:
            step(f"函数 {fn} 已存在，改为更新代码 + 配置")
            u = scf_models.UpdateFunctionCodeRequest()
            u.FunctionName = fn
            u.Namespace = ns
            u.Code = {"ZipFile": zip_b64}
            scf.UpdateFunctionCode(u)
            c = scf_models.UpdateFunctionConfigurationRequest()
            c.FunctionName = fn
            c.Namespace = ns
            c.Environment = env_json
            c.MemorySize = mem
            c.Timeout = tout
            scf.UpdateFunctionConfiguration(c)
            print(f"  ✓ 函数 {fn} 代码与配置已更新")
        else:
            raise
    return fn, ns


def deploy_apigw(apigw, fn, ns):
    from tencentcloud.apigateway.v20180808 import models as apigw_models
    service_name = os.environ.get("APIGW_SERVICE", "reading-course-svc")
    step("创建 API 网关服务")
    svc = apigw_models.CreateServiceRequest()
    svc.ServiceName = service_name
    svc.ProtocolType = "http"
    svc.ServiceDesc = "reading-course public api"
    sresp = apigw.CreateService(svc)
    service_id = sresp.ServiceId
    print(f"  ✓ 服务 {service_id}")

    step("创建 API（ANY / -> SCF {fn}）")
    api = apigw_models.CreateApiRequest()
    api.ServiceId = service_id
    api.ApiName = "reading-course-api"
    api.Path = "/"
    api.Method = ["GET", "POST", "PUT", "DELETE", "HEAD", "OPTIONS"]
    api.Protocol = "HTTP"
    api.ServiceType = "SCF"
    api.ServiceScfFunctionName = fn
    api.ServiceScfFunctionNamespace = ns
    api.ServiceScfFunctionQualifier = "$LATEST"
    api.RequestConfig = {"Path": "/", "Method": "ANY"}
    aresp = apigw.CreateApi(api)
    api_id = aresp.ApiId
    print(f"  ✓ API {api_id}")

    step("发布到 release 环境")
    rel = apigw_models.ReleaseServiceRequest()
    rel.ServiceId = service_id
    rel.EnvironmentName = "release"
    rel.ReleaseDesc = "init"
    apigw.ReleaseService(rel)
    print(f"  ✓ 已发布")
    return service_id


def create_trigger(scf, fn, ns, service_id):
    from tencentcloud.scf.v20180416 import models as scf_models
    step("创建 API 网关触发器")
    trig = scf_models.CreateTriggerRequest()
    trig.FunctionName = fn
    trig.Namespace = ns
    trig.Type = "apigw"
    trig.TriggerName = "reading-course-apigw"
    trig.TriggerDesc = json.dumps({"serviceId": service_id, "path": "/", "method": "ANY"})
    trig.Enable = "OPEN"
    scf.CreateTrigger(trig)
    print(f"  ✓ 触发器已创建")


def main():
    vision = os.environ.get("VISION_API_KEY")
    if not vision:
        sys.exit("✗ 缺少环境变量 VISION_API_KEY（智谱 key）")
    zip_b64 = build_zip()
    scf, apigw = get_clients()
    fn, ns = deploy_function(scf, zip_b64)
    service_id = deploy_apigw(apigw, fn, ns)
    create_trigger(scf, fn, ns, service_id)
    print("\n✅ 部署完成")
    print("   函数：", fn)
    print("   公网地址形如：https://<service-id>.apigw.tencentcs.com/release/")
    print("   验证：curl https://<service-id>.apigw.tencentcs.com/release/health  （应返回 has_api_key:true）")


if __name__ == "__main__":
    main()
