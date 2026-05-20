# -*- coding: utf-8 -*-
"""Database configuration helpers for local and PaaS environments."""

from __future__ import absolute_import

import os


def _get_value(settings, key):
    value = os.environ.get(key)
    if value not in (None, ""):
        return value
    value = settings.get(key)
    if value not in (None, ""):
        return value
    return None


def _normalise_prefix(prefix):
    if prefix == "MYSQL_NAME":
        return "MYSQL"
    return prefix


def prepare_database_environment():
    """Expose PaaS MySQL vars through names the BlueKing SDK reads."""
    if os.environ.get("DB_PREFIX") == "MYSQL_NAME":
        os.environ["DB_PREFIX"] = "MYSQL"

    for source_prefix in ("BKAPP_MYSQL", "BKPAAS_MYSQL"):
        if not os.environ.get("%s_NAME" % source_prefix):
            continue

        for key in ("NAME", "USER", "PASSWORD", "HOST", "PORT"):
            source_key = "%s_%s" % (source_prefix, key)
            target_key = "MYSQL_%s" % key
            if os.environ.get(source_key) and not os.environ.get(target_key):
                os.environ[target_key] = os.environ[source_key]


def _database_from_prefix(settings, prefix):
    prefix = _normalise_prefix(prefix)
    name = _get_value(settings, "%s_NAME" % prefix)
    user = _get_value(settings, "%s_USER" % prefix)
    password = _get_value(settings, "%s_PASSWORD" % prefix)
    host = _get_value(settings, "%s_HOST" % prefix)
    port = _get_value(settings, "%s_PORT" % prefix) or "3306"

    if not all([name, user, password, host]):
        return None

    return {
        "ENGINE": "django.db.backends.mysql",
        "NAME": name,
        "USER": user,
        "PASSWORD": password,
        "HOST": host,
        "PORT": str(port),
        "OPTIONS": {"isolation_level": "repeatable read"},
    }


def get_database_config(settings=None, default=None):
    """Build Django DATABASES from local settings or supported env vars."""
    prepare_database_environment()

    settings = settings or {}
    prefixes = []
    db_prefix = _get_value(settings, "DB_PREFIX")
    if db_prefix:
        prefixes.append(db_prefix)

    prefixes.extend(["BKAPP_MYSQL", "BKPAAS_MYSQL", "GCS_MYSQL", "MYSQL"])

    seen = set()
    for prefix in prefixes:
        prefix = _normalise_prefix(prefix)
        if prefix in seen:
            continue
        seen.add(prefix)

        database = _database_from_prefix(settings, prefix)
        if database:
            return {"default": database}

    return default or {}
