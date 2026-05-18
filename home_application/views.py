# -*- coding: utf-8 -*-
import os

from django.conf import settings
from django.http import JsonResponse
from django.shortcuts import render

from blueapps.account.decorators import login_exempt
from blueking.component.shortcuts import get_client_by_request, get_client_by_user
from home_application.models import BizInfo


api_login_exempt = login_exempt if settings.DEBUG else lambda func: func


def home(request):
    return render(request, "home_application/index_home.html")


def dev_guide(request):
    return render(request, "home_application/dev_guide.html")


def contact(request):
    return render(request, "home_application/contact.html")


def _param_as_int(request, name):
    value = request.GET.get(name)
    if value in (None, ""):
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _missing_param_response(name):
    return JsonResponse({
        "result": False,
        "message": "missing required parameter: {}".format(name),
        "data": {"count": 0, "info": []},
    }, status=400)


def _get_component_client(request):
    bk_token = request.COOKIES.get("bk_token")
    if bk_token:
        return get_client_by_request(request, bk_token=bk_token)
    if settings.DEBUG:
        return get_client_by_user(os.getenv("BK_DEV_USERNAME", "admin"))
    return get_client_by_request(request)


@api_login_exempt
def get_bizs_list(request):
    """Fetch the business list from local cache first, then CMDB."""
    bizs = BizInfo.objects.all().order_by("bk_biz_id")
    if bizs.exists():
        return JsonResponse({
            "result": True,
            "message": "success",
            "data": {
                "count": bizs.count(),
                "info": list(bizs.values("bk_biz_id", "bk_biz_name")),
            },
        })

    client = _get_component_client(request)
    result = client.cc.search_business({
        "fields": ["bk_biz_id", "bk_biz_name"],
        "page": {
            "start": 0,
            "limit": 100,
            "sort": "",
        },
    })

    if result.get("result") and result.get("data"):
        for biz in result["data"].get("info", []):
            BizInfo.objects.update_or_create(
                bk_biz_id=biz["bk_biz_id"],
                defaults={"bk_biz_name": biz["bk_biz_name"]},
            )
    return JsonResponse(result)


@api_login_exempt
def get_sets_list(request):
    """Fetch set list by business id."""
    bk_biz_id = _param_as_int(request, "bk_biz_id")
    if bk_biz_id is None:
        return _missing_param_response("bk_biz_id")

    client = _get_component_client(request)
    result = client.cc.search_set({
        "bk_biz_id": bk_biz_id,
        "fields": [
            "bk_set_id",
            "bk_set_name",
            "bk_biz_id",
            "bk_created_at",
            "bk_supplier_account",
        ],
    })
    return JsonResponse(result)


@api_login_exempt
def get_modules_list(request):
    """Fetch module list by business id and set id."""
    bk_biz_id = _param_as_int(request, "bk_biz_id")
    bk_set_id = _param_as_int(request, "bk_set_id")
    if bk_biz_id is None:
        return _missing_param_response("bk_biz_id")
    if bk_set_id is None:
        return _missing_param_response("bk_set_id")

    client = _get_component_client(request)
    result = client.cc.search_module({
        "bk_biz_id": bk_biz_id,
        "bk_set_id": bk_set_id,
        "fields": [
            "bk_module_id",
            "bk_module_name",
            "bk_set_id",
            "bk_biz_id",
            "bk_created_at",
            "bk_supplier_account",
        ],
    })
    return JsonResponse(result)


@api_login_exempt
def get_hosts_list(request):
    """Fetch host list by business id and optional set/module/operator filters."""
    bk_biz_id = _param_as_int(request, "bk_biz_id")
    if bk_biz_id is None:
        return _missing_param_response("bk_biz_id")

    kwargs = {
        "bk_biz_id": bk_biz_id,
        "page": {
            "start": 0,
            "limit": 100,
        },
        "fields": [
            "bk_host_id",
            "bk_host_innerip",
            "operator",
            "bk_bak_operator",
        ],
    }

    bk_set_id = _param_as_int(request, "bk_set_id")
    if bk_set_id is not None:
        kwargs["bk_set_ids"] = [bk_set_id]

    bk_module_id = _param_as_int(request, "bk_module_id")
    if bk_module_id is not None:
        kwargs["bk_module_ids"] = [bk_module_id]

    operator = request.GET.get("operator")
    if operator:
        kwargs["host_property_filter"] = {
            "condition": "AND",
            "rules": [{
                "field": "operator",
                "operator": "contains",
                "value": operator,
            }],
        }

    client = _get_component_client(request)
    result = client.cc.list_biz_hosts(kwargs)
    return JsonResponse(result)


@api_login_exempt
def get_host_detail(request):
    """Fetch host detail by host id."""
    bk_host_id = _param_as_int(request, "bk_host_id")
    if bk_host_id is None:
        return _missing_param_response("bk_host_id")

    client = _get_component_client(request)
    result = client.cc.get_host_base_info({"bk_host_id": bk_host_id})
    return JsonResponse(result)
