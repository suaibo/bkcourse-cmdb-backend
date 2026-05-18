# -*- coding: utf-8 -*-
from django.db import models


class BizInfo(models.Model):
    """Cached CMDB business metadata."""

    bk_biz_id = models.IntegerField(unique=True)
    bk_biz_name = models.CharField(max_length=50)

    def __str__(self):
        return "{}-{}".format(self.bk_biz_id, self.bk_biz_name)
